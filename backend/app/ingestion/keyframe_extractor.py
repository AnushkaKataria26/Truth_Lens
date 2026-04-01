import subprocess
import os
import glob

def extract_keyframes(s3_video_path: str, job_id: str) -> list[str]:
    # Input: S3 path to video file
    # Download to /tmp/{job_id}/input_video.*
    # We mock the download and assume input.mp4 is available at local_path
    
    tmp_dir = f"/tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    frames_dir = os.path.join(tmp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    local_video_path = f"{tmp_dir}/input_video.mp4"
    # [MOCK] download the file to local_video_path
    
    # Use FFmpeg subprocess to extract I-frames
    frames_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", local_video_path,
            "-vf", "select=eq(pict_type\,I)",
            "-vsync", "vfr", frames_pattern
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass # Handle or log error
        
    extracted_frames = glob.glob(os.path.join(frames_dir, "frame_*.jpg"))
    
    # Additionally extract 1 frame per 2 seconds as fallback if keyframe count < 5
    if len(extracted_frames) < 5:
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", local_video_path,
                "-vf", "fps=1/2",
                os.path.join(frames_dir, "fallback_%04d.jpg")
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass
            
        extracted_frames = glob.glob(os.path.join(frames_dir, "*.jpg"))
        
    # Target: max 30 frames per video to control inference time
    extracted_frames = sorted(extracted_frames)[:30]
    
    # Upload extracted frames to S3: media/{job_id}/frames/
    # [MOCK] s3_client.upload(...)
    
    return extracted_frames
