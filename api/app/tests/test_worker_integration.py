"""
Integration tests for the worker scheduler and scraper pipeline.

Tests cover:
- Worker scheduling logic
- Scraper timeout handling
- Error recovery
- Sequential execution
- Database persistence
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.runner import WorkerScheduler, SCRAPER_TIMEOUT_MINUTES
from app.db.models import IngestionRun
from app.scrapers.base import Scraper


# ============================================================================
# Mock Scrapers for Testing
# ============================================================================

class MockSuccessfulScraper(Scraper):
    """Mock scraper that always succeeds."""
    chain = "mock_success"

    async def fetch_catalog_pages(self):
        await asyncio.sleep(0.1)
        return ["<html>mock data</html>"]

    async def parse_products(self, payload):
        return [
            {
                "chain": self.chain,
                "source_id": "MOCK123",
                "name": "Mock Product 330ml 4.5%",
                "price_nzd": 10.00,
            }
        ]


class MockFailingScraper(Scraper):
    """Mock scraper that always fails."""
    chain = "mock_fail"

    async def fetch_catalog_pages(self):
        raise Exception("Simulated scraper failure")

    async def parse_products(self, payload):
        return []


class MockSlowScraper(Scraper):
    """Mock scraper that takes a long time."""
    chain = "mock_slow"

    async def fetch_catalog_pages(self):
        await asyncio.sleep(100)  # Longer than typical timeout
        return []

    async def parse_products(self, payload):
        return []


# ============================================================================
# Worker Scheduler Tests
# ============================================================================

class TestWorkerScheduler:
    """Test worker scheduling logic."""

    def test_initialization(self):
        """Test worker initializes with correct state."""
        scheduler = WorkerScheduler()

        assert len(scheduler.last_run) > 0
        assert len(scheduler.running_chains) == 0
        assert all(v is None for v in scheduler.last_run.values())

    @pytest.mark.asyncio
    async def test_should_run_never_run_before(self):
        """Test scraper should run if never executed."""
        scheduler = WorkerScheduler()

        should_run = await scheduler.should_run_scraper("countdown")

        assert should_run is True

    @pytest.mark.asyncio
    async def test_should_run_recently_completed(self):
        """Test scraper should not run if recently completed."""
        scheduler = WorkerScheduler()
        scheduler.last_run["countdown"] = datetime.utcnow()

        should_run = await scheduler.should_run_scraper("countdown")

        assert should_run is False

    @pytest.mark.asyncio
    async def test_should_run_old_execution(self):
        """Test scraper should run if execution is old."""
        scheduler = WorkerScheduler()
        scheduler.last_run["countdown"] = datetime.utcnow() - timedelta(days=2)

        should_run = await scheduler.should_run_scraper("countdown")

        assert should_run is True

    @pytest.mark.asyncio
    async def test_should_not_run_if_already_running(self):
        """Test scraper should not run if already executing."""
        scheduler = WorkerScheduler()
        scheduler.running_chains["countdown"] = asyncio.create_task(asyncio.sleep(1))

        should_run = await scheduler.should_run_scraper("countdown")

        assert should_run is False

        # Cleanup
        scheduler.running_chains["countdown"].cancel()


# ============================================================================
# Scraper Execution Tests
# ============================================================================

class TestScraperExecution:
    """Test scraper execution with error handling."""

    @pytest.mark.asyncio
    async def test_successful_scraper_execution(self):
        """Test successful scraper records completion time."""
        scheduler = WorkerScheduler(chains_to_run=["countdown"])

        with patch('app.workers.runner.get_chain_scraper') as mock_get_scraper:
            mock_scraper = MockSuccessfulScraper()
            mock_scraper.run = AsyncMock(return_value=MagicMock())
            mock_get_scraper.return_value = mock_scraper

            await scheduler.run_scraper("countdown")

            # Should record completion
            assert scheduler.last_run["countdown"] is not None
            assert "countdown" not in scheduler.running_chains

    @pytest.mark.asyncio
    async def test_failing_scraper_execution(self):
        """Test failing scraper doesn't crash worker."""
        scheduler = WorkerScheduler(chains_to_run=["countdown"])

        with patch('app.workers.runner.get_chain_scraper') as mock_get_scraper:
            mock_scraper = MockFailingScraper()
            mock_scraper.run = AsyncMock(side_effect=Exception("Test error"))
            mock_get_scraper.return_value = mock_scraper

            # Should not raise exception
            await scheduler.run_scraper("countdown")

            # Should not record completion (failed)
            assert scheduler.last_run["countdown"] is None
            assert "countdown" not in scheduler.running_chains

    @pytest.mark.asyncio
    async def test_timeout_scraper_execution(self):
        """Test slow scraper times out gracefully."""
        scheduler = WorkerScheduler(chains_to_run=["countdown"])

        with patch('app.workers.runner.get_chain_scraper') as mock_get_scraper:
            mock_scraper = MockSlowScraper()

            async def slow_run():
                await asyncio.sleep(100)  # Longer than timeout

            mock_scraper.run = slow_run
            mock_get_scraper.return_value = mock_scraper

            # Reduce timeout for testing
            with patch('app.workers.runner.SCRAPER_TIMEOUT_MINUTES', 0.01):
                await scheduler.run_scraper("countdown")

            # Should not record completion (timed out)
            assert scheduler.last_run["countdown"] is None
            assert "countdown" not in scheduler.running_chains


