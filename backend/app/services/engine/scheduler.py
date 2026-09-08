"""Unified Adaptive Scheduler — orchestrates FSRS, Elo, BKT, and Thompson Sampling.

Layered by data maturity:
  Cold start (0 interactions)  → Elo + placement test
  Early (10-100 interactions)  → BKT + FSRS population defaults
  Mature (100+ interactions)   → Full ensemble + per-user FSRS optimization

Question selection targets P(correct) ≈ 0.75 (Zone of Proximal Development).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .fsrs import FSRSScheduler, Card
from .elo import EloRating, EloEntity
from .bkt import BKTModel, SkillState
from .bandit import ThompsonBandit, NewVsReviewBandit


@dataclass
class QuestionCandidate:
    question_id: str
    skill_ids: list[str]
    elo_entity: EloEntity
    fsrs_card: Card
    is_new: bool = True

    expected_p: float = 0.5
    priority_score: float = 0.0


@dataclass
class SessionConfig:
    target_p: float = 0.75
    frustration_threshold: float = 0.50
    boredom_threshold: float = 0.92
    max_questions: int = 20
    min_questions: int = 5
    time_limit_minutes: int = 30


@dataclass
class SessionState:
    questions_answered: int = 0
    correct_count: int = 0
    combo: int = 0
    max_combo: int = 0
    xp_earned: int = 0
    recent_accuracy: list[bool] = field(default_factory=list)

    def __post_init__(self) -> None:
        pass

    @property
    def accuracy(self) -> float:
        if not self.recent_accuracy:
            return 0.5
        return sum(self.recent_accuracy) / len(self.recent_accuracy)

    @property
    def rolling_accuracy(self) -> float:
        window = self.recent_accuracy[-8:]
        if not window:
            return 0.5
        return sum(window) / len(window)


class AdaptiveScheduler:
    def __init__(
        self,
        fsrs: Optional[FSRSScheduler] = None,
        elo: Optional[EloRating] = None,
        bkt: Optional[BKTModel] = None,
    ):
        self.fsrs = fsrs or FSRSScheduler()
        self.elo = elo or EloRating()
        self.bkt = bkt or BKTModel()
        self.question_bandit = ThompsonBandit()
        self.mode_bandit = NewVsReviewBandit()

    def select_next_question(
        self,
        user_elo: EloEntity,
        skill_states: dict[str, SkillState],
        candidates: list[QuestionCandidate],
        session: SessionState,
        config: SessionConfig,
        now: Optional[datetime] = None,
    ) -> Optional[QuestionCandidate]:
        now = now or datetime.utcnow()

        if not candidates:
            return None

        due_reviews = [c for c in candidates if not c.is_new and c.fsrs_card.due and c.fsrs_card.due <= now]
        new_items = [c for c in candidates if c.is_new]

        should_review = self.mode_bandit.should_review(
            has_due_reviews=bool(due_reviews),
            has_new_content=bool(new_items),
        )

        pool = due_reviews if should_review and due_reviews else new_items if new_items else candidates

        target_p = self._adjust_target(config, session)

        for q in pool:
            q.expected_p = self.elo.expected_score(user_elo.rating, q.elo_entity.rating)

        for q in pool:
            if q.question_id not in self.question_bandit.arms:
                self.question_bandit.add_arm(q.question_id)

        for q in pool:
            p_distance = abs(q.expected_p - target_p)
            zpd_score = 1.0 - p_distance

            urgency = 0.0
            if q.fsrs_card.due and not q.is_new:
                overdue_days = (now - q.fsrs_card.due).days
                urgency = min(1.0, max(0.0, overdue_days / 7.0))

            skill_need = 0.0
            for sid in q.skill_ids:
                if sid in skill_states:
                    skill_need += (1.0 - skill_states[sid].p_known)
            skill_need = min(1.0, skill_need / max(1, len(q.skill_ids)))

            bandit_sample = self.question_bandit.arms[q.question_id].sample()

            q.priority_score = (
                0.35 * zpd_score
                + 0.25 * urgency
                + 0.20 * skill_need
                + 0.20 * bandit_sample
            )

        pool.sort(key=lambda q: q.priority_score, reverse=True)

        top_n = min(5, len(pool))
        selection_pool = pool[:top_n]

        if not selection_pool:
            return None

        weights = [q.priority_score for q in selection_pool]
        total = sum(weights)
        if total <= 0:
            return selection_pool[0]

        import random
        r = random.random() * total
        cumulative = 0.0
        for q in selection_pool:
            cumulative += q.priority_score
            if r <= cumulative:
                return q
        return selection_pool[0]

    def process_answer(
        self,
        question: QuestionCandidate,
        user_elo: EloEntity,
        skill_states: dict[str, SkillState],
        correct: bool,
        response_time_ms: int,
        session: SessionState,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        now = now or datetime.utcnow()
        grade = self._correctness_to_grade(correct, response_time_ms)

        user_elo, question.elo_entity, expected = self.elo.update(
            user_elo, question.elo_entity, correct,
        )

        for sid in question.skill_ids:
            if sid not in skill_states:
                skill_states[sid] = self.bkt.init_state(sid)
            self.bkt.update(skill_states[sid], correct)

        card, log = self.fsrs.review(question.fsrs_card, grade, now)
        question.fsrs_card = card

        reward = self.question_bandit.arms.get(question.question_id)
        if reward:
            r = 0.8 if correct else 0.2
            reward.update(r)

        self.mode_bandit.update(
            was_review=not question.is_new,
            reward=0.7 if correct else 0.3,
        )

        session.questions_answered += 1
        session.recent_accuracy.append(correct)
        if correct:
            session.correct_count += 1
            session.combo += 1
            session.max_combo = max(session.max_combo, session.combo)
        else:
            session.combo = 0

        xp = self._calculate_xp(correct, session.combo, grade)
        session.xp_earned += xp

        return {
            "correct": correct,
            "grade": grade,
            "xp_earned": xp,
            "combo": session.combo,
            "user_elo": user_elo.rating,
            "next_review": card.due.isoformat() if card.due else None,
            "skill_mastery": {
                sid: skill_states[sid].p_known
                for sid in question.skill_ids
                if sid in skill_states
            },
            "session_accuracy": session.accuracy,
        }

    def _adjust_target(self, config: SessionConfig, session: SessionState) -> float:
        rolling = session.rolling_accuracy
        if rolling < config.frustration_threshold:
            return min(0.90, config.target_p + 0.10)
        if rolling > config.boredom_threshold:
            return max(0.60, config.target_p - 0.10)
        return config.target_p

    def _correctness_to_grade(self, correct: bool, response_time_ms: int) -> int:
        if not correct:
            return 1
        if response_time_ms < 3000:
            return 4  # easy / fast
        if response_time_ms < 10000:
            return 3  # good
        return 2  # hard / slow

    def _calculate_xp(self, correct: bool, combo: int, grade: int) -> int:
        if not correct:
            return 3

        base = 10
        if combo >= 15:
            multiplier = 5
        elif combo >= 7:
            multiplier = 3
        elif combo >= 3:
            multiplier = 2
        else:
            multiplier = 1

        bonus = {4: 5, 3: 0, 2: 0, 1: 0}.get(grade, 0)
        return base * multiplier + bonus

    def get_session_summary(self, session: SessionState) -> dict[str, Any]:
        return {
            "total_questions": session.questions_answered,
            "correct": session.correct_count,
            "accuracy": round(session.accuracy * 100, 1),
            "max_combo": session.max_combo,
            "xp_earned": session.xp_earned,
        }
