import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.provenance.c2pa_parser import C2PAResult
from app.provenance.exif_parser import EXIFResult

logger = logging.getLogger(__name__)


@dataclass
class ProvenanceScore:
    confidence: float                          # 0.0–1.0 provenance confidence
    flags: list = field(default_factory=list)  # provenance-specific flags
    c2pa_valid: Optional[bool] = None          # True/False/None (not present)
    exif_anomalies: list = field(default_factory=list)


def _clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))


def compute_provenance_score(
    c2pa_result: C2PAResult,
    exif_result: EXIFResult,
) -> ProvenanceScore:
    """
    Combines C2PA + EXIF results into a provenance contribution
    to the overall authenticity score.

    Provenance is the 5th modality (weight 0.10) added to the scoring engine.
    """
    base_score = 0.5  # neutral — no provenance data
    flags = []
    bonus = 0.0
    penalty = 0.0

    # ── C2PA Scoring ──
    if c2pa_result.present and c2pa_result.valid:
        bonus += 0.15           # valid signed provenance is strong authenticity signal
        if c2pa_result.ingredient_count == 0:
            bonus += 0.05       # original capture, no composite ingredients
        if c2pa_result.edit_history:
            # each edit reduces confidence, capped at 0.10
            edit_penalty = 0.05 * len(c2pa_result.edit_history)
            penalty += min(edit_penalty, 0.10)
            if len(c2pa_result.edit_history) > 3:
                flags.append("excessive_edits")
    elif c2pa_result.present and not c2pa_result.valid:
        # Tampered or invalid C2PA signature is a strong red flag
        penalty += 0.20
        flags.append("c2pa_signature_invalid")
    # c2pa not present → no change (neutral)

    # ── EXIF Scoring ──
    for flag in exif_result.flags:
        if flag == "ai_generation_software_detected":
            penalty += 0.30
            flags.append(flag)
        elif flag == "exif_stripped":
            penalty += 0.10
            flags.append(flag)
        elif flag == "future_creation_date":
            penalty += 0.15
            flags.append(flag)

    provenance_confidence = _clamp(base_score + bonus - penalty, 0.0, 1.0)

    result = ProvenanceScore(
        confidence=provenance_confidence,
        flags=flags,
        c2pa_valid=c2pa_result.valid if c2pa_result.present else None,
        exif_anomalies=exif_result.flags,
    )

    logger.info(
        f"Provenance score: confidence={provenance_confidence:.2f} "
        f"flags={flags} c2pa_valid={result.c2pa_valid}"
    )
    return result


def provenance_to_dict(result: ProvenanceScore) -> dict:
    """Serialize ProvenanceScore for API response."""
    return asdict(result)


# ─────────────────────────────────────────────────────────────────────────────
# Integration: provenance_scorer output is passed to scoring_engine.fuse()
# Add "provenance" as a 5th modality with weight 0.10
# Redistribute existing weights proportionally:
# ─────────────────────────────────────────────────────────────────────────────

MODALITY_WEIGHTS_WITH_PROVENANCE = {
    "visual": 0.36,
    "audio": 0.225,
    "text": 0.18,
    "crossmodal": 0.135,
    "provenance": 0.10,
}
