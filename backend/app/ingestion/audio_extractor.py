import subprocess
import os

def extract_audio(s3_media_path: str, job_id: str) -> str:
    # Input: S3 path to video or audio file
    # [MOCK] download from s3
    
    tmp_dir = f"/tmp/{job_id}"
    os.makedirs(tmp_dir, exist_ok=True)
    local_input = f"{tmp_dir}/input_media"
    
    output_wav = f"{tmp_dir}/audio.wav"
    
    # FFmpeg command to normalize to 16kHz, mono, PCM WAV
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", local_input,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            output_wav
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass # handle
        
    # Upload to S3: media/{job_id}/audio.wav
    # [MOCK] s3_client.upload(...)
    
    return output_wav