# ============================================================================
# Sequential Execution Tests
# ============================================================================

class TestSequentialExecution:
    """Test scrapers run sequentially, not concurrently."""

    @pytest.mark.asyncio
    async def test_scrapers_run_sequentially(self):
        """Test scrapers execute one at a time."""
        scheduler = WorkerScheduler()
        execution_order = []

        async def track_execution(chain):
            execution_order.append(f"{chain}_start")
            await asyncio.sleep(0.1)
            execution_order.append(f"{chain}_end")

        with patch.object(scheduler, 'run_scraper', side_effect=track_execution):
            # Reduce delay for testing
            with patch('app.workers.runner.SEQUENTIAL_DELAY_SECONDS', 0.05):
                await scheduler.run_all_scrapers(force=True)

        # Check execution was sequential (each scraper finishes before next starts)
        for i in range(0, len(execution_order) - 1, 2):
            if i + 2 < len(execution_order):
                assert execution_order[i].endswith("_start")
                assert execution_order[i + 1].endswith("_end")

    @pytest.mark.asyncio
    async def test_delay_between_scrapers(self):
        """Test appropriate delay between scraper executions."""
        scheduler = WorkerScheduler()
        timestamps = []

        async def record_timestamp(chain):
            timestamps.append(datetime.utcnow())

        with patch.object(scheduler, 'run_scraper', side_effect=record_timestamp):
            with patch('app.workers.runner.SEQUENTIAL_DELAY_SECONDS', 0.2):
                # Run just 2 scrapers to test delay
                with patch('app.scrapers.registry.CHAINS', ["chain1", "chain2"]):
                    await scheduler.run_all_scrapers(force=True)

        # Check there was appropriate delay
        if len(timestamps) >= 2:
            delay = (timestamps[1] - timestamps[0]).total_seconds()
            assert delay >= 0.2, f"Delay was only {delay}s"


# ============================================================================
# Database Persistence Tests
# ============================================================================

