from dataclasses import dataclass
from typing import Optional

MODALITY_WEIGHTS = {
    "visual": 0.40,
    "audio": 0.25,
    "text": 0.20,
    "crossmodal": 0.15,
}

CRITICAL_FLAGS = ["face_swap_detected", "neural_tts_detected", "lipsync_mismatch_detected"]

@dataclass
class FusionResult:
    authenticity_score: float
    raw_fake_score: float
    per_modality_weighted_scores: dict[str, float]

def compute_fusion_score(modality_scores: dict[str, float], flags: list[str], c2pa_valid: bool = False) -> FusionResult:
    # Each modality outputs a fake_probability (0.0-1.0)
    # If a modality did not run, redistribute its weight proportionally
    
    total_valid_weight = 0.0
    for mod, score in modality_scores.items():
        if score is not None and mod in MODALITY_WEIGHTS:
            total_valid_weight += MODALITY_WEIGHTS[mod]
            
    if total_valid_weight == 0:
        # Fallback if no modalities ran
        return FusionResult(authenticity_score=100.0, raw_fake_score=0.0, per_modality_weighted_scores={})
        
    raw_fake_score = 0.0
    per_modality_weighted = {}
    
    for mod, fake_prob in modality_scores.items():
        if fake_prob is not None and mod in MODALITY_WEIGHTS:
            # Redistribute weight
            adjusted_weight = MODALITY_WEIGHTS[mod] / total_valid_weight
            weighted_score = fake_prob * adjusted_weight
            
            per_modality_weighted[mod] = weighted_score
            raw_fake_score += weighted_score
            
    # Authenticity score calculation
    authenticity_score = round((1.0 - raw_fake_score) * 100, 1)
    
    # Flag amplification
    if any(flag in CRITICAL_FLAGS for flag in flags):
        authenticity_score -= 10.0 # apply 0.1 penalty to authenticity_score (which is 10.0 on 0-100 scale)
        if authenticity_score < 0:
            authenticity_score = 0.0
            
    # C2PA bonus
    if c2pa_valid:
        authenticity_score += 5.0
        if authenticity_score > 100.0:
            authenticity_score = 100.0
            
    return FusionResult(
        authenticity_score=round(authenticity_score, 1),
        raw_fake_score=round(raw_fake_score, 4),
        per_modality_weighted_scores=per_modality_weighted
    )
