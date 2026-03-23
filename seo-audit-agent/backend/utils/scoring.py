"""
Opportunity Scoring

Calculates priority scores for keywords, content gaps, and backlink opportunities.
"""

import logging

logger = logging.getLogger(__name__)


def keyword_opportunity_score(
    volume: int,
    difficulty: int,
    current_position: int | None = None,
    cpc: float = 0.0,
) -> tuple[float, str]:
    """
    Score a keyword opportunity from 0-100.
    Returns (score, label) where label is High/Medium/Low.
    """
    # Volume score (0-30)
    if volume > 10000:
        vol_score = 30
    elif volume > 5000:
        vol_score = 25
    elif volume > 1000:
        vol_score = 20
    elif volume > 500:
        vol_score = 15
    elif volume > 100:
        vol_score = 10
    else:
        vol_score = 5

    # Difficulty score (0-30, lower is better)
    diff_score = max(0, 30 - (difficulty * 0.3))

    # Position score (0-25)
    if current_position is None:
        pos_score = 20  # Not ranking = opportunity
    elif current_position <= 3:
        pos_score = 5  # Already ranking well
    elif current_position <= 10:
        pos_score = 15  # Quick win: push to top 3
    elif current_position <= 20:
        pos_score = 25  # Good opportunity: push to page 1
    elif current_position <= 50:
        pos_score = 20
    else:
        pos_score = 10

    # CPC bonus (0-15)
    cpc_score = min(15, cpc * 3)

    total = vol_score + diff_score + pos_score + cpc_score

    if total >= 65:
        label = "High"
    elif total >= 40:
        label = "Medium"
    else:
        label = "Low"

    return round(total, 1), label


def gap_opportunity_score(
    volume: int,
    difficulty: int,
    your_position: int | None,
    best_competitor_position: int,
) -> tuple[float, str]:
    """Score a gap opportunity."""
    base_score, _ = keyword_opportunity_score(volume, difficulty, your_position)

    # Bonus if competitor ranks well (proves the keyword is achievable)
    if best_competitor_position <= 3:
        comp_bonus = 15
    elif best_competitor_position <= 10:
        comp_bonus = 10
    else:
        comp_bonus = 5

    # Penalty if you already rank (less of a gap)
    if your_position and your_position <= 10:
        gap_penalty = 20
    elif your_position and your_position <= 20:
        gap_penalty = 10
    else:
        gap_penalty = 0

    total = min(100, base_score + comp_bonus - gap_penalty)

    if total >= 65:
        label = "High"
    elif total >= 40:
        label = "Medium"
    else:
        label = "Low"

    return round(total, 1), label


def backlink_opportunity_score(
    da: int,
    competitor_count: int,
    total_competitors: int,
) -> tuple[float, str]:
    """Score a backlink opportunity."""
    # DA score (0-40)
    da_score = min(40, da * 0.5)

    # Competitor prevalence (0-40) - more competitors have it = more important
    prevalence = competitor_count / max(1, total_competitors)
    prev_score = prevalence * 40

    # DA 30+ bonus (0-20)
    da_bonus = 20 if da >= 30 else (10 if da >= 20 else 0)

    total = da_score + prev_score + da_bonus

    if total >= 65:
        label = "High"
    elif total >= 40:
        label = "Medium"
    else:
        label = "Low"

    return round(total, 1), label
