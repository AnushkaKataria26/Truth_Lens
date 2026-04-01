from typing import Literal

def classify_risk(authenticity_score: float) -> Literal["high", "medium", "authentic"]:
    # Classification thresholds:
    if authenticity_score < 40:
        return "high"
    elif authenticity_score < 70:
        return "medium"
    else:
        return "authentic"
