"""
Backlink Gap Agent

Analyzes:
1. Referring Domain Gap — domains linking to competitors but not you
2. DA 30+ Referring Domain Gap — high-authority domains gap
3. Backlink Gap — overall link profile comparison

Uses SEMrush Backlink Analytics API.

Output: backlinks.json conforming to BacklinkOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from collections import defaultdict

from backend.connectors.semrush_connector import SEMrushConnector
from backend.utils.scoring import backlink_opportunity_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def run(config: dict, competitors_path: str, output_path: str):
    """Run backlink gap analysis."""
    site_url = config["website_url"]
    domain = site_url.replace("https://", "").replace("http://", "").rstrip("/")
    min_da = config.get("min_referring_da", 30)

    with open(competitors_path) as f:
        comp_data = json.load(f)

    competitors = [c for c in comp_data.get("competitors", [])
                   if c.get("selected") or c.get("verified")][:5]

    semrush = SEMrushConnector()

    # ── 1. Get your referring domains ──────────────────
    logger.info(f"Fetching referring domains for {domain}...")
    your_domains = set()
    try:
        your_refs = semrush.backlinks_referring_domains(domain, limit=500)
        for row in your_refs:
            ref_domain = row.get("domain", "").lower().strip()
            if ref_domain:
                your_domains.add(ref_domain)
        logger.info(f"  Your site: {len(your_domains)} referring domains")
    except Exception as e:
        logger.warning(f"Failed to fetch your backlinks: {e}")

    # ── 2. Get competitor referring domains ─────────────
    all_ref_domains: dict[str, dict] = {}  # ref_domain -> data

    for comp in competitors:
        comp_domain = comp["domain"]
        logger.info(f"Fetching referring domains for {comp_domain}...")
        try:
            comp_refs = semrush.backlinks_referring_domains(comp_domain, limit=500)
            for row in comp_refs:
                ref_domain = row.get("domain", "").lower().strip()
                da = int(row.get("domain_ascore", 0))
                if not ref_domain:
                    continue

                if ref_domain not in all_ref_domains:
                    all_ref_domains[ref_domain] = {
                        "domain": ref_domain,
                        "da": da,
                        "your_site": ref_domain in your_domains,
                        "competitor_presence": {},
                        "backlinks_count": int(row.get("backlinks_num", 0)),
                        "country": row.get("country", ""),
                    }
                all_ref_domains[ref_domain]["competitor_presence"][comp_domain] = True
                # Update DA to highest seen
                all_ref_domains[ref_domain]["da"] = max(
                    all_ref_domains[ref_domain]["da"], da
                )
            logger.info(f"  {comp_domain}: {len(comp_refs)} referring domains")
        except Exception as e:
            logger.warning(f"Failed to fetch backlinks for {comp_domain}: {e}")

    # ── 3. Identify gaps ───────────────────────────────
    referring_domain_gap = []
    total_competitors = len(competitors)

    for ref_domain, data in all_ref_domains.items():
        # Skip if you already have this domain
        if data["your_site"]:
            continue

        da = data["da"]
        comp_count = len(data["competitor_presence"])

        # Classify domain type (heuristic)
        domain_type = "Blog"
        if any(ext in ref_domain for ext in [".edu", ".ac."]):
            domain_type = "Edu"
        elif any(ext in ref_domain for ext in [".gov", ".nic."]):
            domain_type = "Gov"
        elif any(word in ref_domain for word in ["news", "times", "herald", "gazette", "post"]):
            domain_type = "News"
        elif any(word in ref_domain for word in ["forum", "community", "discuss"]):
            domain_type = "Forum"
        elif any(word in ref_domain for word in ["directory", "listing", "yellow"]):
            domain_type = "Directory"

        score, label = backlink_opportunity_score(da, comp_count, total_competitors)

        referring_domain_gap.append({
            "domain": ref_domain,
            "da": da,
            "your_site": False,
            "competitor_presence": data["competitor_presence"],
            "domain_type": domain_type,
            "is_da30_plus": da >= 30,
            "competitors_linking": comp_count,
            "opportunity_score": score,
            "opportunity": label,
        })

    # Sort by opportunity score
    referring_domain_gap.sort(key=lambda x: x["opportunity_score"], reverse=True)

    # ── 4. Summary stats ───────────────────────────────
    da30_plus = [d for d in referring_domain_gap if d["is_da30_plus"]]

    backlink_gap_summary = {}
    for comp in competitors:
        comp_domain = comp["domain"]
        gaps_for_comp = sum(
            1 for d in referring_domain_gap
            if comp_domain in d["competitor_presence"]
        )
        backlink_gap_summary[comp_domain] = gaps_for_comp

    # ── Output ─────────────────────────────────────────
    output = {
        "total_referring_domains": len(referring_domain_gap),
        "da30_plus_domains": len(da30_plus),
        "your_referring_domains": len(your_domains),
        "referring_domain_gap": referring_domain_gap,
        "da30_plus_gap": da30_plus,
        "backlink_gap_summary": backlink_gap_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Backlink gap analysis complete: {len(referring_domain_gap)} domain gaps "
                f"({len(da30_plus)} DA30+) → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backlink Gap Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--competitors", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.competitors, args.output)
