"""
Integration tests for the worker executor and scraper pipeline.

Tests cover:
- Scraper timeout handling
- Database persistence
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.db.models import IngestionRun
from app.scrapers.base import Scraper
from app.workers.runner import SCRAPER_TIMEOUT_MINUTES, ScraperExecutor

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
# Worker Executor Tests
# ============================================================================


class TestScraperExecutor:
    """Test worker executor state."""

    def test_initialization(self):
        """Test worker initializes with correct state."""
        executor = ScraperExecutor()

        assert executor.chains_to_run
        assert set(executor.consecutive_failures) == set(executor.chains_to_run)


# ============================================================================
# Scraper Execution Tests
# ============================================================================


class TestScraperExecution:
    """Test scraper execution with error handling."""

    @pytest.mark.asyncio
    async def test_successful_scraper_execution(self):
        """Test successful scraper records completion time."""
        executor = ScraperExecutor(chains_to_run=["countdown"])

        with patch("app.workers.runner.get_chain_scraper") as mock_get_scraper:
            mock_scraper = MockSuccessfulScraper()
            mock_scraper.run = AsyncMock(return_value=MagicMock())
            mock_get_scraper.return_value = mock_scraper

            succeeded = await executor.run_scraper("countdown")

            assert succeeded is True
            assert executor.consecutive_failures["countdown"] == 0

    @pytest.mark.asyncio
    async def test_failing_scraper_execution(self):
        """Test failing scraper doesn't crash worker."""
        executor = ScraperExecutor(chains_to_run=["countdown"])

        with patch("app.workers.runner.get_chain_scraper") as mock_get_scraper:
            mock_scraper = MockFailingScraper()
            mock_scraper.run = AsyncMock(side_effect=Exception("Test error"))
            mock_get_scraper.return_value = mock_scraper

            # Should not raise exception
            succeeded = await executor.run_scraper("countdown")

            assert succeeded is False
            assert executor.consecutive_failures["countdown"] == 1

    @pytest.mark.asyncio
    async def test_timeout_scraper_execution(self):
        """Test slow scraper times out gracefully."""
        executor = ScraperExecutor(chains_to_run=["countdown"])

        with patch("app.workers.runner.get_chain_scraper") as mock_get_scraper:
            mock_scraper = MockSlowScraper()

            async def slow_run():
                await asyncio.sleep(100)  # Longer than timeout

            mock_scraper.run = slow_run
            mock_get_scraper.return_value = mock_scraper

            # Reduce timeout for testing
            with patch("app.workers.runner.SCRAPER_TIMEOUT_MINUTES", 0.01):
                succeeded = await executor.run_scraper("countdown")

            assert succeeded is False
            assert executor.consecutive_failures["countdown"] == 1


# ============================================================================
# Database Persistence Tests
# ============================================================================


class TestDatabasePersistence:
    """Test scraper data persistence to database."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingestion_run_created(self):
        """Test ingestion run is created in database."""

        scraper = MockSuccessfulScraper()

        # Mock database operations
        with patch("app.scrapers.base.async_transaction") as mock_transaction:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            stores_result = MagicMock()
            stores_result.scalars.return_value.all.return_value = []
            run_result = MagicMock()
            mock_run = MagicMock(spec=IngestionRun)
            run_result.scalar_one.return_value = mock_run
            mock_session.execute = AsyncMock(side_effect=[stores_result, run_result])
            mock_transaction.return_value.__aenter__.return_value = mock_session

            with patch.object(
                scraper,
                "_upsert_products_batch",
                AsyncMock(return_value=1),
            ):
                result = await scraper.run()

            assert mock_session.add.called
            assert result is mock_run
            assert mock_run.status == "completed"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_failed_scraper_marks_run_failed(self):
        """Test failed scraper updates run status to failed."""
        scraper = MockFailingScraper()

        with patch("app.scrapers.base.async_transaction") as mock_transaction:
            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            stores_result = MagicMock()
            stores_result.scalars.return_value.all.return_value = []
            mock_result = MagicMock()
            mock_run = MagicMock(spec=IngestionRun)
            mock_result.scalar_one.return_value = mock_run
            mock_session.execute = AsyncMock(side_effect=[stores_result, mock_result])
            mock_transaction.return_value.__aenter__.return_value = mock_session

            with pytest.raises(Exception, match="Simulated scraper failure"):
                await scraper.run()

            assert mock_session.execute.called
            assert mock_run.status == "failed"
            assert "Simulated scraper failure" in mock_run.error_message


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
        assert len(found_chains) > 0, (
            f"Expected at least one known chain, got: {list(CHAINS.keys())}"
        )
