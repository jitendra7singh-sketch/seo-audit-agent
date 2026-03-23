"""
Gap Analysis Agent

Identifies:
1. Keyword Gap — keywords competitors rank for that you don't (or rank poorly)
2. Content Page Gap — page types/topics competitors cover that you don't

Output: gap-analysis.json conforming to GapAnalysisOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from collections import defaultdict

from backend.connectors.semrush_connector import SEMrushConnector
from backend.utils.scoring import gap_opportunity_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def run(config: dict, keywords_path: str, competitors_path: str,
        pages_path: str, output_path: str):
    """Run gap analysis agent."""
    site_url = config["website_url"]
    domain = site_url.replace("https://", "").replace("http://", "").rstrip("/")

    market_db_map = {
        "India": "in", "United States": "us", "United Kingdom": "uk",
        "Global": "us", "Southeast Asia": "in", "Europe": "uk",
    }
    db = market_db_map.get(config.get("target_market", "India"), "in")

    # Load existing data
    with open(keywords_path) as f:
        kw_data = json.load(f)
    with open(competitors_path) as f:
        comp_data = json.load(f)
    with open(pages_path) as f:
        pages_data = json.load(f)

    # Your keywords (keyword -> position mapping)
    your_keywords = {}
    for kw in kw_data.get("keywords", []):
        pos = kw.get("position")
        your_keywords[kw["keyword"]] = pos

    # Selected competitors
    competitors = [c for c in comp_data.get("competitors", [])
                   if c.get("selected") or c.get("verified")][:5]

    semrush = SEMrushConnector()

    # ── 1. Keyword Gap ─────────────────────────────────
    logger.info("Analyzing keyword gaps...")
    competitor_keywords: dict[str, dict[str, int]] = {}  # keyword -> {domain: position}

    for comp in competitors:
        comp_domain = comp["domain"]
        logger.info(f"  Fetching keywords for {comp_domain}...")
        try:
            comp_kws = semrush.domain_organic_keywords(comp_domain, database=db, limit=5000)
            for row in comp_kws:
                kw = row.get("Ph", "").lower().strip()
                pos = int(row.get("Po", 0))
                vol = int(row.get("Nq", 0))
                diff = int(row.get("Kd", 0))
                cpc = float(row.get("Cp", 0))

                if kw not in competitor_keywords:
                    competitor_keywords[kw] = {
                        "volume": vol, "difficulty": diff, "cpc": cpc,
                        "competitors": {}
                    }
                competitor_keywords[kw]["competitors"][comp_domain] = pos
        except Exception as e:
            logger.warning(f"Failed to fetch keywords for {comp_domain}: {e}")

    # Find gaps: keywords where competitors rank but you don't (or rank poorly)
    keyword_gaps = []
    for kw, data in competitor_keywords.items():
        your_pos = your_keywords.get(kw)
        comp_positions = data["competitors"]

        # Gap = you don't rank in top 20, but at least one competitor does in top 20
        best_comp_pos = min(comp_positions.values()) if comp_positions else 999
        is_gap = (your_pos is None or your_pos > 20) and best_comp_pos <= 20

        if is_gap:
            score, label = gap_opportunity_score(
                volume=data["volume"],
                difficulty=data["difficulty"],
                your_position=your_pos,
                best_competitor_position=best_comp_pos,
            )
            keyword_gaps.append({
                "term": kw,
                "your_position": your_pos,
                "competitor_positions": comp_positions,
                "volume": data["volume"],
                "difficulty": data["difficulty"],
                "cpc": data["cpc"],
                "opportunity_score": score,
                "opportunity": label,
            })

    keyword_gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)

    # ── 2. Content Page Gap ────────────────────────────
    logger.info("Analyzing content page gaps...")

    # Your pages (from GSC or site crawl)
    your_page_types = set()
    your_page_topics = set()
    # Use keyword groups as proxy for topic coverage
    for kw in kw_data.get("keywords", []):
        if kw.get("position") and kw["position"] <= 20:
            your_page_topics.add(kw.get("group", ""))
            your_page_types.add(kw.get("topic_cluster", ""))

    # Competitor page types
    comp_page_types = defaultdict(lambda: defaultdict(int))
    for page in pages_data.get("pages", []):
        ptype = page.get("page_type", "")
        comp = page.get("competitor", "")
        comp_page_types[ptype][comp] += 1

    content_gaps = []
    for ptype, comp_counts in comp_page_types.items():
        # Check if multiple competitors have this page type but you have few/none
        competitors_with = len(comp_counts)
        total_comp_pages = sum(comp_counts.values())

        if competitors_with >= 2 and total_comp_pages >= 5:
            content_gaps.append({
                "term": ptype,
                "your_position": None,
                "competitor_positions": {k: v for k, v in comp_counts.items()},
                "volume": total_comp_pages * 100,  # Estimated potential
                "difficulty": 50,
                "opportunity": "High" if competitors_with >= 3 else "Medium",
                "type": "page_type",
                "competitors_count": competitors_with,
                "total_pages": total_comp_pages,
            })

    content_gaps.sort(key=lambda x: x.get("total_pages", 0), reverse=True)

    # ── Output ─────────────────────────────────────────
    missing_keywords = sum(1 for g in keyword_gaps if g["your_position"] is None)

    output = {
        "keyword_gaps": keyword_gaps[:2000],
        "content_gaps": content_gaps,
        "total_keyword_gaps": len(keyword_gaps),
        "total_content_gaps": len(content_gaps),
        "missing_keywords": missing_keywords,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Gap analysis complete: {len(keyword_gaps)} keyword gaps, "
                f"{len(content_gaps)} content gaps → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gap Analysis Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--competitors", required=True)
    parser.add_argument("--pages", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.keywords, args.competitors, args.pages, args.output)
