from dataclasses import dataclass
from typing import List

from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image

@dataclass
class ContextResult:
    clip_similarity: float
    reverse_search_match: bool
    flags: list[str]

# Cache model at module level so it isn't repeatedly loaded
_clip_model = None
_clip_processor = None

def get_clip_model():
    global _clip_model, _clip_processor
    if _clip_model is None:
        try:
            _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        except Exception as e:
            print(f"Error loading CLIP model: {e}")
    return _clip_model, _clip_processor

def match_context(image_path: str, caption_text: str) -> ContextResult:
    # CLIP-based image-text consistency
    # Model: openai/clip-vit-base-patch32 via HuggingFace transformers
    
    model, processor = get_clip_model()
    
    clip_similarity = 0.0
    
    if model and processor:
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(text=[caption_text], images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            # Use cosine similarity of embeddings for better scoring bounds
            image_embeds = outputs.image_embeds / outputs.image_embeds.norm(dim=-1, keepdim=True)
            text_embeds = outputs.text_embeds / outputs.text_embeds.norm(dim=-1, keepdim=True)
            clip_similarity = (image_embeds @ text_embeds.T).item()
            # Normalize from [-1, 1] to [0, 1] roughly
            clip_similarity = max(0.0, min(1.0, (clip_similarity + 1.0) / 2.0))
        except Exception as e:
            print(f"Error computing CLIP similarity: {e}")
            clip_similarity = 0.5
    else:
        clip_similarity = 0.85 # Fallback example mock normalized score
    
    flags = []
    
    # Low similarity (< 0.25) → "caption_image_mismatch" flag
    if clip_similarity < 0.25:
        flags.append("caption_image_mismatch")
        
    # Also: reverse image search via SerpAPI (Google Lens API)
    # if image found with different original caption, raise "recontextualized_media" flag
    reverse_search_match = True
    # [MOCK if different context found]
    # flags.append("recontextualized_media")
    
    return ContextResult(
        clip_similarity=clip_similarity,
        reverse_search_match=reverse_search_match,
        flags=flags
    )
