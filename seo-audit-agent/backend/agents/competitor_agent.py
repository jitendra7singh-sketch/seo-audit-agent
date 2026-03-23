"""
Competitor Discovery Agent

Discovers organic competitors using SEMrush domain data,
enriches with DA/traffic metrics, and outputs for user verification.

Output: competitors.json conforming to CompetitorOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

from backend.connectors.semrush_connector import SEMrushConnector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def run(config: dict, keywords_path: str, output_path: str):
    """Run competitor discovery agent."""
    site_url = config["website_url"]
    domain = site_url.replace("https://", "").replace("http://", "").rstrip("/")
    max_competitors = config.get("max_competitors", 10)
    known_competitors = config.get("known_competitors", [])

    market_db_map = {
        "India": "in", "United States": "us", "United Kingdom": "uk",
        "Global": "us", "Southeast Asia": "in", "Europe": "uk",
    }
    db = market_db_map.get(config.get("target_market", "India"), "in")

    semrush = SEMrushConnector()
    competitors_map: dict[str, dict] = {}

    # ── 1. SEMrush Organic Competitors ─────────────────
    logger.info(f"Discovering competitors for {domain}...")
    try:
        raw_competitors = semrush.domain_competitors(domain, database=db, limit=50)
        for row in raw_competitors:
            comp_domain = row.get("Dn", "").strip().lower()
            if not comp_domain or comp_domain == domain:
                continue
            competitors_map[comp_domain] = {
                "domain": comp_domain,
                "overlap_pct": round(float(row.get("Cr", 0)) * 100, 1),
                "common_keywords": int(row.get("Np", 0)),
                "total_keywords": int(row.get("Or", 0)),
                "estimated_traffic": str(int(float(row.get("Ot", 0)))),
                "source": "semrush",
            }
        logger.info(f"SEMrush found {len(competitors_map)} organic competitors")
    except Exception as e:
        logger.warning(f"SEMrush competitor discovery failed: {e}")

    # ── 2. Add known competitors ───────────────────────
    for known in known_competitors:
        known = known.strip().lower()
        if known and known not in competitors_map and known != domain:
            competitors_map[known] = {
                "domain": known,
                "overlap_pct": 0,
                "common_keywords": 0,
                "total_keywords": 0,
                "estimated_traffic": "0",
                "source": "manual",
            }

    # ── 3. Enrich with domain overview ─────────────────
    logger.info("Enriching competitor metrics...")
    for comp_domain, data in competitors_map.items():
        try:
            overview = semrush.domain_overview(comp_domain, database=db)
            if overview:
                data["total_keywords"] = int(overview.get("Or", data["total_keywords"]))
                data["estimated_traffic"] = str(int(float(overview.get("Ot", data["estimated_traffic"]))))
                data["da"] = int(overview.get("Rk", 0))  # Rank as proxy
                data["paid_keywords"] = int(overview.get("Ad", 0))
        except Exception as e:
            logger.warning(f"Failed to enrich {comp_domain}: {e}")
            data["da"] = 0

    # ── 4. Get DA from backlinks overview ──────────────
    for comp_domain, data in competitors_map.items():
        try:
            bl_overview = semrush.backlinks_overview(comp_domain)
            if bl_overview:
                data["da"] = int(bl_overview.get("ascore", data.get("da", 0)))
        except Exception as e:
            logger.debug(f"Backlink overview failed for {comp_domain}: {e}")

    # ── 5. Sort and limit ──────────────────────────────
    competitors_list = sorted(
        competitors_map.values(),
        key=lambda x: x.get("overlap_pct", 0),
        reverse=True,
    )[:max_competitors]

    # Add metadata
    for i, comp in enumerate(competitors_list):
        comp["id"] = i + 1
        comp["verified"] = comp["domain"] in known_competitors
        comp["selected"] = comp["verified"]  # pre-select known ones

    # ── Output ─────────────────────────────────────────
    output = {
        "total": len(competitors_list),
        "competitors": competitors_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Competitor discovery complete: {len(competitors_list)} competitors → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Competitor Discovery Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.keywords, args.output)
