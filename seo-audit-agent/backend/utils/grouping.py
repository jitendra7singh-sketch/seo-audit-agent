"""
Keyword Grouping & Clustering Utilities

Assigns keywords to semantic groups and intent categories using:
1. Rule-based intent classification
2. TF-IDF + KMeans clustering for topic groups
"""

import re
import logging
from collections import defaultdict
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans

logger = logging.getLogger(__name__)

# ── Intent Classification Rules ────────────────────────

INTENT_PATTERNS = {
    "Transactional": [
        r"\b(buy|book|order|purchase|subscribe|download|get|hire|rent)\b",
        r"\b(price|pricing|cost|cheap|affordable|discount|deal|coupon|offer)\b",
        r"\b(ticket|booking|reservation|checkout)\b",
    ],
    "Navigational": [
        r"\b(login|sign ?in|sign ?up|register|account|dashboard|app)\b",
        r"\b(\.com|\.in|\.org|website|official|homepage)\b",
    ],
    "Commercial Investigation": [
        r"\b(best|top|review|compare|comparison|vs|versus|alternative)\b",
        r"\b(rating|rated|ranked|ranking|list of)\b",
    ],
    "Informational": [
        r"\b(what|how|why|when|where|who|which|can|does|do|is|are)\b",
        r"\b(guide|tutorial|tips|learn|meaning|definition|example)\b",
    ],
}

BRAND_INDICATORS = [
    "makemytrip", "goibibo", "cleartrip", "ixigo", "yatra",
    "easemytrip", "redbus", "abhibus", "irctc", "confirmtkt",
]


def classify_intent(keyword: str) -> str:
    """Classify keyword intent based on pattern matching."""
    kw_lower = keyword.lower()

    # Check each intent category in priority order
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, kw_lower):
                return intent

    return "Informational"  # default


def is_brand_keyword(keyword: str, brand_terms: Optional[list[str]] = None) -> bool:
    """Check if a keyword is a branded term."""
    kw_lower = keyword.lower()
    terms = (brand_terms or []) + BRAND_INDICATORS
    return any(term in kw_lower for term in terms)


def classify_length(keyword: str) -> str:
    """Classify keyword as short-tail or long-tail."""
    word_count = len(keyword.split())
    return "Short-tail" if word_count <= 2 else "Long-tail"


# ── Topic Clustering ───────────────────────────────────

def cluster_keywords(
    keywords: list[str],
    n_clusters: int = 30,
    max_features: int = 5000,
) -> dict[str, int]:
    """
    Cluster keywords into topic groups using TF-IDF + KMeans.
    Returns: {keyword: cluster_id}
    """
    if len(keywords) < n_clusters:
        n_clusters = max(2, len(keywords) // 3)

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 3),
        stop_words="english",
        sublinear_tf=True,
    )

    tfidf_matrix = vectorizer.fit_transform(keywords)

    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        random_state=42,
        batch_size=min(1000, len(keywords)),
        n_init=3,
    )
    labels = kmeans.fit_predict(tfidf_matrix)

    # Generate cluster names from top terms
    feature_names = vectorizer.get_feature_names_out()
    cluster_names = {}
    for i in range(n_clusters):
        center = kmeans.cluster_centers_[i]
        top_indices = center.argsort()[-3:][::-1]
        top_terms = [feature_names[idx] for idx in top_indices]
        cluster_names[i] = " | ".join(top_terms).title()

    return {kw: cluster_names[label] for kw, label in zip(keywords, labels)}


# ── Full Grouping Pipeline ─────────────────────────────

def group_keywords(
    keywords: list[dict],
    brand_terms: Optional[list[str]] = None,
    n_topic_clusters: int = 30,
) -> list[dict]:
    """
    Full keyword grouping pipeline.
    
    Input: list of dicts with at least {"keyword": str, "volume": int}
    Output: same list with added "intent", "group", "is_brand", "length_type"
    """
    # Extract keyword strings for clustering
    kw_strings = [kw["keyword"] for kw in keywords]

    # Topic clustering
    logger.info(f"Clustering {len(kw_strings)} keywords into ~{n_topic_clusters} topics")
    topic_map = cluster_keywords(kw_strings, n_clusters=n_topic_clusters)

    # Classify each keyword
    for kw in keywords:
        text = kw["keyword"]
        kw["intent"] = classify_intent(text)
        kw["is_brand"] = is_brand_keyword(text, brand_terms)
        kw["length_type"] = classify_length(text)
        kw["topic_cluster"] = topic_map.get(text, "Other")

        # Assign primary group
        if kw["is_brand"]:
            kw["group"] = "Brand"
        else:
            kw["group"] = kw["intent"]

    return keywords


def get_group_summary(keywords: list[dict]) -> dict:
    """Get summary counts by group."""
    summary = defaultdict(int)
    for kw in keywords:
        summary[kw.get("group", "Ungrouped")] += 1
    return dict(sorted(summary.items(), key=lambda x: -x[1]))
