"""
Google Search Console Connector

Fetches:
- Search performance data (queries, pages, devices, countries)
- URL inspection
- Sitemaps
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


class GSCConnector:
    """Connector for Google Search Console API."""

    def __init__(self, service_account_json: Optional[str] = None):
        raw = service_account_json or os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "")
        if not raw:
            raise ValueError("GSC_SERVICE_ACCOUNT_JSON is required")

        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        self.service = build("searchconsole", "v1", credentials=creds)

    def get_search_analytics(
        self,
        site_url: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: list[str] = None,
        row_limit: int = 5000,
        start_row: int = 0,
    ) -> list[dict]:
        """
        Query Search Analytics API.
        
        dimensions: list of 'query', 'page', 'device', 'country', 'date'
        """
        if dimensions is None:
            dimensions = ["query"]

        if not end_date:
            end_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=93)).strftime("%Y-%m-%d")

        all_rows = []
        current_start = start_row

        while True:
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions,
                "rowLimit": min(row_limit - len(all_rows), 25000),
                "startRow": current_start,
            }

            response = (
                self.service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )

            rows = response.get("rows", [])
            if not rows:
                break

            for row in rows:
                entry = {
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": round(row["ctr"], 4),
                    "position": round(row["position"], 1),
                }
                for i, dim in enumerate(dimensions):
                    entry[dim] = row["keys"][i]
                all_rows.append(entry)

            current_start += len(rows)

            if len(all_rows) >= row_limit or len(rows) < 25000:
                break

        return all_rows

    def get_queries(self, site_url: str, limit: int = 5000) -> list[dict]:
        """Get top queries with clicks, impressions, CTR, position."""
        return self.get_search_analytics(
            site_url, dimensions=["query"], row_limit=limit
        )

    def get_pages(self, site_url: str, limit: int = 5000) -> list[dict]:
        """Get top pages with performance data."""
        return self.get_search_analytics(
            site_url, dimensions=["page"], row_limit=limit
        )

    def get_query_page_matrix(self, site_url: str, limit: int = 10000) -> list[dict]:
        """Get query + page combinations for interlinking analysis."""
        return self.get_search_analytics(
            site_url, dimensions=["query", "page"], row_limit=limit
        )

    def get_sitemaps(self, site_url: str) -> list[dict]:
        """List sitemaps submitted to GSC."""
        response = self.service.sitemaps().list(siteUrl=site_url).execute()
        return response.get("sitemap", [])
