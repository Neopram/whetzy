"""Bayesian Knowledge Tracing (BKT) — HMM-based mastery estimation.

Models four parameters per skill:
  P(L0) — prior probability of knowing the skill
  P(T)  — probability of learning after one opportunity
  P(G)  — probability of guessing correctly without knowing
  P(S)  — probability of slipping (wrong despite knowing)

Updates via the HMM forward algorithm. Mastery probability P(L)
increases toward 1.0 as the student demonstrates knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain_thresholds import MASTERY_THRESHOLD


@dataclass
class SkillParams:
    p_l0: float = 0.1   # prior knowledge
    p_t: float = 0.2    # learn rate
    p_g: float = 0.25   # guess rate
    p_s: float = 0.1    # slip rate

    # Used only by `update_unknown`, when the learner explicitly declares they
    # do not know. That is a different observation from a wrong answer: no
    # guessing took place, so P(G) plays no part in the posterior.
    p_dk_known: float = 0.05    # declares ignorance despite knowing (momentary doubt)
    p_dk_unknown: float = 0.80  # honestly declares ignorance when not knowing


@dataclass
class SkillState:
    skill_id: str
    p_known: float = 0.1
    attempts: int = 0
    correct: int = 0


class BKTModel:
    def __init__(self, default_params: SkillParams | None = None):
        self.default_params = default_params or SkillParams()
        self.skill_params: dict[str, SkillParams] = {}

    def set_params(self, skill_id: str, params: SkillParams) -> None:
        self.skill_params[skill_id] = params

    def get_params(self, skill_id: str) -> SkillParams:
        return self.skill_params.get(skill_id, self.default_params)

    def update(
        self, state: SkillState, correct: bool,
    ) -> SkillState:
        params = self.get_params(state.skill_id)
        p_l = state.p_known

        if correct:
            p_correct_given_known = 1.0 - params.p_s
            p_correct_given_unknown = params.p_g
            numerator = p_l * p_correct_given_known
            denominator = numerator + (1.0 - p_l) * p_correct_given_unknown
        else:
            p_wrong_given_known = params.p_s
            p_wrong_given_unknown = 1.0 - params.p_g
            numerator = p_l * p_wrong_given_known
            denominator = numerator + (1.0 - p_l) * p_wrong_given_unknown

        if denominator > 0:
            p_l_posterior = numerator / denominator
        else:
            p_l_posterior = p_l

        p_l_next = p_l_posterior + (1.0 - p_l_posterior) * params.p_t

        state.p_known = min(1.0, max(0.0, p_l_next))
        state.attempts += 1
        if correct:
            state.correct += 1

        return state

    def update_unknown(self, state: SkillState) -> SkillState:
        """Update mastery from an explicit "I don't know".

        A wrong answer is ambiguous: on a four-option question a quarter of
        lucky guesses look like knowledge, and a wrong one may be a slip by
        someone who does know. An explicit declaration of ignorance carries
        neither confound — nobody guesses their way into saying "I don't know".

        So the posterior uses a separate likelihood pair (`p_dk_known`,
        `p_dk_unknown`) and P(G) drops out entirely. The result is stronger
        negative evidence than a wrong answer: with p_known = 0.5 and the
        defaults, a wrong answer lands at ~0.12 while this lands at ~0.06.

        The learning transition still applies — the learner goes on to read the
        explanation, which is an opportunity to learn like any other. The
        attempt is counted, but never as `correct`.
        """
        params = self.get_params(state.skill_id)
        p_l = state.p_known

        numerator = p_l * params.p_dk_known
        denominator = numerator + (1.0 - p_l) * params.p_dk_unknown

        p_l_posterior = numerator / denominator if denominator > 0 else p_l
        p_l_next = p_l_posterior + (1.0 - p_l_posterior) * params.p_t

        state.p_known = min(1.0, max(0.0, p_l_next))
        state.attempts += 1

        return state

    def is_mastered(self, state: SkillState, threshold: float = MASTERY_THRESHOLD) -> bool:
        return state.p_known >= threshold

    def predict_correct(self, state: SkillState) -> float:
        params = self.get_params(state.skill_id)
        p_l = state.p_known
        return p_l * (1.0 - params.p_s) + (1.0 - p_l) * params.p_g

    def init_state(self, skill_id: str) -> SkillState:
        params = self.get_params(skill_id)
        return SkillState(skill_id=skill_id, p_known=params.p_l0)

    def batch_mastery(
        self, states: list[SkillState], threshold: float = MASTERY_THRESHOLD,
    ) -> dict[str, bool]:
        return {s.skill_id: self.is_mastered(s, threshold) for s in states}

    def overall_mastery(self, states: list[SkillState]) -> float:
        if not states:
            return 0.0
        return sum(s.p_known for s in states) / len(states)
