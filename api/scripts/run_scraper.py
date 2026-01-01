"""Run a specific scraper."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.registry import CHAINS as SCRAPERS


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_scraper.py <chain> [--live]")
        print(f"Available chains: {', '.join(SCRAPERS.keys())}")
        sys.exit(1)

    chain = sys.argv[1].lower()
    use_fixtures = "--live" not in sys.argv

    if chain not in SCRAPERS:
        print(f"Unknown chain: {chain}")
        print(f"Available chains: {', '.join(SCRAPERS.keys())}")
        sys.exit(1)

    scraper_class = SCRAPERS[chain]

    # Try to instantiate with use_fixtures if supported
    try:
        scraper = scraper_class(use_fixtures=use_fixtures)
        mode = "fixture" if use_fixtures else "live HTTP"
    except TypeError:
        # Some scrapers don't accept use_fixtures (e.g., API-based)
        scraper = scraper_class()
        mode = "live API"

    print(f"Running {chain} scraper in {mode} mode...")

    try:
        run = await scraper.run()
        print(f"\nScraper completed successfully!")
        print(f"Status: {run.status}")
        print(f"Total items: {run.items_total}")
        print(f"Changed items: {run.items_changed}")
        print(f"Failed items: {run.items_failed}")
        print(f"Started: {run.started_at}")
        print(f"Finished: {run.finished_at}")
    except Exception as e:
        print(f"\nScraper failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
