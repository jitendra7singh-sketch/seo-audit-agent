"""
Interlinking Analysis Agent

Analyzes internal linking structure using GSC data to find:
1. Orphan pages (pages with no internal links)
2. Hub page opportunities
3. Missing internal link suggestions based on keyword overlap

Output: interlinking.json conforming to InterlinkOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import urlparse

from backend.connectors.gsc_connector import GSCConnector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def find_keyword_overlap(page_a_keywords: set, page_b_keywords: set) -> set:
    """Find common keywords between two pages."""
    return page_a_keywords & page_b_keywords


def suggest_anchor_text(common_keywords: set, target_keyword: str) -> str:
    """Suggest anchor text for an internal link."""
    if target_keyword:
        return target_keyword
    if common_keywords:
        # Pick the shortest common keyword as anchor text
        return min(common_keywords, key=len)
    return ""


def run(config: dict, keywords_path: str, output_path: str):
    """Run interlinking analysis."""
    site_url = config["website_url"]

    # Load keyword data
    with open(keywords_path) as f:
        kw_data = json.load(f)

    # ── 1. Get page-query matrix from GSC ──────────────
    logger.info("Fetching page-query data from GSC...")
    page_keywords: dict[str, dict] = {}  # page_url -> {keywords: set, clicks: int, ...}

    try:
        gsc = GSCConnector()
        matrix = gsc.get_query_page_matrix(site_url, limit=10000)

        for row in matrix:
            page = row.get("page", "")
            query = row.get("query", "")
            clicks = row.get("clicks", 0)
            impressions = row.get("impressions", 0)
            position = row.get("position", 0)

            if page not in page_keywords:
                page_keywords[page] = {
                    "url": page,
                    "keywords": set(),
                    "total_clicks": 0,
                    "total_impressions": 0,
                    "best_position": 999,
                    "top_keyword": "",
                }
            page_keywords[page]["keywords"].add(query)
            page_keywords[page]["total_clicks"] += clicks
            page_keywords[page]["total_impressions"] += impressions
            if position < page_keywords[page]["best_position"]:
                page_keywords[page]["best_position"] = position
                page_keywords[page]["top_keyword"] = query

        logger.info(f"GSC: {len(page_keywords)} pages with keyword data")
    except Exception as e:
        logger.warning(f"GSC connector failed: {e}")
        # Fallback: use keyword data
        for kw in kw_data.get("keywords", []):
            url = kw.get("url", "")
            if url:
                if url not in page_keywords:
                    page_keywords[url] = {
                        "url": url, "keywords": set(),
                        "total_clicks": 0, "total_impressions": 0,
                        "best_position": 999, "top_keyword": "",
                    }
                page_keywords[url]["keywords"].add(kw["keyword"])

    # ── 2. Identify orphan pages ───────────────────────
    # Pages with very low impressions relative to the site average
    if page_keywords:
        avg_impressions = sum(
            p["total_impressions"] for p in page_keywords.values()
        ) / len(page_keywords)

        orphan_pages = [
            p["url"] for p in page_keywords.values()
            if p["total_impressions"] < avg_impressions * 0.1 and p["total_clicks"] < 5
        ]
    else:
        orphan_pages = []

    logger.info(f"Identified {len(orphan_pages)} potential orphan pages")

    # ── 3. Identify hub pages ──────────────────────────
    # Pages ranking for many keywords = good hub candidates
    hub_pages = sorted(
        [p for p in page_keywords.values() if len(p["keywords"]) >= 5],
        key=lambda x: len(x["keywords"]),
        reverse=True,
    )[:20]

    # ── 4. Generate interlinking suggestions ───────────
    suggestions = []
    pages_list = list(page_keywords.values())

    # Group keywords by topic cluster
    keyword_groups = defaultdict(list)
    for kw in kw_data.get("keywords", []):
        group = kw.get("group", kw.get("topic_cluster", "Other"))
        keyword_groups[group].append(kw["keyword"])

    # For each pair of pages with keyword overlap, suggest a link
    processed_pairs = set()
    for i, page_a in enumerate(pages_list):
        for j, page_b in enumerate(pages_list):
            if i >= j:
                continue
            pair_key = (page_a["url"], page_b["url"])
            if pair_key in processed_pairs:
                continue

            overlap = find_keyword_overlap(page_a["keywords"], page_b["keywords"])
            if len(overlap) >= 2:  # At least 2 common keywords
                processed_pairs.add(pair_key)

                # Determine which page should link to which
                # Higher authority page links to lower authority page
                if page_a["total_clicks"] >= page_b["total_clicks"]:
                    source, target = page_a, page_b
                else:
                    source, target = page_b, page_a

                anchor = suggest_anchor_text(overlap, target["top_keyword"])

                # Find keyword group
                group = "Other"
                for g, kws in keyword_groups.items():
                    if any(kw in overlap for kw in kws):
                        group = g
                        break

                priority = "High" if len(overlap) >= 5 else ("Medium" if len(overlap) >= 3 else "Low")

                suggestions.append({
                    "source_url": source["url"],
                    "target_url": target["url"],
                    "anchor_text": anchor,
                    "keyword_group": group,
                    "priority": priority,
                    "common_keywords": len(overlap),
                    "reason": f"{len(overlap)} common keywords between pages",
                })

            if len(suggestions) >= 500:
                break
        if len(suggestions) >= 500:
            break

    # Sort by priority
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    suggestions.sort(key=lambda x: (priority_order.get(x["priority"], 2), -x["common_keywords"]))

    # ── Output ─────────────────────────────────────────
    output = {
        "total_suggestions": len(suggestions),
        "orphan_pages": orphan_pages[:100],
        "hub_pages": [{"url": p["url"], "keyword_count": len(p["keywords"]),
                       "top_keyword": p["top_keyword"]} for p in hub_pages],
        "suggestions": suggestions[:200],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Interlinking analysis complete: {len(suggestions)} suggestions, "
                f"{len(orphan_pages)} orphans → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interlinking Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.keywords, args.output)
