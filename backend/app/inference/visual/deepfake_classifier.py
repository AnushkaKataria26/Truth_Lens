from dataclasses import dataclass
from typing import Optional
import os

from app.inference.visual.face_detector import FaceDetection

@dataclass
class VisualResult:
    fake_probability: float
    per_frame_scores: list[dict]
    manipulation_type: str

def get_manipulation_hint(fake_prob: float) -> str:
    if fake_prob > 0.85:
        return "face_swap"
    elif fake_prob > 0.65:
        return "face_reenactment"
    elif fake_prob > 0.45:
        return "partial_manipulation"
    else:
        return "authentic"

def classify_deepfakes(face_detections: list[FaceDetection]) -> VisualResult:
    import torch
    import torch.nn as nn
    import torchvision.transforms as T
    from PIL import Image
    from torchvision.models import efficientnet_v2_s

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load model
    model = efficientnet_v2_s()
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    
    model_path = "models/efficientnetv2_ff.pth"
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    
    transforms = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    valid_faces = [fd for fd in face_detections if fd.crop_path is not None]
    
    if not valid_faces:
        return VisualResult(fake_probability=0.0, per_frame_scores=[], manipulation_type="authentic")
    
    # Batch process all face crops (batch_size=8)
    per_frame_scores = []
    total_weight = 0.0
    weighted_sum = 0.0
    
    for face in valid_faces:
        try:
            img = Image.open(face.crop_path).convert("RGB")
            tensor = transforms(img).unsqueeze(0).to(device)
            with torch.no_grad():
                out = model(tensor)
                prob = torch.softmax(out, dim=1)[0, 1].item()
        except Exception as e:
            print(f"Error processing face crop: {e}")
            prob = 0.0
        
        per_frame_scores.append({
            "frame_idx": face.frame_idx,
            "fake_probability": prob,
            "confidence": face.confidence
        })
        
        # aggregate across all crops: weighted average where weight = face detection confidence
        weight = face.confidence
        weighted_sum += prob * weight
        total_weight += weight
        
    avg_fake_prob = weighted_sum / total_weight if total_weight > 0 else 0.0
    manipulation_type = get_manipulation_hint(avg_fake_prob)
    
    return VisualResult(
        fake_probability=avg_fake_prob,
        per_frame_scores=per_frame_scores,
        manipulation_type=manipulation_type
    )
