"""
Action Plan Agent

Synthesizes all audit data into a comprehensive, prioritized SEO action plan.

Reads all JSON outputs from previous agents and generates:
- Overall SEO health score
- Categorized action items (Content, Technical, Backlinks, Interlinking)
- Quick wins
- Timeline recommendations

Output: action-plan.json conforming to ActionPlanOutput schema
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def load_json(path: str) -> dict:
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load {path}: {e}")
        return {}


def calculate_health_score(
    keywords: dict, gaps: dict, backlinks: dict, interlinking: dict
) -> int:
    """Calculate overall SEO health score 0-100."""
    score = 50  # baseline

    # Keyword coverage (0-20 points)
    total_kw = keywords.get("total", 0)
    if total_kw >= 5000:
        score += 20
    elif total_kw >= 2000:
        score += 15
    elif total_kw >= 500:
        score += 10
    else:
        score += 5

    # Gap severity (-20 to 0)
    missing = gaps.get("missing_keywords", 0)
    total_gaps = gaps.get("total_keyword_gaps", 0)
    if total_gaps > 0:
        gap_ratio = missing / max(total_gaps, 1)
        score -= int(gap_ratio * 20)

    # Backlink health (0-15)
    your_refs = backlinks.get("your_referring_domains", 0)
    da30_gap = backlinks.get("da30_plus_domains", 0)
    if your_refs > 200:
        score += 10
    elif your_refs > 50:
        score += 5
    if da30_gap < 20:
        score += 5

    # Interlinking health (0-15)
    orphans = len(interlinking.get("orphan_pages", []))
    if orphans < 10:
        score += 15
    elif orphans < 30:
        score += 10
    elif orphans < 50:
        score += 5

    return max(0, min(100, score))


def generate_content_actions(keywords: dict, gaps: dict, pages: dict) -> list[dict]:
    """Generate content-related action items."""
    items = []

    # High-opportunity keyword gaps
    kw_gaps = gaps.get("keyword_gaps", [])
    high_opp_gaps = [g for g in kw_gaps if g.get("opportunity") == "High"]

    if high_opp_gaps:
        top_keywords = [g["term"] for g in high_opp_gaps[:10]]
        items.append({
            "title": f"Create content for {len(high_opp_gaps)} high-opportunity keyword gaps",
            "description": (
                f"Your competitors rank for {len(high_opp_gaps)} high-opportunity keywords "
                f"where you have no presence. Top targets: {', '.join(top_keywords[:5])}. "
                "Create dedicated landing pages or blog posts targeting these keywords."
            ),
            "priority": "High",
            "category": "Content",
            "estimated_impact": "High",
            "effort": "High",
            "timeline": "Month 1-3",
        })

    # Content page gaps
    content_gaps = gaps.get("content_gaps", [])
    if content_gaps:
        missing_types = [g["term"] for g in content_gaps[:5]]
        items.append({
            "title": f"Add missing page types: {', '.join(missing_types[:3])}",
            "description": (
                f"Competitors have {len(content_gaps)} page types that you're missing. "
                f"Prioritize creating: {', '.join(missing_types)}. "
                "These page types drive significant traffic for competitors."
            ),
            "priority": "High",
            "category": "Content",
            "estimated_impact": "High",
            "effort": "Medium",
            "timeline": "Month 1-2",
        })

    # Quick win keywords (position 11-20)
    all_kws = keywords.get("keywords", [])
    quick_wins = [kw for kw in all_kws
                  if kw.get("position") and 11 <= kw["position"] <= 20
                  and kw.get("volume", 0) >= 500]

    if quick_wins:
        items.append({
            "title": f"Optimize {len(quick_wins)} keywords on page 2 to push to page 1",
            "description": (
                f"You have {len(quick_wins)} keywords ranking on page 2 (positions 11-20) "
                f"with 500+ monthly searches. Optimize existing content, improve on-page SEO, "
                f"and add internal links to push these to page 1. "
                f"Top targets: {', '.join(kw['keyword'] for kw in quick_wins[:5])}."
            ),
            "priority": "High",
            "category": "Content",
            "estimated_impact": "High",
            "effort": "Low",
            "timeline": "Week 1-2",
        })

    # Keyword group coverage
    groups = keywords.get("groups", {})
    low_coverage = {g: c for g, c in groups.items() if c < 50}
    if low_coverage:
        items.append({
            "title": f"Expand content in {len(low_coverage)} underserved keyword groups",
            "description": (
                f"Some keyword groups have low coverage: "
                f"{', '.join(f'{g} ({c} keywords)' for g, c in list(low_coverage.items())[:5])}. "
                "Create topic clusters and pillar pages for these groups."
            ),
            "priority": "Medium",
            "category": "Content",
            "estimated_impact": "Medium",
            "effort": "Medium",
            "timeline": "Month 2-4",
        })

    return items


def generate_backlink_actions(backlinks: dict) -> list[dict]:
    """Generate backlink-related action items."""
    items = []

    da30_gap = backlinks.get("da30_plus_gap", [])
    total_gap = backlinks.get("total_referring_domains", 0)

    if da30_gap:
        high_da = [d for d in da30_gap if d.get("da", 0) >= 50][:10]
        items.append({
            "title": f"Acquire backlinks from {len(da30_gap)} high-authority domains (DA 30+)",
            "description": (
                f"{len(da30_gap)} domains with DA 30+ link to your competitors but not you. "
                f"Top targets: {', '.join(d['domain'] for d in high_da[:5])}. "
                "Prioritize outreach to domains that link to multiple competitors."
            ),
            "priority": "High",
            "category": "Backlinks",
            "estimated_impact": "High",
            "effort": "High",
            "timeline": "Month 1-6",
        })

    # By domain type
    ref_gap = backlinks.get("referring_domain_gap", [])
    type_counts = {}
    for d in ref_gap:
        dtype = d.get("domain_type", "Blog")
        type_counts[dtype] = type_counts.get(dtype, 0) + 1

    if type_counts.get("News", 0) >= 5:
        items.append({
            "title": f"Pursue {type_counts['News']} news/media backlink opportunities",
            "description": (
                "Multiple news domains link to competitors but not you. "
                "Create newsworthy content, press releases, or data studies to earn media coverage."
            ),
            "priority": "Medium",
            "category": "Backlinks",
            "estimated_impact": "High",
            "effort": "Medium",
            "timeline": "Month 2-4",
        })

    if type_counts.get("Edu", 0) >= 2 or type_counts.get("Gov", 0) >= 2:
        items.append({
            "title": "Build .edu and .gov backlinks through scholarship/resource pages",
            "description": (
                "Competitors have educational and government backlinks. "
                "Create scholarship programs, educational resources, or partner with "
                "educational institutions to earn high-authority .edu/.gov links."
            ),
            "priority": "Medium",
            "category": "Backlinks",
            "estimated_impact": "High",
            "effort": "High",
            "timeline": "Month 3-6",
        })

    # General gap
    gap_summary = backlinks.get("backlink_gap_summary", {})
    if gap_summary:
        worst_comp = max(gap_summary.items(), key=lambda x: x[1])
        items.append({
            "title": f"Close the referring domain gap with {worst_comp[0]}",
            "description": (
                f"{worst_comp[0]} has {worst_comp[1]} referring domains that don't link to you. "
                "Implement a sustained link building campaign targeting these domains through "
                "guest posting, broken link building, and digital PR."
            ),
            "priority": "High",
            "category": "Backlinks",
            "estimated_impact": "High",
            "effort": "High",
            "timeline": "Ongoing",
        })

    return items


def generate_interlinking_actions(interlinking: dict) -> list[dict]:
    """Generate interlinking action items."""
    items = []

    orphans = interlinking.get("orphan_pages", [])
    if orphans:
        items.append({
            "title": f"Fix {len(orphans)} orphan pages with no internal links",
            "description": (
                f"{len(orphans)} pages have minimal internal links and very low visibility. "
                "Add contextual internal links from relevant high-authority pages. "
                f"Top orphans: {', '.join(orphans[:3])}."
            ),
            "priority": "High",
            "category": "Interlinking",
            "estimated_impact": "Medium",
            "effort": "Low",
            "timeline": "Week 1-2",
        })

    hubs = interlinking.get("hub_pages", [])
    if hubs:
        items.append({
            "title": f"Strengthen {len(hubs)} hub pages as topic cluster pillars",
            "description": (
                f"{len(hubs)} pages rank for many keywords and serve as topic hubs. "
                "Ensure these pages link to all related subpages and vice versa. "
                "Add table-of-contents sections and related content blocks."
            ),
            "priority": "Medium",
            "category": "Interlinking",
            "estimated_impact": "Medium",
            "effort": "Low",
            "timeline": "Week 2-4",
        })

    suggestions = interlinking.get("suggestions", [])
    high_priority = [s for s in suggestions if s.get("priority") == "High"]
    if high_priority:
        items.append({
            "title": f"Implement {len(high_priority)} high-priority internal links",
            "description": (
                f"Add {len(high_priority)} internal links between pages with high keyword overlap. "
                "Use descriptive anchor text matching target page keywords. "
                "This improves crawlability and distributes link equity."
            ),
            "priority": "High",
            "category": "Interlinking",
            "estimated_impact": "Medium",
            "effort": "Low",
            "timeline": "Week 1-2",
        })

    return items


def generate_technical_actions(keywords: dict, gaps: dict) -> list[dict]:
    """Generate technical SEO action items."""
    items = []

    items.append({
        "title": "Audit and optimize Core Web Vitals",
        "description": (
            "Run PageSpeed Insights on your top 20 landing pages. "
            "Optimize LCP, FID/INP, and CLS metrics. Focus on image optimization, "
            "lazy loading, reducing JavaScript payload, and server response times."
        ),
        "priority": "High",
        "category": "Technical",
        "estimated_impact": "Medium",
        "effort": "Medium",
        "timeline": "Month 1",
    })

    items.append({
        "title": "Implement structured data markup",
        "description": (
            "Add schema.org markup (FAQ, HowTo, Breadcrumb, Product, Review) "
            "to all relevant pages. This improves SERP visibility with rich snippets "
            "and can significantly increase CTR."
        ),
        "priority": "Medium",
        "category": "Technical",
        "estimated_impact": "Medium",
        "effort": "Medium",
        "timeline": "Month 1-2",
    })

    items.append({
        "title": "Review and optimize XML sitemaps",
        "description": (
            "Ensure all important pages are in your sitemap and no-index/blocked pages "
            "are excluded. Submit updated sitemaps to GSC. "
            "Consider separate sitemaps for different content types."
        ),
        "priority": "Medium",
        "category": "Technical",
        "estimated_impact": "Low",
        "effort": "Low",
        "timeline": "Week 1",
    })

    items.append({
        "title": "Optimize meta titles and descriptions for CTR",
        "description": (
            "Review meta titles and descriptions for your top 100 pages. "
            "Include primary keywords, use action-oriented language, and ensure "
            "titles are under 60 characters and descriptions under 155 characters."
        ),
        "priority": "High",
        "category": "Technical",
        "estimated_impact": "Medium",
        "effort": "Low",
        "timeline": "Week 1-2",
    })

    return items


def run(config: dict, data_dir: str, output_path: str):
    """Generate comprehensive SEO action plan."""
    logger.info("Generating SEO action plan...")

    # Load all data
    keywords = load_json(os.path.join(data_dir, "keywords.json"))
    competitors = load_json(os.path.join(data_dir, "competitors.json"))
    pages = load_json(os.path.join(data_dir, "top-pages.json"))
    gaps = load_json(os.path.join(data_dir, "gap-analysis.json"))
    backlinks = load_json(os.path.join(data_dir, "backlinks.json"))
    interlinking = load_json(os.path.join(data_dir, "interlinking.json"))

    # Calculate health score
    score = calculate_health_score(keywords, gaps, backlinks, interlinking)
    logger.info(f"SEO Health Score: {score}/100")

    # Generate actions by category
    content_items = generate_content_actions(keywords, gaps, pages)
    backlink_items = generate_backlink_actions(backlinks)
    interlink_items = generate_interlinking_actions(interlinking)
    technical_items = generate_technical_actions(keywords, gaps)

    # Build sections
    sections = [
        {
            "title": "Content Strategy",
            "description": "Content gaps and keyword targeting opportunities",
            "items": content_items,
        },
        {
            "title": "Backlink Acquisition",
            "description": "Link building and referring domain gap closure",
            "items": backlink_items,
        },
        {
            "title": "Internal Linking",
            "description": "Site structure and internal link optimization",
            "items": interlink_items,
        },
        {
            "title": "Technical SEO",
            "description": "Technical optimizations for better crawling and indexing",
            "items": technical_items,
        },
    ]

    # Identify quick wins (low effort + high/medium impact)
    all_items = content_items + backlink_items + interlink_items + technical_items
    quick_wins = [
        item for item in all_items
        if item["effort"] == "Low" and item["estimated_impact"] in ("High", "Medium")
    ]

    # Summary
    total_gaps = gaps.get("total_keyword_gaps", 0)
    missing = gaps.get("missing_keywords", 0)
    da30_gap = backlinks.get("da30_plus_domains", 0)

    summary = (
        f"SEO Health Score: {score}/100. "
        f"Found {keywords.get('total', 0)} keywords across {len(keywords.get('groups', {}))} groups. "
        f"Identified {total_gaps} keyword gaps ({missing} completely missing). "
        f"{da30_gap} high-authority (DA 30+) referring domain opportunities. "
        f"{len(interlinking.get('orphan_pages', []))} orphan pages need internal links. "
        f"{len(quick_wins)} quick wins available for immediate impact."
    )

    # ── Output ─────────────────────────────────────────
    output = {
        "summary": summary,
        "score": score,
        "sections": sections,
        "quick_wins": quick_wins,
        "total_actions": len(all_items),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"✅ Action plan complete: {len(all_items)} actions, "
                f"{len(quick_wins)} quick wins → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Action Plan Agent")
    parser.add_argument("--config", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    run(config, args.data_dir, args.output)
