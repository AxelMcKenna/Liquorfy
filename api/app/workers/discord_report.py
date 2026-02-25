"""
Daily Discord report for scraper runs.

Sends an embed summary to a Discord webhook after each scraper pass,
showing which chains succeeded, failed, or had no data.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List

import httpx
from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from app.db.models import IngestionRun
from app.db.session import get_async_session
from app.scrapers.registry import CHAINS

logger = logging.getLogger(__name__)

# Discord embed colour codes
_GREEN = 0x2ECC71
_AMBER = 0xF1C40F
_RED = 0xE74C3C


async def _fetch_latest_runs() -> Dict[str, IngestionRun]:
    """Return the most recent IngestionRun per chain."""
    async with get_async_session() as session:
        subquery = (
            select(
                IngestionRun,
                func.row_number()
                .over(
                    partition_by=IngestionRun.chain,
                    order_by=desc(IngestionRun.started_at),
                )
                .label("rn"),
            )
            .where(IngestionRun.chain.in_(CHAINS))
            .subquery()
        )

        ir_alias = aliased(IngestionRun, subquery)
        result = await session.execute(
            select(ir_alias).where(subquery.c.rn == 1)
        )
        latest_runs = result.scalars().all()

    return {run.chain: run for run in latest_runs}


def _format_duration(run: IngestionRun) -> str:
    """Format run duration as e.g. '3m 12s'."""
    if not run.finished_at or not run.started_at:
        return "??"
    delta = run.finished_at - run.started_at
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}m {seconds}s"


def _build_embed(chain_runs: Dict[str, IngestionRun]) -> dict:
    """Assemble a Discord embed payload from the latest runs."""
    completed: List[str] = []
    failed: List[str] = []
    no_data: List[str] = []

    total_items = 0
    total_changed = 0
    total_failed_items = 0

    for chain in sorted(CHAINS):
        run = chain_runs.get(chain)
        if run is None:
            no_data.append(f"**{chain}**: no run recorded")
            continue

        if run.status == "completed":
            line = (
                f"**{chain}**: {run.items_total} items, "
                f"{run.items_changed} changed, "
                f"{run.items_failed} failed "
                f"({_format_duration(run)})"
            )
            completed.append(line)
            total_items += run.items_total
            total_changed += run.items_changed
            total_failed_items += run.items_failed
        else:
            line = f"**{chain}**: status={run.status} ({_format_duration(run)})"
            failed.append(line)

    # Pick colour
    if failed or no_data:
        colour = _RED
    elif total_failed_items > 0:
        colour = _AMBER
    else:
        colour = _GREEN

    fields = [
        {
            "name": "Summary",
            "value": (
                f"{len(completed)} completed, "
                f"{len(failed)} failed, "
                f"{len(no_data)} missing\n"
                f"**{total_items}** items total, "
                f"**{total_changed}** changed, "
                f"**{total_failed_items}** item failures"
            ),
            "inline": False,
        }
    ]

    if completed:
        fields.append({
            "name": "Completed",
            "value": "\n".join(completed),
            "inline": False,
        })
    if failed:
        fields.append({
            "name": "Failed",
            "value": "\n".join(failed),
            "inline": False,
        })
    if no_data:
        fields.append({
            "name": "No Data",
            "value": "\n".join(no_data),
            "inline": False,
        })

    return {
        "embeds": [
            {
                "title": "Liquorfy Scraper Report",
                "color": colour,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


async def send_discord_report() -> None:
    """
    Fetch latest scraper runs and POST a summary embed to Discord.

    Reads DISCORD_WEBHOOK_URL from env. No-ops silently if unset.
    Wrapped in try/except so it can never crash the worker.
    """
    try:
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            logger.debug("DISCORD_WEBHOOK_URL not set — skipping report")
            return

        chain_runs = await _fetch_latest_runs()
        payload = _build_embed(chain_runs)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()

        logger.info("Discord scraper report sent successfully")
    except Exception as e:
        logger.warning(f"Discord report failed (non-fatal): {e}")
