"""Periodic refresh script.

Runs on a schedule (e.g. cron) to:
1. Scrape the current active auctions from alermipianovendite.it.
2. Write the result to a timestamped snapshot file in data/cache/ — the existing
   canonical active_auction_lots.json is never overwritten.
3. Add first_seen/last_seen timestamps to entries in the canonical cache file.
4. Compare the scraped auction titles/dates against the known dataset to detect
   auctions not yet catalogued.
5. For each uncatalogued auction:
   - Trigger the historical PDF extraction pipeline.
   - Trigger the Wayback Machine discovery → URL extraction → detail fetching pipeline.
6. Run the downstream stages (integration → geocoding → price analysis) when new
   data was collected or --force-downstream is passed.

Usage (from the repo root):
    uv run python pipeline/scripts/run_periodic_refresh.py
    uv run python pipeline/scripts/run_periodic_refresh.py --force-downstream
"""
import importlib.util
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# pipeline/scripts/ → pipeline/ → repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CANONICAL_CACHE = CACHE_DIR / "active_auction_lots.json"
SCRIPTS_DIR = PROJECT_ROOT / "pipeline" / "scripts"


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_scraper():
    """Import run_active_auction_scraper without relying on package structure."""
    spec = importlib.util.spec_from_file_location(
        "run_active_auction_scraper",
        SCRIPTS_DIR / "run_active_auction_scraper.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_script(name: str) -> bool:
    """Run a pipeline script via uv from the repo root and return True on success."""
    script = SCRIPTS_DIR / name
    logger.info("Running %s …", name)
    result = subprocess.run(
        ["uv", "run", "python", str(script)],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        logger.error("%s failed (exit %d)", name, result.returncode)
        return False
    return True


def _known_auction_keys() -> set[str]:
    """Return normalised (title|date) keys from the canonical cache."""
    keys: set[str] = set()
    if not CANONICAL_CACHE.exists():
        return keys
    try:
        data = json.loads(CANONICAL_CACHE.read_text(encoding="utf-8"))
        for a in data.get("active_auctions", []):
            keys.add(_key(a.get("title", ""), a.get("auction_date", "")))
    except Exception as e:
        logger.warning("Could not read canonical cache: %s", e)
    return keys


def _key(title: str, date: str) -> str:
    return f"{title.strip().lower()}|{(date or '').strip()}"


def _write_timestamped_snapshot(data: dict) -> Path:
    """Write scraped data to a new timestamped file; never touch the canonical one."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = CACHE_DIR / f"active_auction_lots_{ts}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Snapshot written → %s", path)
    return path


def _annotate_canonical_cache(now_iso: str) -> None:
    """Add first_seen/last_seen timestamps to entries in the canonical cache file.

    The fields first_seen and last_seen are appended without altering any other
    field. If the file does not exist this is a no-op.
    """
    if not CANONICAL_CACHE.exists():
        return
    try:
        data = json.loads(CANONICAL_CACHE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Could not annotate canonical cache: %s", e)
        return

    origin = data.get("scraped_at", now_iso)
    changed = False

    for entry in (*data.get("active_auctions", []), *data.get("lots", [])):
        if "first_seen" not in entry:
            entry["first_seen"] = origin
            changed = True
        if entry.get("last_seen") != now_iso:
            entry["last_seen"] = now_iso
            changed = True

    if changed:
        CANONICAL_CACHE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("Annotated canonical cache with timestamps")


# ── main ─────────────────────────────────────────────────────────────────────

def main(force_downstream: bool = False) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Scrape current active auctions using the existing scraper module.
    #    We override its OUTPUT_PATH so it writes to the canonical location
    #    at the project root, then restore the original value immediately after
    #    to avoid persistent side-effects if the module is imported elsewhere.
    logger.info("=== Step 1: Scrape active auctions ===")
    scraper = _load_scraper()
    original_output_path = scraper.OUTPUT_PATH
    scraper.OUTPUT_PATH = CANONICAL_CACHE  # write to the correct project-root path

    try:
        scraped = scraper.scrape_active_auctions()
    except Exception as e:
        logger.error("Scraping failed: %s", e)
        sys.exit(1)
    finally:
        scraper.OUTPUT_PATH = original_output_path

    # 2. Write a timestamped snapshot alongside the canonical file.
    snapshot_path = _write_timestamped_snapshot(scraped)

    # 3. Annotate old entries in the canonical cache with timestamps.
    _annotate_canonical_cache(now_iso)

    # 4. Detect auctions not yet in the canonical cache prior to this run.
    logger.info("=== Step 2: Detect new auctions ===")
    known_keys = _known_auction_keys()
    new_auctions = [
        a for a in scraped.get("active_auctions", [])
        if _key(a.get("title", ""), a.get("auction_date", "")) not in known_keys
    ]

    if not new_auctions:
        logger.info("No new auctions detected.")
        if not force_downstream:
            logger.info("Refresh complete. Use --force-downstream to rerun downstream stages.")
            return
        logger.info("--force-downstream: running downstream stages anyway.")
    else:
        logger.info(
            "Found %d new auction(s): %s",
            len(new_auctions),
            [a["title"] for a in new_auctions],
        )

    # 5a. Historical PDF extraction for any new auction cycle.
    if new_auctions:
        logger.info("=== Step 3a: Historical PDF extraction ===")
        _run_script("run_historical_extraction.py")

    # 5b. Wayback Machine pipeline for new auctions.
    if new_auctions:
        logger.info("=== Step 3b: Wayback Machine pipeline ===")
        ok = _run_script("run_wayback_discovery.py")
        if ok:
            ok = _run_script("run_url_extraction.py")
        if ok:
            ok = _run_script("run_detail_fetching.py")
        if ok:
            _run_script("run_data_extraction.py")

    # 6. Downstream pipeline: PDF extraction → integration → geocoding → analysis.
    if new_auctions or force_downstream:
        logger.info("=== Step 4: Downstream pipeline ===")
        ok = _run_script("run_pdf_extraction.py")
        if ok:
            ok = _run_script("run_dataset_integration.py")
        if ok:
            ok = _run_script("run_geocoding.py")
        if ok:
            _run_script("run_price_analysis.py")

    logger.info("=== Periodic refresh complete ===")
    logger.info("Snapshot: %s", snapshot_path)
    if new_auctions:
        logger.info("New auctions processed: %s", [a["title"] for a in new_auctions])


if __name__ == "__main__":
    main(force_downstream="--force-downstream" in sys.argv)
