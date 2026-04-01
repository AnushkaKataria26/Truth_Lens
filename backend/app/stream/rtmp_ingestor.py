import os
import signal
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# [MOCK] Redis client for PID storage
# from app.core.redis_client import redis_client

# In-memory PID map for mock
_stream_pids: dict[str, int] = {}


def start_stream_capture(
    stream_url: str,
    session_id: str,
    output_dir: str,
    sample_interval: int = 2,
) -> Optional[int]:
    """
    FFmpeg-based frame extraction from live stream.
    Supports RTMP, HLS (m3u8), and direct video stream URLs.

    Launches FFmpeg as a non-blocking subprocess.
    Stores PID in Redis: SET "stream:pid:{session_id}" {pid} EX 86400
    Returns the subprocess PID.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Video frame extraction: 1 frame per N seconds
    video_cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-vf", f"fps=1/{sample_interval}",   # 1 frame per N seconds
        "-q:v", "2",                           # JPEG quality level
        "-f", "image2",
        os.path.join(output_dir, "frame_%08d.jpg"),
        "-loglevel", "error",
    ]

    try:
        proc = subprocess.Popen(
            video_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        # Store PID for later cleanup
        # [MOCK] In production: redis_client.setex(f"stream:pid:{session_id}", 86400, str(proc.pid))
        _stream_pids[session_id] = proc.pid

        logger.info(
            f"Started FFmpeg capture for session {session_id} "
            f"(PID={proc.pid}, interval={sample_interval}s)"
        )
        return proc.pid

    except FileNotFoundError:
        logger.error("FFmpeg not found in PATH. Install ffmpeg to enable stream capture.")
        return None
    except Exception as e:
        logger.error(f"Failed to start FFmpeg for session {session_id}: {e}")
        return None


def start_audio_capture(
    stream_url: str,
    session_id: str,
    output_dir: str,
    sample_interval: int = 2,
) -> Optional[int]:
    """
    Audio extraction from stream (parallel FFmpeg process).
    Outputs WAV segments for synthetic speech detection.
    """
    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    audio_cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",           # 16kHz sample rate (speech model input)
        "-ac", "1",               # mono
        "-f", "segment",
        "-segment_time", str(sample_interval),
        os.path.join(audio_dir, "audio_%08d.wav"),
        "-loglevel", "error",
    ]

    try:
        proc = subprocess.Popen(
            audio_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        # Store audio PID separately
        _stream_pids[f"{session_id}:audio"] = proc.pid

        logger.info(f"Started audio capture for session {session_id} (PID={proc.pid})")
        return proc.pid

    except Exception as e:
        logger.error(f"Failed to start audio capture for session {session_id}: {e}")
        return None


def stop_stream_capture(session_id: str):
    """
    Terminate FFmpeg processes (video + audio) for a session.
    Cleans up PID from Redis.
    """
    for key in [session_id, f"{session_id}:audio"]:
        pid = _stream_pids.pop(key, None)
        # [MOCK] In production: pid = redis_client.get(f"stream:pid:{key}")
        if pid:
            try:
                os.kill(int(pid), signal.SIGTERM)
                logger.info(f"Terminated FFmpeg process PID={pid} for {key}")
            except ProcessLookupError:
                logger.warning(f"FFmpeg PID={pid} already exited for {key}")
            except Exception as e:
                logger.error(f"Failed to kill FFmpeg PID={pid}: {e}")
            # redis_client.delete(f"stream:pid:{key}")


def validate_stream_url(stream_url: str, timeout: int = 5) -> bool:
    """
    Validate stream URL reachability with a HEAD request (timeout=5s).
    For RTMP URLs, attempts a quick ffprobe check instead.
    """
    if stream_url.startswith("rtmp://"):
        # Use ffprobe to validate RTMP
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-i", stream_url, "-show_entries",
                 "format=duration", "-of", "default=noprint_wrappers=1"],
                timeout=timeout,
                capture_output=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    else:
        # HTTP/HLS URL: use httpx HEAD request
        try:
            import httpx
            resp = httpx.head(stream_url, timeout=timeout, follow_redirects=True)
            return resp.status_code < 400
        except Exception:
            return False
