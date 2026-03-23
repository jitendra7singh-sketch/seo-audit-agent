"""
Pydantic models for all data flowing through the SEO audit pipeline.
Every agent outputs JSON conforming to these schemas.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Enums ──────────────────────────────────────────────

class KeywordIntent(str, Enum):
    TRANSACTIONAL = "Transactional"
    INFORMATIONAL = "Informational"
    NAVIGATIONAL = "Navigational"
    COMMERCIAL = "Commercial Investigation"


class KeywordGroup(str, Enum):
    BRAND = "Brand"
    NON_BRAND = "Non-Brand"
    LONG_TAIL = "Long-tail"
    SHORT_TAIL = "Short-tail"
    TRANSACTIONAL = "Transactional"
    INFORMATIONAL = "Informational"
    NAVIGATIONAL = "Navigational"
    COMMERCIAL = "Commercial Investigation"


class Opportunity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class PageType(str, Enum):
    HOMEPAGE = "Homepage"
    CATEGORY = "Category/Hub"
    PRODUCT = "Product/Service"
    BLOG = "Blog/Article"
    LANDING = "Landing Page"
    COMPARISON = "Comparison"
    HOWTO = "How-to/Guide"
    FAQ = "FAQ"
    TOOL = "Tool/Calculator"
    LOCATION = "Location"
    REVIEW = "Review"
    GLOSSARY = "Glossary"


# ── Keyword Models ─────────────────────────────────────

class Keyword(BaseModel):
    keyword: str
    volume: int = 0
    difficulty: int = 0
    cpc: float = 0.0
    intent: KeywordIntent = KeywordIntent.INFORMATIONAL
    group: str = "Ungrouped"
    trend: list[int] = Field(default_factory=lambda: [0] * 12)
    source: str = "semrush"  # semrush | gsc | gads
    position: Optional[int] = None  # current ranking position
    url: Optional[str] = None  # ranking URL


class KeywordResearchOutput(BaseModel):
    total: int
    groups: dict[str, int]
    keywords: list[Keyword]
    generated_at: str


# ── Competitor Models ──────────────────────────────────

class Competitor(BaseModel):
    domain: str
    da: int = 0
    estimated_traffic: str = "0"
    total_keywords: int = 0
    overlap_pct: float = 0.0
    verified: bool = False
    selected: bool = False
    source: str = "semrush"


class CompetitorOutput(BaseModel):
    total: int
    competitors: list[Competitor]
    generated_at: str


# ── Top Pages Models ───────────────────────────────────

class TopPage(BaseModel):
    url: str
    competitor: str
    estimated_traffic: int = 0
    keyword_count: int = 0
    page_type: PageType = PageType.BLOG
    keyword_group: str = "Ungrouped"
    top_keyword: str = ""


class TopPagesOutput(BaseModel):
    total: int
    pages: list[TopPage]
    page_type_distribution: dict[str, int]
    generated_at: str


# ── Gap Analysis Models ────────────────────────────────

class GapItem(BaseModel):
    term: str  # keyword or URL path
    your_position: Optional[int] = None
    competitor_positions: dict[str, Optional[int]]  # domain -> position
    volume: int = 0
    difficulty: int = 0
    opportunity: Opportunity = Opportunity.MEDIUM


class GapAnalysisOutput(BaseModel):
    keyword_gaps: list[GapItem]
    content_gaps: list[GapItem]
    total_keyword_gaps: int
    total_content_gaps: int
    missing_keywords: int  # keywords where you have no position
    generated_at: str


# ── Backlink Models ────────────────────────────────────

class ReferringDomain(BaseModel):
    domain: str
    da: int = 0
    your_site: bool = False
    competitor_presence: dict[str, bool]  # domain -> has_backlink
    domain_type: str = "Blog"  # Blog, News, Directory, Forum, Edu, Gov
    is_da30_plus: bool = False


class BacklinkOutput(BaseModel):
    total_referring_domains: int
    da30_plus_domains: int
    referring_domain_gap: list[ReferringDomain]
    backlink_gap_summary: dict[str, int]  # competitor -> count they have that you don't
    generated_at: str


# ── Interlinking Models ────────────────────────────────

class InterlinkSuggestion(BaseModel):
    source_url: str
    target_url: str
    anchor_text: str
    keyword_group: str
    priority: Priority = Priority.MEDIUM
    reason: str = ""


class InterlinkOutput(BaseModel):
    total_suggestions: int
    orphan_pages: list[str]
    hub_pages: list[str]
    suggestions: list[InterlinkSuggestion]
    generated_at: str


# ── Action Plan Models ─────────────────────────────────

class ActionItem(BaseModel):
    title: str
    description: str
    priority: Priority
    category: str  # "Content", "Technical", "Backlinks", "Interlinking"
    estimated_impact: str = "Medium"
    effort: str = "Medium"  # Low, Medium, High
    timeline: str = ""  # "Week 1-2", "Month 1", etc.


class ActionPlanSection(BaseModel):
    title: str
    description: str
    items: list[ActionItem]


class ActionPlanOutput(BaseModel):
    summary: str
    score: int  # overall SEO health score 0-100
    sections: list[ActionPlanSection]
    quick_wins: list[ActionItem]
    generated_at: str
