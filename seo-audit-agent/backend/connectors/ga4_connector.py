"""
Google Analytics 4 Connector

Fetches:
- Page performance data
- Traffic sources
- User engagement metrics
"""

import os
import json
import logging
from typing import Optional
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange, OrderBy
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


class GA4Connector:
    """Connector for Google Analytics 4 Data API."""

    def __init__(
        self,
        property_id: Optional[str] = None,
        service_account_json: Optional[str] = None,
    ):
        self.property_id = property_id or os.environ.get("GA4_PROPERTY_ID", "")
        raw = service_account_json or os.environ.get("GA4_SERVICE_ACCOUNT_JSON", "")

        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID is required")
        if not raw:
            raise ValueError("GA4_SERVICE_ACCOUNT_JSON is required")

        info = json.loads(raw) if isinstance(raw, str) else raw
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )
        self.client = BetaAnalyticsDataClient(credentials=creds)

    def _run_report(
        self,
        dimensions: list[str],
        metrics: list[str],
        date_range: str = "90daysAgo",
        limit: int = 10000,
        order_by_metric: Optional[str] = None,
    ) -> list[dict]:
        """Run a GA4 report and return parsed rows."""
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=date_range, end_date="today")],
            limit=limit,
        )

        if order_by_metric:
            request.order_bys = [
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_by_metric), desc=True)
            ]

        response = self.client.run_report(request)
        results = []
        for row in response.rows:
            entry = {}
            for i, dim in enumerate(dimensions):
                entry[dim] = row.dimension_values[i].value
            for i, met in enumerate(metrics):
                entry[met] = row.metric_values[i].value
            results.append(entry)

        return results

    def get_top_pages(self, limit: int = 5000) -> list[dict]:
        """Get top landing pages by sessions."""
        return self._run_report(
            dimensions=["pagePath", "pageTitle"],
            metrics=["sessions", "activeUsers", "bounceRate",
                     "averageSessionDuration", "screenPageViews"],
            limit=limit,
            order_by_metric="sessions",
        )

    def get_traffic_sources(self, limit: int = 500) -> list[dict]:
        """Get traffic breakdown by source/medium."""
        return self._run_report(
            dimensions=["sessionSource", "sessionMedium"],
            metrics=["sessions", "activeUsers", "conversions"],
            limit=limit,
            order_by_metric="sessions",
        )

    def get_organic_landing_pages(self, limit: int = 2000) -> list[dict]:
        """Get organic search landing pages."""
        return self._run_report(
            dimensions=["landingPage"],
            metrics=["sessions", "activeUsers", "bounceRate",
                     "averageSessionDuration", "conversions"],
            limit=limit,
            order_by_metric="sessions",
        )
