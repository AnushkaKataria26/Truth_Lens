import json
from dataclasses import dataclass
from typing import List

from app.agents.tools.arxiv_scraper import ArxivPaper
from app.agents.tools.hf_model_monitor import HFModel

PATTERN_PROMPT = """
You are a deepfake detection researcher. Extract detection-relevant technical patterns
from this paper abstract that could improve an existing detection model.

Abstract: {abstract}

Return JSON:
{{
  "attack_type": "<GAN/diffusion/voice_clone/face_swap/etc>",
  "detection_signals": ["<signal1>", "<signal2>"],
  "recommended_augmentation": "<data augmentation strategy>",
  "novelty_score": <0.0-1.0, how novel vs known techniques>
}}
"""

@dataclass
class ExtractedPattern:
    attack_type: str
    detection_signals: List[str]
    recommended_augmentation: str
    novelty_score: float
    source_id: str

def extract_patterns(papers: List[ArxivPaper], models: List[HFModel]) -> List[ExtractedPattern]:
    # Input: list of ArxivPaper + HFModel objects
    # For each paper abstract, call LLM with prompt:
    # novelty_score is LLM-estimated — used in evaluate_novelty_node
    # Store extracted patterns in DB: agent_extracted_patterns
    # Return: list of ExtractedPattern
    
    extracted = []
    
    # [MOCK LLM Call]
    for paper in papers:
        # call_llm(PATTERN_PROMPT.format(abstract=paper.abstract))
        extracted.append(ExtractedPattern(
            attack_type="diffusion",
            detection_signals=["high-frequency artifacts", "frequency domain analysis"],
            recommended_augmentation="JPEG compression noise",
            novelty_score=0.85,
            source_id=paper.id
        ))
        
    for model in models:
        # Similarly extract from model description
        extracted.append(ExtractedPattern(
            attack_type="face_swap",
            detection_signals=["boundary blending artifacts"],
            recommended_augmentation="random cropping and resizing",
            novelty_score=0.45,
            source_id=model.model_id
        ))
        
    return extracted
