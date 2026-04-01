import os
from typing import Optional

def generate_heatmap(job_id: str, visual_result, frame_paths: list[str]) -> list[str]:
    # Use GradCAM on EfficientNetV2 final convolutional layer
    # Target layer: model.features[-1]
    # Generate for the 3 highest fake_probability frames only
    
    # Sort per_frame_scores by probability
    scores = sorted(visual_result.per_frame_scores, key=lambda x: x["fake_probability"], reverse=True)
    top_3 = scores[:3]
    
    heatmaps_dir = f"/tmp/{job_id}/heatmaps"
    os.makedirs(heatmaps_dir, exist_ok=True)
    
    s3_urls = []
    
    for item in top_3:
        idx = item["frame_idx"]
        frame_path = frame_paths[idx] if idx < len(frame_paths) else None
        
        if frame_path:
            # [MOCK] gradcam generation
            # Output: RGB heatmap overlaid on original frame (cv2 applyColorMap COLORMAP_JET)
            # Resize heatmap to original frame dimensions
            # Save as PNG
            
            heatmap_path = f"{heatmaps_dir}/heatmap_{idx}.png"
            # cv2.imwrite(heatmap_path, heatmap_img)
            
            # upload to S3: media/{job_id}/heatmaps/heatmap_{frame_idx}.png
            # [MOCK] s3_client.upload(heatmap_path, f"s3://truthlens-media/media/{job_id}/heatmaps/heatmap_{idx}.png")
            
            s3_urls.append(f"s3://truthlens-media/media/{job_id}/heatmaps/heatmap_{idx}.png")
            
    return s3_urls
