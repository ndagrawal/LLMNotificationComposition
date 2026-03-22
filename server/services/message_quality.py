"""
message_quality.py — Six-Dimension Message Quality Evaluator.

Implements the Message Quality Framework introduced in v3 of the paper:
  "LLM-Based Intelligent Notification Message Composition" (Agrawal, 2026).

The six dimensions are:
  1. Contextual Relevance   — Does the message integrate available context signals?
  2. Clarity                — Is the message concise and unambiguous?
  3. Actionability          — Does the message motivate a clear, specific action?
  4. Novelty Handling       — Does the message bridge from known to adjacent content?
  5. Linguistic Freshness   — Does the message avoid repetitive slot-fill phrasing?
  6. Persuasive Appropriateness — Is persuasive framing present but not manipulative?

Each dimension is scored 0.0–1.0. The composite quality score is a weighted sum.
The evaluator also implements the three-criterion binding-constraint check that
determines whether LLM generation is the appropriate composition path.

Reference: Section 2 (Message Quality Framework) and Section 12
           (Binding-Constraint Framework) of the v3 paper.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from models.schemas import ComposeRequest, NotificationDomain, NotificationIntent


# ── Quality Dimension Weights ──────────────────────────────────────────────────
# Weights reflect the relative importance of each dimension as argued in the paper.
DIMENSION_WEIGHTS: dict[str, float] = {
    "contextual_relevance":       0.25,
    "clarity":                    0.20,
    "actionability":              0.20,
    "novelty_handling":           0.10,
    "linguistic_freshness":       0.15,
    "persuasive_appropriateness": 0.10,
}

assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class QualityScore:
    """Per-dimension and composite quality scores for a single candidate message."""
    contextual_relevance: float = 0.0
    clarity: float = 0.0
    actionability: float = 0.0
    novelty_handling: float = 0.0
    linguistic_freshness: float = 0.0
    persuasive_appropriateness: float = 0.0
    composite: float = 0.0
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "contextual_relevance": round(self.contextual_relevance, 3),
            "clarity": round(self.clarity, 3),
            "actionability": round(self.actionability, 3),
            "novelty_handling": round(self.novelty_handling, 3),
            "linguistic_freshness": round(self.linguistic_freshness, 3),
            "persuasive_appropriateness": round(self.persuasive_appropriateness, 3),
            "composite": round(self.composite, 3),
            "flags": self.flags,
        }


@dataclass
class BindingConstraintResult:
    """
    Result of the three-criterion binding-constraint check.

    All three criteria must be True for LLM generation to be the
    appropriate composition path (Section 12 of the v3 paper).
    """
    framing_variance: bool
    linguistic_sensitivity: bool
    context_richness: bool
    use_llm: bool
    reason: str

    @property
    def criteria_met(self) -> int:
        return sum([self.framing_variance, self.linguistic_sensitivity, self.context_richness])


# ── Heuristic Signals ─────────────────────────────────────────────────────────

# Action verbs that signal strong actionability
ACTION_VERBS = {
    "check", "see", "get", "try", "discover", "explore", "order", "buy",
    "open", "view", "claim", "grab", "start", "join", "read", "watch",
    "tap", "find", "browse", "shop", "save", "unlock",
}

# Slot-fill patterns that indicate low linguistic freshness
SLOT_FILL_PATTERNS = [
    r"hello\s+\[",
    r"hi\s+\[",
    r"dear\s+\[",
    r"\[user\]",
    r"\[name\]",
    r"\[item\]",
    r"your\s+\[",
    r"check\s+out\s+\w+\s*$",   # "Check out [item]" with nothing else
    r"^\w+\s+is\s+available\s+now\s*[.!]?\s*$",  # "X is available now."
]

# Manipulative / dark-pattern phrases (reduce persuasive_appropriateness)
DARK_PATTERNS = [
    r"\byou\s+will\s+lose\b",
    r"\bact\s+now\s+or\b",
    r"\blast\s+chance\b",
    r"\bonly\s+\d+\s+left\b",
    r"\bexpires?\s+in\s+\d+\s+minutes?\b",
    r"\byou\s+must\s+act\b",
    r"\bdo\s+not\s+miss\s+out\b",
]

# Persuasion signals that are appropriate (increase persuasive_appropriateness)
POSITIVE_PERSUASION = [
    r"\bbecause\b",
    r"\bsince\b",
    r"\bremember\b",
    r"\byou\s+loved\b",
    r"\bbased\s+on\b",
    r"\bperfect\s+for\b",
    r"\bjust\s+for\s+you\b",
    r"\byou\s+might\s+love\b",
]

# Intents where linguistic sensitivity is inherently high
HIGH_LINGUISTIC_SENSITIVITY_INTENTS = {
    NotificationIntent.re_engagement,
    NotificationIntent.recommendation,
    NotificationIntent.new_content,
    NotificationIntent.social_activity,
    NotificationIntent.abandoned_cart,
}

# Intents where framing variance is inherently high
HIGH_FRAMING_VARIANCE_INTENTS = {
    NotificationIntent.re_engagement,
    NotificationIntent.recommendation,
    NotificationIntent.new_content,
    NotificationIntent.social_activity,
    NotificationIntent.abandoned_cart,
    NotificationIntent.promotional_offer,
}

# Intents where framing variance is low (transactional / time-critical)
LOW_FRAMING_VARIANCE_INTENTS = {
    NotificationIntent.order_update,
    NotificationIntent.flash_sale,  # content is structurally determined
}


# ── Main Evaluator ─────────────────────────────────────────────────────────────

class MessageQualityEvaluator:
    """
    Heuristic implementation of the six-dimension message quality framework.

    In production, this would be backed by an LLM judge or a fine-tuned
    reward model trained on human preference data. The heuristic version
    here is intended for development, testing, and low-latency paths.
    """

    def evaluate(
        self,
        title: str,
        body: str,
        request: ComposeRequest,
        context_keys: Optional[list[str]] = None,
    ) -> QualityScore:
        """
        Evaluate a single candidate message across all six dimensions.

        Args:
            title: The notification title.
            body: The notification body.
            request: The original ComposeRequest (for context signals).
            context_keys: Keys retrieved during RAG context assembly.

        Returns:
            A QualityScore with per-dimension and composite scores.
        """
        score = QualityScore()
        full_text = f"{title} {body}".lower()
        context_keys = context_keys or []

        # ── 1. Contextual Relevance ────────────────────────────────────────────
        score.contextual_relevance = self._score_contextual_relevance(
            title, body, full_text, request, context_keys
        )

        # ── 2. Clarity ─────────────────────────────────────────────────────────
        score.clarity = self._score_clarity(title, body, full_text)

        # ── 3. Actionability ───────────────────────────────────────────────────
        score.actionability = self._score_actionability(title, body, full_text)

        # ── 4. Novelty Handling ────────────────────────────────────────────────
        score.novelty_handling = self._score_novelty_handling(title, body, full_text, request)

        # ── 5. Linguistic Freshness ────────────────────────────────────────────
        score.linguistic_freshness = self._score_linguistic_freshness(title, body, full_text)

        # ── 6. Persuasive Appropriateness ──────────────────────────────────────
        score.persuasive_appropriateness, flags = self._score_persuasive_appropriateness(full_text)
        score.flags = flags

        # ── Composite Score ────────────────────────────────────────────────────
        score.composite = round(
            DIMENSION_WEIGHTS["contextual_relevance"] * score.contextual_relevance
            + DIMENSION_WEIGHTS["clarity"] * score.clarity
            + DIMENSION_WEIGHTS["actionability"] * score.actionability
            + DIMENSION_WEIGHTS["novelty_handling"] * score.novelty_handling
            + DIMENSION_WEIGHTS["linguistic_freshness"] * score.linguistic_freshness
            + DIMENSION_WEIGHTS["persuasive_appropriateness"] * score.persuasive_appropriateness,
            3,
        )

        return score

    # ── Dimension Scorers ──────────────────────────────────────────────────────

    def _score_contextual_relevance(
        self,
        title: str,
        body: str,
        full_text: str,
        request: ComposeRequest,
        context_keys: list[str],
    ) -> float:
        """
        Measures how well the message integrates available context signals.
        Checks for: item name, category, weather, time-of-day, user affinity cues.
        """
        score = 0.4  # base
        item_words = set(request.content_item.title.lower().split())

        # Item name present in title (strong relevance signal)
        title_words = set(title.lower().split())
        if title_words & item_words:
            score += 0.25

        # Item name or category present in body
        body_lower = body.lower()
        if any(w in body_lower for w in item_words):
            score += 0.10

        # Context keys referenced (weather, time, affinity)
        context_signals_used = sum(
            1 for k in context_keys
            if any(sig in k for sig in ["weather", "time", "affinity", "preference"])
        )
        score += min(0.15, context_signals_used * 0.05)

        # Attributes referenced
        attrs = request.content_item.attributes
        if attrs:
            attr_vals = " ".join(str(v).lower() for v in attrs.values())
            attr_words = set(attr_vals.split())
            if attr_words & set(full_text.split()):
                score += 0.10

        return round(min(1.0, score), 3)

    def _score_clarity(self, title: str, body: str, full_text: str) -> float:
        """
        Measures conciseness and unambiguity.
        Optimal: title 25–50 chars, body 60–120 chars, no excessive punctuation.
        """
        score = 0.5

        # Title length
        tl = len(title)
        if 25 <= tl <= 50:
            score += 0.20
        elif 15 <= tl < 25 or 50 < tl <= 65:
            score += 0.10
        elif tl < 10 or tl > 80:
            score -= 0.15

        # Body length
        bl = len(body)
        if 60 <= bl <= 120:
            score += 0.15
        elif 40 <= bl < 60 or 120 < bl <= 160:
            score += 0.05
        elif bl < 20 or bl > 200:
            score -= 0.10

        # Excessive punctuation
        if title.count("!") > 1 or body.count("!") > 2:
            score -= 0.10
        if title.count("?") > 1:
            score -= 0.05

        # ALL CAPS words (shouting)
        if re.search(r"\b[A-Z]{4,}\b", title):
            score -= 0.10

        # Ellipsis overuse
        if full_text.count("...") > 1:
            score -= 0.05

        return round(max(0.0, min(1.0, score)), 3)

    def _score_actionability(self, title: str, body: str, full_text: str) -> float:
        """
        Measures whether the message motivates a clear, specific action.
        Checks for action verbs and specificity of the call-to-action.
        """
        score = 0.4
        words = set(full_text.split())

        # Action verbs present
        action_count = len(words & ACTION_VERBS)
        score += min(0.30, action_count * 0.10)

        # Action verb in title (stronger signal — title is the hook)
        title_words = set(title.lower().split())
        if title_words & ACTION_VERBS:
            score += 0.15

        # Specific benefit or value proposition
        if any(w in full_text for w in ["save", "free", "off", "deal", "offer", "exclusive"]):
            score += 0.05

        # Vague CTA penalty
        if re.search(r"\bclick\s+here\b|\btap\s+here\b|\blearn\s+more\b", full_text):
            score -= 0.10

        return round(max(0.0, min(1.0, score)), 3)

    def _score_novelty_handling(
        self,
        title: str,
        body: str,
        full_text: str,
        request: ComposeRequest,
    ) -> float:
        """
        Measures whether the message bridges from known to adjacent content.
        Relevant for recommendation and new_content intents.
        """
        score = 0.5

        # For intents where novelty is not a concern, return neutral
        if request.intent not in {NotificationIntent.recommendation, NotificationIntent.new_content}:
            return score

        # Bridging language ("because you liked", "similar to", "you might love")
        bridging_patterns = [
            r"because\s+you",
            r"similar\s+to",
            r"you\s+(might|may|will)\s+love",
            r"based\s+on\s+your",
            r"you\s+loved",
            r"fans\s+of",
            r"if\s+you\s+like",
        ]
        for pattern in bridging_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                score += 0.20
                break

        # Category reference (anchors the recommendation in known territory)
        category = request.content_item.category.lower()
        if category in full_text:
            score += 0.10

        # Penalise if the message reads as a cold recommendation with no bridge
        if not any(re.search(p, full_text, re.IGNORECASE) for p in bridging_patterns):
            score -= 0.10

        return round(max(0.0, min(1.0, score)), 3)

    def _score_linguistic_freshness(
        self, title: str, body: str, full_text: str
    ) -> float:
        """
        Measures whether the message avoids repetitive slot-fill phrasing.
        Penalises template-like constructions.
        """
        score = 0.7  # start optimistic — LLM output is usually fresh

        # Slot-fill pattern detection
        for pattern in SLOT_FILL_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                score -= 0.20
                break

        # Generic opener penalty
        generic_openers = [
            r"^check\s+out\b",
            r"^don'?t\s+miss\b",
            r"^hello\b",
            r"^hi\b",
            r"^dear\b",
        ]
        for pattern in generic_openers:
            if re.search(pattern, title.lower()):
                score -= 0.15
                break

        # Repetition between title and body
        title_words = set(title.lower().split()) - {"the", "a", "an", "is", "are", "your"}
        body_words = set(body.lower().split()) - {"the", "a", "an", "is", "are", "your"}
        overlap_ratio = len(title_words & body_words) / max(len(title_words), 1)
        if overlap_ratio > 0.6:
            score -= 0.10

        return round(max(0.0, min(1.0, score)), 3)

    def _score_persuasive_appropriateness(
        self, full_text: str
    ) -> tuple[float, list[str]]:
        """
        Measures whether persuasive framing is present but not manipulative.
        Returns (score, flags_list).
        """
        score = 0.6
        flags: list[str] = []

        # Dark pattern detection (strong penalty)
        for pattern, *_ in [
            (r"\byou\s+will\s+lose\b", "loss_aversion"),
            (r"\bact\s+now\s+or\b", "coercive_urgency"),
            (r"\blast\s+chance\b", "false_urgency"),
            (r"\bonly\s+\d+\s+left\b", "false_scarcity"),
            (r"\bexpires?\s+in\s+\d+\s+minutes?\b", "false_timer"),
            (r"\byou\s+must\s+act\b", "coercive_language"),
        ]:
            if re.search(pattern, full_text, re.IGNORECASE):
                score -= 0.25
                flags.append(pattern)

        # Positive persuasion signals (mild boost)
        for pattern in POSITIVE_PERSUASION:
            if re.search(pattern, full_text, re.IGNORECASE):
                score += 0.08
                break  # only count once

        return round(max(0.0, min(1.0, score)), 3), flags


# ── Binding-Constraint Checker ─────────────────────────────────────────────────

def check_binding_constraint(
    request: ComposeRequest,
    context_keys: Optional[list[str]] = None,
) -> BindingConstraintResult:
    """
    Implements the three-criterion binding-constraint framework from Section 12
    of the v3 paper.

    All three criteria must be satisfied for LLM generation to be appropriate:
      1. Framing Variance:       Content admits multiple meaningful framings.
      2. Linguistic Sensitivity: User response is sensitive to HOW it is framed.
      3. Context Richness:       Sufficient grounded context for non-trivial composition.

    Args:
        request: The ComposeRequest.
        context_keys: Keys retrieved during RAG context assembly.

    Returns:
        BindingConstraintResult with per-criterion flags and a use_llm recommendation.
    """
    context_keys = context_keys or []

    # ── Criterion 1: Framing Variance ──────────────────────────────────────────
    framing_variance = request.intent not in LOW_FRAMING_VARIANCE_INTENTS
    # Order updates and pure flash-sale alerts are structurally determined.

    # ── Criterion 2: Linguistic Sensitivity ───────────────────────────────────
    linguistic_sensitivity = request.intent in HIGH_LINGUISTIC_SENSITIVITY_INTENTS
    # Re-engagement, recommendation, and discovery contexts are linguistically sensitive.

    # ── Criterion 3: Context Richness ─────────────────────────────────────────
    # Require at least 3 context signals to justify non-trivial composition.
    meaningful_keys = [
        k for k in context_keys
        if any(sig in k for sig in ["preference", "affinity", "weather", "time", "open_rate"])
    ]
    context_richness = len(meaningful_keys) >= 2 or bool(request.content_item.attributes)

    # ── Decision ──────────────────────────────────────────────────────────────
    use_llm = framing_variance and linguistic_sensitivity and context_richness

    if use_llm:
        reason = (
            f"All three criteria met (framing_variance={framing_variance}, "
            f"linguistic_sensitivity={linguistic_sensitivity}, "
            f"context_richness={context_richness}). LLM generation is appropriate."
        )
    else:
        failed = []
        if not framing_variance:
            failed.append(f"framing_variance=False (intent={request.intent.value} is structurally determined)")
        if not linguistic_sensitivity:
            failed.append(f"linguistic_sensitivity=False (intent={request.intent.value} is not linguistically sensitive)")
        if not context_richness:
            failed.append(f"context_richness=False (only {len(meaningful_keys)} context signals available)")
        reason = "LLM generation is NOT the binding constraint. " + "; ".join(failed) + ". Use template path."

    return BindingConstraintResult(
        framing_variance=framing_variance,
        linguistic_sensitivity=linguistic_sensitivity,
        context_richness=context_richness,
        use_llm=use_llm,
        reason=reason,
    )
