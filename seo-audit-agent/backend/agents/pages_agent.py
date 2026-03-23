"""
Top Pages Agent

For each selected competitor, fetches top organic pages via SEMrush,
classifies page types, and maps to keyword groups.

Output: top-pages.json conforming to TopPagesOutput schema
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import urlparse

from backend.connectors.semrush_connector import SEMrushConnector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# ── Page Type Classification ───────────────────────────

PAGE_TYPE_PATTERNS = {
    "Homepage": [r"^/$", r"^/index"],
    "Blog/Article": [r"/blog/", r"/article/", r"/news/", r"/post/", r"/stories/"],
    "Category/Hub": [r"^/[a-z-]+/?$", r"/category/", r"/topics/"],
    "Product/Service": [r"/product/", r"/service/", r"/tour/", r"/package/"],
    "FAQ": [r"/faq", r"/help/", r"/support/"],
    "How-to/Guide": [r"/how-to", r"/guide/", r"/tutorial/"],
    "Comparison": [r"/compare", r"/vs-", r"-vs-", r"/versus"],
    "Review": [r"/review", r"/rating"],
    "Tool/Calculator": [r"/tool/", r"/calculator/", r"/checker/", r"/converter/"],
    "Location": [r"/city/", r"/state/", r"/country/", r"/location/", r"/destination/"],
    "Landing Page": [r"/lp/", r"/landing/", r"/promo/", r"/offer/"],
    "Glossary": [r"/glossary/", r"/dictionary/", r"/meaning/", r"/definition/"],
}


def classify_page_type(url: str) -> str:
    """Classify a URL into a page type."""
    path = urlparse(url).path.lower()
    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path):
                return page_type
    # Heuristic fallbacks
    segments = [s for s in path.split("/") if s]
    if len(segments) == 0:
        return "Homepage"
    if len(segments) == 1:
        return "Category/Hub"
    if len(segments) >= 3:
        return "Blog/Article"
    return "Product/Service"


def run(config: dict, competitors_path: str, output_path: str):
    """Run top pages agent."""
    page_limit = config.get("competitor_page_count", 2000)

    market_db_map = {
        "India": "in", "United States": "us", "United Kingdom": "uk",
        "Global": "us", "Southeast Asia": "in", "Europe": "uk",
    }
    db = market_db_map.get(config.get("target_market", "India"), "in")

    # Load competitors
    with open(competitors_path) as f:
        comp_data = json.load(f)

    # Only analyze selected/verified competitors
    competitors = [c for c in comp_data.get("competitors", [])
                   if c.get("selected") or c.get("verified")]

    if not competitors:
        logger.warning("No competitors selected — using all competitors")
        competitors = comp_data.get("competitors", [])[:5]

    semrush = SEMrushConnector()
    all_pages = []
    pages_per_competitor = max(100, page_limit // len(competitors))

    for comp in competitors:
        comp_domain = comp["domain"]
        logger.info(f"Fetching top pages for {comp_domain}...")

        try:
            raw_pages = semrush.domain_pages(
                comp_domain, database=db, limit=pages_per_competitor
            )
            for page in raw_pages:
                url = page.get("url", "")
                if not url:
                    continue
                full_url = url if url.startswith("http") else f"https://{comp_domain}{url}"
                page_type = classify_page_type(full_url)

                all_pages.append({
                    "url": full_url,
                    "competitor": comp_domain,
                    "estimated_traffic": page.get("traffic", 0),
                    "keyword_count": page.get("keywords", 0),
                    "page_type": page_type,
                    "top_keyword": page.get("top_keyword", ""),
                    "top_position": page.get("top_position", 0),
                })

            logger.info(f"  {comp_domain}: {len(raw_pages)} pages")
        except Exception as e:
            logger.warning(f"Failed to fetch pages for {comp_domain}: {e}")

    # Sort by traffic and limit
    all_pages.sort(key=lambda x: x.get("estimated_traffic", 0), reverse=True)
    all_pages = all_pages[:page_limit]

    # Add IDs
    for i, page in enumerate(all_pages):
        page["id"] = i + 1

    # Page type distribution
    type_dist = defaultdict(int)
    for page in all_pages:
        type_dist[page["page_type"]] += 1

    output = {
        "total": len(all_pages),
        "pages": all_pages,
        "page_type_distribution": dict(sorted(type_dist.items(), key=lambda x: -x[1])),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Top pages analysis complete: {len(all_pages)} pages → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Top Pages Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--competitors", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.competitors, args.output)
