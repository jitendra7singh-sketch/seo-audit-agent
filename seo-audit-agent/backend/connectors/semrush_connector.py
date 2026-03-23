"""
SEMrush API Connector

Handles all SEMrush API calls:
- Domain overview
- Keyword research
- Competitor discovery
- Backlink analytics
- Organic pages
"""

import os
import time
import logging
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SEMRUSH_BASE = "https://api.semrush.com"


class SEMrushConnector:
    """Connector for SEMrush API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SEMRUSH_API_KEY", "")
        if not self.api_key:
            raise ValueError("SEMRUSH_API_KEY is required")
        self.session = requests.Session()
        self._request_count = 0

    def _throttle(self):
        """Rate limit: max 10 requests per second."""
        self._request_count += 1
        if self._request_count % 10 == 0:
            time.sleep(1)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _get(self, endpoint: str, params: dict) -> str:
        """Make a GET request to SEMrush API."""
        self._throttle()
        params["key"] = self.api_key
        url = f"{SEMRUSH_BASE}/{endpoint}"
        logger.debug(f"SEMrush request: {endpoint} params={list(params.keys())}")
        resp = self.session.get(url, params=params, timeout=60)
        resp.raise_for_status()
        return resp.text

    def _parse_csv(self, raw: str) -> list[dict]:
        """Parse SEMrush semicolon-delimited response."""
        lines = raw.strip().split("\n")
        if len(lines) < 2:
            return []
        headers = lines[0].split(";")
        results = []
        for line in lines[1:]:
            values = line.split(";")
            if len(values) == len(headers):
                results.append(dict(zip(headers, values)))
        return results

    # ── Domain Analytics ───────────────────────────────

    def domain_overview(self, domain: str, database: str = "in") -> dict:
        """Get domain overview metrics."""
        raw = self._get("", {
            "type": "domain_ranks",
            "domain": domain,
            "database": database,
            "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At,Ac",
        })
        rows = self._parse_csv(raw)
        return rows[0] if rows else {}

    def domain_organic_keywords(
        self, domain: str, database: str = "in",
        limit: int = 5000, offset: int = 0
    ) -> list[dict]:
        """Get organic keywords for a domain."""
        raw = self._get("", {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "display_offset": offset,
            "export_columns": "Ph,Po,Nq,Cp,Co,Tr,Tc,Nr,Td,Kd,Ur",
            "display_sort": "tr_desc",
        })
        return self._parse_csv(raw)

    def domain_competitors(
        self, domain: str, database: str = "in", limit: int = 20
    ) -> list[dict]:
        """Get organic competitors for a domain."""
        raw = self._get("", {
            "type": "domain_organic_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "export_columns": "Dn,Cr,Np,Or,Ot,Oc,Ad",
            "display_sort": "cr_desc",
        })
        return self._parse_csv(raw)

    # ── Keyword Analytics ──────────────────────────────

    def keyword_overview(
        self, keywords: list[str], database: str = "in"
    ) -> list[dict]:
        """Get keyword metrics for a batch of keywords."""
        # SEMrush allows batch of up to 100 keywords
        all_results = []
        for i in range(0, len(keywords), 100):
            batch = keywords[i : i + 100]
            raw = self._get("", {
                "type": "phrase_all",
                "phrase": ";".join(batch),
                "database": database,
                "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Kd,In",
            })
            all_results.extend(self._parse_csv(raw))
        return all_results

    def keyword_related(
        self, keyword: str, database: str = "in", limit: int = 100
    ) -> list[dict]:
        """Get related keywords."""
        raw = self._get("", {
            "type": "phrase_related",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Kd",
            "display_sort": "nq_desc",
        })
        return self._parse_csv(raw)

    def keyword_questions(
        self, keyword: str, database: str = "in", limit: int = 50
    ) -> list[dict]:
        """Get question-based keywords."""
        raw = self._get("", {
            "type": "phrase_questions",
            "phrase": keyword,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td,Kd",
        })
        return self._parse_csv(raw)

    # ── Backlink Analytics ─────────────────────────────

    def backlinks_overview(self, domain: str) -> dict:
        """Get backlink overview for a domain."""
        raw = self._get("analytics/v1/", {
            "target": domain,
            "target_type": "root_domain",
            "type": "backlinks_overview",
            "export_columns": "ascore,total,domains_num,urls_num,ips_num,"
                            "follows_num,nofollows_num,texts_num,images_num,"
                            "forms_num,frames_num",
        })
        rows = self._parse_csv(raw)
        return rows[0] if rows else {}

    def backlinks_referring_domains(
        self, domain: str, limit: int = 500
    ) -> list[dict]:
        """Get referring domains for a domain."""
        raw = self._get("analytics/v1/", {
            "target": domain,
            "target_type": "root_domain",
            "type": "backlinks_refdomains",
            "display_limit": limit,
            "export_columns": "domain_ascore,domain,backlinks_num,"
                            "ip,country,first_seen,last_seen",
            "display_sort": "domain_ascore_desc",
        })
        return self._parse_csv(raw)

    # ── URL Analytics ──────────────────────────────────

    def url_organic_keywords(
        self, url: str, database: str = "in", limit: int = 100
    ) -> list[dict]:
        """Get organic keywords for a specific URL."""
        raw = self._get("", {
            "type": "url_organic",
            "url": url,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ph,Po,Nq,Cp,Co,Tr,Tc,Nr,Td",
            "display_sort": "tr_desc",
        })
        return self._parse_csv(raw)

    def domain_pages(
        self, domain: str, database: str = "in", limit: int = 2000
    ) -> list[dict]:
        """Get top organic pages for a domain."""
        raw = self._get("", {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
            "export_columns": "Ur,Ph,Po,Nq,Cp,Tr",
            "display_sort": "tr_desc",
        })
        # Aggregate by URL
        url_map: dict[str, dict] = {}
        for row in self._parse_csv(raw):
            url = row.get("Ur", "")
            if url not in url_map:
                url_map[url] = {
                    "url": url,
                    "traffic": 0,
                    "keywords": 0,
                    "top_keyword": row.get("Ph", ""),
                    "top_position": int(row.get("Po", 0)),
                }
            url_map[url]["traffic"] += int(float(row.get("Tr", 0)))
            url_map[url]["keywords"] += 1
        return sorted(url_map.values(), key=lambda x: x["traffic"], reverse=True)[:limit]