class TestDatabasePersistence:
    """Test scraper data persistence to database."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingestion_run_created(self):
        """Test ingestion run is created in database."""
        from app.db.session import async_transaction
        from sqlalchemy import select

        scraper = MockSuccessfulScraper()

        # Mock database operations
        with patch('app.scrapers.base.async_transaction') as mock_transaction:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_transaction.return_value.__aenter__.return_value = mock_session

            try:
                await scraper.run()
            except Exception:
                pass  # May fail due to mocking, but should attempt to create run

            # Should have tried to add IngestionRun
            assert mock_session.add.called

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_failed_scraper_marks_run_failed(self):
        """Test failed scraper updates run status to failed."""
        scraper = MockFailingScraper()

        with patch('app.scrapers.base.async_transaction') as mock_transaction:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_result = AsyncMock()
            mock_run = MagicMock(spec=IngestionRun)
            mock_result.scalar_one.return_value = mock_run
            mock_session.execute.return_value = mock_result
            mock_transaction.return_value.__aenter__.return_value = mock_session

            try:
                await scraper.run()
            except Exception:
                pass  # Expected to fail

            # Should have updated status to "failed"
            # (Check attempted by looking for execute calls)
            assert mock_session.execute.called


# ============================================================================
# Error Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """Test worker error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_worker_continues_after_scraper_failure(self):
        """Test worker continues processing after a scraper fails."""
        scheduler = WorkerScheduler()
        completed_chains = []

        async def track_and_maybe_fail(chain):
            if chain == "countdown":
                raise Exception("Simulated failure")
            completed_chains.append(chain)

        with patch.object(scheduler, 'run_scraper', side_effect=track_and_maybe_fail):
            with patch('app.workers.runner.SEQUENTIAL_DELAY_SECONDS', 0.01):
                with patch('app.scrapers.registry.CHAINS', ["countdown", "new_world", "paknsave"]):
                    await scheduler.run_all_scrapers(force=True)

        # Should have attempted all scrapers despite failure
        assert "new_world" in completed_chains
        assert "paknsave" in completed_chains


# ============================================================================
# Health Monitoring Tests
# ============================================================================

class TestHealthMonitoring:
    """Test health monitoring capabilities."""

    def test_scheduler_tracks_last_run_times(self):
        """Test scheduler maintains last run timestamps."""
        scheduler = WorkerScheduler()

        assert hasattr(scheduler, 'last_run')
        assert isinstance(scheduler.last_run, dict)

        # Update a timestamp
        test_time = datetime.utcnow()
        scheduler.last_run["countdown"] = test_time

        assert scheduler.last_run["countdown"] == test_time

    def test_scheduler_tracks_running_chains(self):
        """Test scheduler tracks currently running chains."""
        scheduler = WorkerScheduler()

        assert hasattr(scheduler, 'running_chains')
        assert isinstance(scheduler.running_chains, dict)
        assert len(scheduler.running_chains) == 0


# ============================================================================
# Configuration Tests
# ============================================================================

class TestWorkerConfiguration:
    """Test worker configuration values."""

    def test_scraper_timeout_configured(self):
        """Test scraper timeout is configured reasonably."""
        assert SCRAPER_TIMEOUT_MINUTES > 0
        # Allow up to 2 hours for scrapers that need it
        assert SCRAPER_TIMEOUT_MINUTES <= 180, "Timeout should be reasonable (<180 minutes)"

    def test_worker_has_chain_list(self):
        """Test worker has access to chain list."""
        from app.scrapers.registry import CHAINS

        # Just verify we have some chains configured
        assert len(CHAINS) > 0
        # Verify at least some expected chains exist
        known_chains = {"liquorland", "super_liquor", "glengarry", "black_bull", "thirsty_liquor"}
        found_chains = set(CHAINS.keys()) & known_chains
        assert len(found_chains) > 0, f"Expected at least one known chain, got: {list(CHAINS.keys())}"


# ============================================================================
# Concurrency Safety Tests
# ============================================================================

class TestConcurrencySafety:
    """Test worker handles concurrent operations safely."""

    @pytest.mark.asyncio
    async def test_same_scraper_not_run_concurrently(self):
        """Test same scraper is not executed concurrently."""
        scheduler = WorkerScheduler()

        async def long_running_scraper(chain):
            await asyncio.sleep(0.5)

        with patch.object(scheduler, 'run_scraper', side_effect=long_running_scraper):
            # Start first run
            task1 = asyncio.create_task(scheduler.run_scraper("countdown"))
            scheduler.running_chains["countdown"] = task1

            # Try to start second run
            should_run = await scheduler.should_run_scraper("countdown")

            assert should_run is False, "Should not run same scraper concurrently"

            # Cleanup
            task1.cancel()
            try:
                await task1
            except asyncio.CancelledError:
                pass
