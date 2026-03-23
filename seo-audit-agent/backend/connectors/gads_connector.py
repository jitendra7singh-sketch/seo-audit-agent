"""
Google Ads Keyword Planner Connector

Fetches:
- Keyword ideas from seed keywords
- Search volume and forecasts
- Keyword competition data
"""

import os
import logging
from typing import Optional
from google.ads.googleads.client import GoogleAdsClient

logger = logging.getLogger(__name__)


class GoogleAdsConnector:
    """Connector for Google Ads Keyword Planner API."""

    def __init__(
        self,
        developer_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        customer_id: Optional[str] = None,
    ):
        self.developer_token = developer_token or os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
        self.client_id = client_id or os.environ.get("GOOGLE_ADS_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("GOOGLE_ADS_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", "")
        self.customer_id = (customer_id or os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "")).replace("-", "")

        if not all([self.developer_token, self.client_id, self.client_secret,
                     self.refresh_token, self.customer_id]):
            raise ValueError("All Google Ads credentials are required")

        self.client = GoogleAdsClient.load_from_dict({
            "developer_token": self.developer_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "use_proto_plus": True,
        })

    def get_keyword_ideas(
        self,
        seed_keywords: list[str],
        language_id: str = "1000",  # English
        geo_target: str = "2356",  # India
        limit: int = 5000,
    ) -> list[dict]:
        """
        Get keyword ideas from seed keywords using Keyword Planner.

        language_id: 1000=English, 1023=Hindi
        geo_target: 2356=India, 2840=US, 2826=UK
        """
        kp_service = self.client.get_service("KeywordPlanIdeaService")
        request = self.client.get_type("GenerateKeywordIdeasRequest")

        request.customer_id = self.customer_id
        request.language = f"languageConstants/{language_id}"
        request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
        request.include_adult_keywords = False
        request.keyword_plan_network = (
            self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        )

        # Use seed keywords
        request.keyword_seed.keywords.extend(seed_keywords)

        results = []
        response = kp_service.generate_keyword_ideas(request=request)

        for idea in response:
            metrics = idea.keyword_idea_metrics
            competition_map = {0: "UNSPECIFIED", 1: "UNKNOWN", 2: "LOW", 3: "MEDIUM", 4: "HIGH"}
            results.append({
                "keyword": idea.text,
                "volume": metrics.avg_monthly_searches,
                "competition": competition_map.get(metrics.competition, "UNKNOWN"),
                "competition_index": metrics.competition_index,
                "low_bid": metrics.low_top_of_page_bid_micros / 1_000_000 if metrics.low_top_of_page_bid_micros else 0,
                "high_bid": metrics.high_top_of_page_bid_micros / 1_000_000 if metrics.high_top_of_page_bid_micros else 0,
                "monthly_volumes": [
                    {"month": mv.month, "year": mv.year, "volume": mv.monthly_searches}
                    for mv in metrics.monthly_search_volumes
                ],
            })

            if len(results) >= limit:
                break

        return results

    def get_search_volume(
        self, keywords: list[str],
        language_id: str = "1000",
        geo_target: str = "2356",
    ) -> list[dict]:
        """Get exact search volumes for specific keywords."""
        kp_service = self.client.get_service("KeywordPlanIdeaService")
        request = self.client.get_type("GenerateKeywordHistoricalMetricsRequest")

        request.customer_id = self.customer_id
        request.language = f"languageConstants/{language_id}"
        request.geo_target_constants.append(f"geoTargetConstants/{geo_target}")
        request.keywords.extend(keywords[:10000])  # API limit

        results = []
        response = kp_service.generate_keyword_historical_metrics(request=request)

        for result in response.results:
            metrics = result.keyword_metrics
            results.append({
                "keyword": result.text,
                "volume": metrics.avg_monthly_searches,
                "competition": str(metrics.competition),
            })

        return results
