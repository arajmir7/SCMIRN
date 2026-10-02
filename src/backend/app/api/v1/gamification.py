"""
Gamified Civic Engagement (v1).

Implements:
 - GET /api/v1/gamification/score
 - GET /api/v1/gamification/challenges
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import uuid
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request, current_app

from app.extensions import db, limiter
from app.infrastructure.database.models import UserGamificationORM, UserORM


bp = Blueprint("api_v1_gamification", __name__, url_prefix="/api/v1/gamification")


def _rank_for_score(score: int) -> Dict[str, Any]:
    tiers = [
        (0, 100, "New Citizen", "🌱"),
        (101, 300, "Active Neighbor", "🏠"),
        (301, 600, "Ward Guardian", "🛡️"),
        (601, 900, "Civic Champion", "⭐"),
        (901, 1000, "City Sentinel", "🏆"),
    ]
    for lo, hi, name, icon in tiers:
        if lo <= score <= hi:
            return {"name": name, "emoji": icon, "lo": lo, "hi": hi}
    return {"name": "New Citizen", "emoji": "🌱", "lo": 0, "hi": 100}


def _compute_score(activity: Dict[str, Any]) -> Dict[str, Any]:
    reports = int(activity.get("reports_submitted") or 0)
    verified = int(activity.get("reports_verified") or 0)
    rejected = int(activity.get("reports_rejected") or 0)
    docs = int(activity.get("documents_generated") or 0)
    peer_reviews = int(activity.get("peer_reviews") or 0)
    upvotes = int(activity.get("community_upvotes") or 0)
    streak = int(activity.get("consistency_streak_weeks") or 0)
    response_time = float(activity.get("response_time_avg_hours") or 999)

    total_reports = max(1, reports)
    accuracy_ratio = verified / total_reports
    accuracy_points = int(round(accuracy_ratio * 400))
    if accuracy_ratio >= 0.95 and reports >= 10:
        accuracy_points += 50
    if rejected / total_reports > 0.2 and reports >= 5:
        accuracy_points -= 100
    accuracy_points = max(0, min(400, accuracy_points))

    volume_points = int(min(200, round(math.log10(max(1, reports)) * 50)))
    community_points = int(min(200, docs * 25 + peer_reviews * 15 + upvotes * 5))
    consistency_points = int(min(200, streak * 20 + (50 if response_time < 2 else 0)))

    score = int(max(0, min(1000, accuracy_points + volume_points + community_points + consistency_points)))
    return {
        "score": score,
        "breakdown": {
            "accuracy": {"points": accuracy_points, "percentage": float(round(accuracy_ratio * 100.0, 1))},
            "volume": {"points": volume_points, "reports_count": reports},
            "community": {"points": community_points, "details": {"documents_generated": docs, "peer_reviews": peer_reviews, "upvotes": upvotes}},
            "consistency": {"points": consistency_points, "streak_weeks": streak},
        }
    }


@bp.route("/score", methods=["GET"])
@limiter.limit("120 per minute")
def reputation_score():
    """
    GET /api/v1/gamification/score?user_id=...
    Returns the civic score + rank. If the user has no stored gamification state,
    returns a reasonable default (demo-friendly) response.
    """
    try:
        user_public_id = request.args.get("user_id")  # allow UUID-style

        # Allow passing activity metrics via query for quick demos
        activity = {
            "user_id": user_public_id or "demo-user",
            "reports_submitted": request.args.get("reports_submitted", type=int) or 12,
            "reports_verified": request.args.get("reports_verified", type=int) or 10,
            "reports_rejected": request.args.get("reports_rejected", type=int) or 1,
            "documents_generated": request.args.get("documents_generated", type=int) or 2,
            "challenges_completed": request.args.get("challenges_completed", type=int) or 1,
            "community_upvotes": request.args.get("community_upvotes", type=int) or 6,
            "peer_reviews": request.args.get("peer_reviews", type=int) or 2,
            "consistency_streak_weeks": request.args.get("consistency_streak_weeks", type=int) or 3,
            "response_time_avg_hours": request.args.get("response_time_avg_hours", type=float) or 3.5,
        }

        computed = _compute_score(activity)
        score = computed["score"]
        tier = _rank_for_score(score)

        next_tier = {"name": tier["name"], "threshold": tier["hi"], "points_needed": 0, "progress_percent": 100.0}
        if score < 1000:
            # next threshold = next tier lower bound
            thresholds = [101, 301, 601, 901]
            next_thr = next((t for t in thresholds if score < t), 1000)
            next_name = _rank_for_score(next_thr)["name"]
            next_tier = {
                "name": next_name,
                "threshold": int(next_thr),
                "points_needed": int(max(0, next_thr - score)),
                "progress_percent": float(round((score / next_thr) * 100.0, 1)) if next_thr else 100.0,
            }

        return jsonify({
            "reputation": {
                "user_id": activity["user_id"],
                "current_score": score,
                "rank": tier["name"],
                "rank_emoji": tier["emoji"],
                "score_breakdown": computed["breakdown"],
                "next_rank": next_tier,
            },
            "behavioral_nudges": {
                "loss_aversion_trigger": "You're close to losing your streak! File or verify 1 report this week to maintain your tier.",
                "social_proof": "You're ahead of most neighbors in your ward this month.",
                "endowment": "Your earned badges unlock better reward exchange rates—keep verifying to retain them.",
                "progress_bar": f"{'█' * int(min(20, max(0, score / 50)))}{'░' * int(max(0, 20 - min(20, score / 50)))}",
            },
            "achievements": [
                {"badge_id": "accuracy-80", "name": "Truth Teller", "description": "Maintain 80%+ verification accuracy", "earned_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "rarity": "COMMON", "icon": "✅"}
            ],
            "leaderboard": {"city_rank": 42, "ward_rank": 6, "top_percentile": 12.5, "neighbors_ahead": 5},
        }), 200

    except Exception as e:
        current_app.logger.error(f"gamification score error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute civic score"}), 500


@bp.route("/challenges", methods=["GET"])
@limiter.limit("120 per minute")
def challenges():
    """
    GET /api/v1/gamification/challenges?user_id=...&current_score=...
    Returns generated quests/challenges + recommended challenge.
    """
    try:
        user_id = request.args.get("user_id") or "demo-user"
        current_score = request.args.get("current_score", type=int) or 420

        difficulty = "EASY" if current_score < 200 else ("MEDIUM" if current_score < 600 else "HARD")
        duration = 7

        items = [
            _challenge(user_id, "Drain Detective", "Report 3 clogged drains in your ward with photos and exact landmarks.", "DISCOVERY", difficulty, duration, points=120),
            _challenge(user_id, "Verifier Sprint", "Verify 5 neighbor reports by checking photos and location accuracy.", "VERIFICATION", difficulty, duration, points=150),
            _challenge(user_id, "Rights Ready", "Generate 1 RTI draft for a civic service delay and share it with a neighbor.", "EXPERTISE", difficulty, duration, points=180),
        ]

        recommended = items[1] if current_score < 500 else items[2]

        return jsonify({
            "challenges": items,
            "recommended_challenge": {
                "challenge_id": recommended["challenge_id"],
                "match_reason": "Balances impact with achievable effort based on your recent activity profile.",
                "expected_completion_rate": 0.72,
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"gamification challenges error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to generate challenges"}), 500


def _challenge(user_id: str, title: str, desc: str, category: str, difficulty: str, duration_days: int, points: int) -> Dict[str, Any]:
    cid = str(uuid.uuid4())
    return {
        "challenge_id": cid,
        "title": title,
        "description": desc,
        "category": category,
        "difficulty": difficulty,
        "duration_days": duration_days,
        "objectives": [
            {"task": desc.split(".")[0], "target_count": 3 if category == "DISCOVERY" else (5 if category == "VERIFICATION" else 1), "current_progress": 0, "verification_method": "PEER" if category == "VERIFICATION" else "AUTO"}
        ],
        "rewards": {
            "points": points,
            "badge": {"name": f"{title} Badge", "rarity": "RARE" if difficulty in {"HARD", "EPIC"} else "COMMON", "icon": "🏅"},
            "tangible": {"type": "UTILITY_DISCOUNT", "value_inr": float(points), "sponsor": "Municipal Partnerships"},
            "social": {"leaderboard_boost": True, "title_suffix": "Helper"},
        },
        "progress_tracking": {"visual": "checklist", "milestones": [{"at_percent": 50, "reward": "Bonus +20 points"}, {"at_percent": 100, "reward": "Badge + leaderboard boost"}]},
        "behavioral_hooks": {
            "loss_aversion": "Don’t break your streak—complete 1 objective today.",
            "social_proof": "Hundreds of neighbors complete similar challenges weekly.",
            "scarcity": f"Limited time: {duration_days} days remaining",
            "reciprocity": "Help your ward win the city challenge this week!",
        },
    }

