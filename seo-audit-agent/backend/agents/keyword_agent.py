"""
Keyword Research Agent

Collects keywords from multiple sources, deduplicates, groups, and scores them.

Sources:
1. Google Search Console — existing ranking keywords
2. Google Ads Keyword Planner — keyword ideas from seeds
3. SEMrush — domain keywords + related keywords

Output: keywords.json conforming to KeywordResearchOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from collections import defaultdict

from backend.connectors.semrush_connector import SEMrushConnector
from backend.connectors.gsc_connector import GSCConnector
from backend.connectors.gads_connector import GoogleAdsConnector
from backend.utils.grouping import group_keywords, get_group_summary
from backend.utils.scoring import keyword_opportunity_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def run(config: dict, output_path: str):
    """Run the keyword research agent."""
    site_url = config["website_url"]
    domain = site_url.replace("https://", "").replace("http://", "").rstrip("/")
    target_count = config.get("keyword_count", 5000)
    seed_keywords = config.get("seed_keywords", [])
    category = config.get("category", "")
    market_db_map = {
        "India": "in", "United States": "us", "United Kingdom": "uk",
        "Global": "us", "Southeast Asia": "in", "Europe": "uk",
    }
    db = market_db_map.get(config.get("target_market", "India"), "in")

    all_keywords: dict[str, dict] = {}  # keyword -> data

    # ── Source 1: Google Search Console ────────────────
    try:
        logger.info("Fetching keywords from Google Search Console...")
        gsc = GSCConnector()
        gsc_data = gsc.get_queries(site_url, limit=target_count)
        for row in gsc_data:
            kw = row["query"].lower().strip()
            if kw and len(kw) > 1:
                all_keywords[kw] = {
                    "keyword": kw,
                    "volume": 0,  # GSC doesn't provide volume; will be enriched
                    "difficulty": 0,
                    "cpc": 0.0,
                    "position": row.get("position"),
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "source": "gsc",
                }
        logger.info(f"GSC: collected {len(gsc_data)} keywords")
    except Exception as e:
        logger.warning(f"GSC connector failed: {e}")

    # ── Source 2: Google Ads Keyword Planner ───────────
    try:
        logger.info("Fetching keyword ideas from Google Ads...")
        geo_map = {"India": "2356", "United States": "2840", "United Kingdom": "2826"}
        geo = geo_map.get(config.get("target_market", "India"), "2356")
        gads = GoogleAdsConnector()
        gads_data = gads.get_keyword_ideas(
            seed_keywords=seed_keywords, geo_target=geo, limit=target_count
        )
        for row in gads_data:
            kw = row["keyword"].lower().strip()
            if kw and len(kw) > 1 and kw not in all_keywords:
                all_keywords[kw] = {
                    "keyword": kw,
                    "volume": row.get("volume", 0),
                    "difficulty": 0,
                    "cpc": row.get("high_bid", 0),
                    "source": "gads",
                }
        logger.info(f"Google Ads: collected {len(gads_data)} keyword ideas")
    except Exception as e:
        logger.warning(f"Google Ads connector failed: {e}")

    # ── Source 3: SEMrush ──────────────────────────────
    try:
        logger.info("Fetching keywords from SEMrush...")
        semrush = SEMrushConnector()

        # Domain organic keywords
        domain_kws = semrush.domain_organic_keywords(domain, database=db, limit=target_count)
        for row in domain_kws:
            kw = row.get("Ph", "").lower().strip()
            if kw and len(kw) > 1:
                existing = all_keywords.get(kw, {})
                all_keywords[kw] = {
                    "keyword": kw,
                    "volume": int(row.get("Nq", existing.get("volume", 0))),
                    "difficulty": int(row.get("Kd", existing.get("difficulty", 0))),
                    "cpc": float(row.get("Cp", existing.get("cpc", 0))),
                    "position": int(row.get("Po", 0)) or existing.get("position"),
                    "url": row.get("Ur", ""),
                    "source": "semrush",
                }
        logger.info(f"SEMrush domain keywords: {len(domain_kws)}")

        # Related keywords from seeds
        for seed in seed_keywords[:10]:
            related = semrush.keyword_related(seed, database=db, limit=200)
            for row in related:
                kw = row.get("Ph", "").lower().strip()
                if kw and len(kw) > 1 and kw not in all_keywords:
                    all_keywords[kw] = {
                        "keyword": kw,
                        "volume": int(row.get("Nq", 0)),
                        "difficulty": int(row.get("Kd", 0)),
                        "cpc": float(row.get("Cp", 0)),
                        "source": "semrush",
                    }

            # Question keywords
            questions = semrush.keyword_questions(seed, database=db, limit=50)
            for row in questions:
                kw = row.get("Ph", "").lower().strip()
                if kw and len(kw) > 1 and kw not in all_keywords:
                    all_keywords[kw] = {
                        "keyword": kw,
                        "volume": int(row.get("Nq", 0)),
                        "difficulty": int(row.get("Kd", 0)),
                        "cpc": float(row.get("Cp", 0)),
                        "source": "semrush",
                    }

        logger.info(f"Total unique keywords after SEMrush: {len(all_keywords)}")
    except Exception as e:
        logger.warning(f"SEMrush connector failed: {e}")

    # ── Deduplicate & Limit ────────────────────────────
    keywords_list = sorted(
        all_keywords.values(),
        key=lambda x: x.get("volume", 0),
        reverse=True,
    )[:target_count]

    # ── Group & Score ──────────────────────────────────
    logger.info(f"Grouping {len(keywords_list)} keywords...")
    brand_terms = [domain.split(".")[0]]
    keywords_list = group_keywords(keywords_list, brand_terms=brand_terms)

    for kw in keywords_list:
        score, label = keyword_opportunity_score(
            volume=kw.get("volume", 0),
            difficulty=kw.get("difficulty", 0),
            current_position=kw.get("position"),
            cpc=kw.get("cpc", 0),
        )
        kw["opportunity_score"] = score
        kw["opportunity"] = label

    # ── Build Output ───────────────────────────────────
    groups = get_group_summary(keywords_list)

    output = {
        "total": len(keywords_list),
        "groups": groups,
        "keywords": keywords_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Keyword research complete: {len(keywords_list)} keywords → {output_path}")
    logger.info(f"   Groups: {groups}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keyword Research Agent")
    parser.add_argument("--config", required=True, help="Path to audit config JSON")
    parser.add_argument("--output", required=True, help="Output path for keywords JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    run(config, args.output)
