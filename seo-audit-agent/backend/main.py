"""
SEO Audit Orchestrator

Runs all agents in sequence. Used for local development/testing.
In production (GitHub Actions), each agent runs as a separate job.
"""

import argparse
import json
import logging
import os
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(description="SEO Audit Orchestrator")
    parser.add_argument("--config", required=True, help="Path to audit-config.json")
    parser.add_argument("--output-dir", default="audit-data", help="Output directory")
    parser.add_argument("--agents", default="all",
                        help="Comma-separated list of agents to run, or 'all'")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    out = args.output_dir
    os.makedirs(out, exist_ok=True)

    agents_to_run = (
        ["keywords", "competitors", "pages", "gaps", "backlinks", "interlinks", "actionplan"]
        if args.agents == "all"
        else [a.strip() for a in args.agents.split(",")]
    )

    logger.info(f"Running agents: {agents_to_run}")
    logger.info(f"Config: {config.get('website_url')} / {config.get('category')}")

    if "keywords" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 1: Keyword Research")
        logger.info("=" * 60)
        from backend.agents.keyword_agent import run as run_keywords
        run_keywords(config, f"{out}/keywords.json")

    if "competitors" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 2: Competitor Discovery")
        logger.info("=" * 60)
        from backend.agents.competitor_agent import run as run_competitors
        run_competitors(config, f"{out}/keywords.json", f"{out}/competitors.json")

    if "pages" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 3: Top Pages Analysis")
        logger.info("=" * 60)
        from backend.agents.pages_agent import run as run_pages
        run_pages(config, f"{out}/competitors.json", f"{out}/top-pages.json")

    if "gaps" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 4: Gap Analysis")
        logger.info("=" * 60)
        from backend.agents.gap_agent import run as run_gaps
        run_gaps(config, f"{out}/keywords.json", f"{out}/competitors.json",
                 f"{out}/top-pages.json", f"{out}/gap-analysis.json")

    if "backlinks" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 5: Backlink Gap Analysis")
        logger.info("=" * 60)
        from backend.agents.backlink_agent import run as run_backlinks
        run_backlinks(config, f"{out}/competitors.json", f"{out}/backlinks.json")

    if "interlinks" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 6: Interlinking Analysis")
        logger.info("=" * 60)
        from backend.agents.interlink_agent import run as run_interlinks
        run_interlinks(config, f"{out}/keywords.json", f"{out}/interlinking.json")

    if "actionplan" in agents_to_run:
        logger.info("=" * 60)
        logger.info("STAGE 7: Action Plan")
        logger.info("=" * 60)
        from backend.agents.action_plan_agent import run as run_actionplan
        run_actionplan(config, out, f"{out}/action-plan.json")

    logger.info("=" * 60)
    logger.info("✅ ALL STAGES COMPLETE")
    logger.info(f"Output directory: {out}/")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
