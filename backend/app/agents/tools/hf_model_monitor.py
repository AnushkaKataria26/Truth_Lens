import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class HFModel:
    model_id: str
    description: str
    tags: List[str]
    last_modified: str

def fetch_recent_models() -> List[HFModel]:
    # Use HuggingFace Hub API (huggingface_hub library)
    # Query tags: ["deepfake", "face-detection", "audio-deepfake", "synthetic-detection"]
    # Filter: models updated in last 7 days, sorted by downloads desc, top 10 per tag
    # For each model: extract model_id, description, tags, last_modified
    # Flag models that appear new (not in DB table: agent_seen_hf_models)
    # Return: list of HFModel(model_id, description, tags, last_modified)
    
    # [MOCK IMPLEMENTATION]
    models = []
    
    models.append(HFModel(
        model_id="mock_user/mock_deepfake_detector",
        description="A mock deepfake detection model.",
        tags=["deepfake", "face-detection"],
        last_modified=datetime.datetime.utcnow().isoformat()
    ))
    
    return models
