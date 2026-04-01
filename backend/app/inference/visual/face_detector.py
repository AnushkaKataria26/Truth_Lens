from dataclasses import dataclass
from typing import Optional
import os

# Mocks for ml libraries
# from facenet_pytorch import MTCNN
# import torch
# from PIL import Image

@dataclass
class FaceDetection:
    frame_idx: int
    bbox: Optional[list[int]] # [x1, y1, x2, y2]
    crop_path: Optional[str]
    confidence: float

def detect_faces(frame_paths: list[str], job_id: str) -> list[FaceDetection]:
    # Use MTCNN (facenet-pytorch) for face detection on each keyframe
    # [MOCK] We assume torch & mtcnn are available
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # mtcnn = MTCNN(keep_all=True, device=device)
    
    tmp_dir = f"/tmp/{job_id}/faces"
    os.makedirs(tmp_dir, exist_ok=True)
    
    results = []
    
    for idx, frame_path in enumerate(frame_paths):
        # [MOCK] img = Image.open(frame_path)
        # boxes, probs = mtcnn.detect(img)
        
        # Mocking detection outcome
        box = [100, 100, 250, 250]
        prob = 0.98
        
        if prob > 0.0:
            # Crop detected faces with 20px padding
            # [MOCK] img_crop = img.crop(...)
            crop_path = f"{tmp_dir}/frame_{idx}_face.jpg"
            # img_crop.save(crop_path)
            
            results.append(FaceDetection(
                frame_idx=idx,
                bbox=box,
                crop_path=crop_path,
                confidence=prob
            ))
        else:
            # If no face detected in frame, mark frame as "no_face"
            results.append(FaceDetection(
                frame_idx=idx,
                bbox=None,
                crop_path=None,
                confidence=0.0
            ))
            
    return results
