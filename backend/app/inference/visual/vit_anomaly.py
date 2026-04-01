from dataclasses import dataclass

@dataclass
class ViTResult:
    anomaly_score: float
    anomaly_map: list[list[float]] # 14x14 attention grid

def detect_pixel_anomalies(frame_paths: list[str]) -> ViTResult:
    # Model: ViT-B/16 fine-tuned for pixel anomaly detection
    # Input: full frame (not just face crop), resized to 384x384
    # Detects splicing, inpainting, copy-move artifacts
    
    # Run on max 10 frames (evenly spaced) to control latency
    if len(frame_paths) > 10:
        step = max(1, len(frame_paths) // 10)
        selected_frames = frame_paths[::step][:10]
    else:
        selected_frames = frame_paths
        
    # [MOCK] Process selected_frames through ViT model
    # import torch
    # model = load_vit_model()
    # grid = model(frames) ...
    
    anomaly_score = 0.35 # Example score
    
    # 14x14 mock grid
    anomaly_map = [[0.0 for _ in range(14)] for _ in range(14)]
    
    return ViTResult(
        anomaly_score=anomaly_score,
        anomaly_map=anomaly_map
    )
