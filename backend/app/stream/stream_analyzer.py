import uuid
import time
import json
import logging
from datetime import datetime
from typing import Optional

from app.stream.frame_sampler import SegmentResult, store_segment_result
from app.stream.stream_manager import increment_segment_count

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Reduced pipeline for real-time stream analysis.
# Full pipeline is too slow; stream analysis runs a lightweight subset.
# ─────────────────────────────────────────────────────────────────────────────

STREAM_WEIGHTS = {
    "visual": 0.60,
    "audio": 0.30,
    "crossmodal": 0.10,
}

# Skipped in stream mode (too slow or not applicable):
# - Full RAG fact-check (text) — requires LLM round-trip
# - CLIP context matcher — unnecessary for frame-level analysis
# - C2PA metadata — no provenance metadata in live streams


def _detect_faces(frame_path: str) -> list[dict]:
    """
    Face detection using MTCNN — fast, ~50ms.
    Returns list of face bounding boxes.
    """
    # [MOCK] In production: MTCNN(image_size=160, margin=20).detect(img)
    return [{"box": [100, 80, 200, 200], "confidence": 0.98}]


def _classify_deepfake(frame_path: str, face_boxes: list[dict]) -> dict:
    """
    EfficientNetV2 deepfake classification on detected faces — ~150ms on GPU.
    Returns fake probability per face.
    """
    # [MOCK] In production: model.predict(cropped_face)
    return {
        "fake_probability": 0.35,
        "model": "efficientnet_v2_deepfake",
    }


def _generate_gradcam(frame_path: str) -> Optional[str]:
    """
    GradCAM heatmap — only generated if fake_probability > 0.6.
    Avoids heatmap cost on clean frames.
    Returns S3 URL of heatmap image (or None).
    """
    # [MOCK] In production:
    # heatmap = gradcam(model, img)
    # s3_url = upload_to_s3(heatmap, f"heatmaps/stream/{session_id}/{segment}.jpg")
    return None


def _vit_anomaly_detection(frame_path: str) -> dict:
    """
    ViT anomaly detection — fallback when no face detected (image manipulation).
    """
    # [MOCK]
    return {"anomaly_score": 0.15, "model": "vit_anomaly"}


def _detect_synthetic_speech(audio_path: str) -> dict:
    """
    Synthetic speech detector on audio segment.
    Runs ONLY the synthetic detector (skip vocoder fingerprinting for speed).
    """
    # [MOCK]
    return {"synthetic_probability": 0.12, "model": "wav2vec_synthetic"}


def _check_lipsync(frame_path: str, audio_path: str) -> dict:
    """
    LipSync verification — only when both face AND audio are present.
    """
    # [MOCK]
    return {"sync_score": 0.92, "model": "syncnet_v2"}


def analyze_segment(
    session_id: str,
    segment_index: int,
    frame_path: str,
    audio_path: Optional[str] = None,
    frame_timestamp: float = 0.0,
) -> SegmentResult:
    """
    Per-segment inference — lightweight subset of the full analysis pipeline.

    Execution order:
    1. Face detection (MTCNN) — fast, ~50ms
    2. EfficientNetV2 deepfake classification on detected faces — ~150ms on GPU
    3. GradCAM heatmap ONLY if fake_probability > 0.6
    4. ViT anomaly ONLY if no face detected (image manipulation fallback)
    5. Per audio segment: synthetic_detector ONLY — skip vocoder
    6. LipSync ONLY if both face and audio present
    """
    start_time = time.time()
    flags = []
    visual_score = 1.0
    audio_score = 1.0
    crossmodal_score = 1.0
    heatmap_url = None

    # ── Step 1: Face detection ──
    faces = _detect_faces(frame_path)

    if faces:
        # ── Step 2: EfficientNetV2 deepfake classification ──
        deepfake_result = _classify_deepfake(frame_path, faces)
        fake_prob = deepfake_result["fake_probability"]
        visual_score = 1.0 - fake_prob

        if fake_prob > 0.6:
            flags.append("deepfake_face")
            # ── Step 3: GradCAM heatmap ──
            heatmap_url = _generate_gradcam(frame_path)

        if fake_prob > 0.8:
            flags.append("high_confidence_fake")
    else:
        # ── Step 4: ViT anomaly (no face fallback) ──
        anomaly = _vit_anomaly_detection(frame_path)
        visual_score = 1.0 - anomaly["anomaly_score"]
        if anomaly["anomaly_score"] > 0.6:
            flags.append("image_manipulation")

    # ── Step 5: Audio analysis ──
    if audio_path:
        synthetic = _detect_synthetic_speech(audio_path)
        audio_score = 1.0 - synthetic["synthetic_probability"]
        if synthetic["synthetic_probability"] > 0.6:
            flags.append("synthetic_speech")

        # ── Step 6: LipSync (face + audio required) ──
        if faces:
            lipsync = _check_lipsync(frame_path, audio_path)
            crossmodal_score = lipsync["sync_score"]
            if lipsync["sync_score"] < 0.5:
                flags.append("lipsync_mismatch")

    # ── Compute weighted authenticity score ──
    authenticity_score = round(
        visual_score * STREAM_WEIGHTS["visual"] * 100
        + audio_score * STREAM_WEIGHTS["audio"] * 100
        + crossmodal_score * STREAM_WEIGHTS["crossmodal"] * 100,
        1,
    )

    # Determine risk level
    if authenticity_score < 40:
        risk_level = "high"
    elif authenticity_score < 70:
        risk_level = "medium"
    else:
        risk_level = "authentic"

    processing_time_ms = int((time.time() - start_time) * 1000)

    result = SegmentResult(
        id=str(uuid.uuid4()),
        session_id=session_id,
        segment_index=segment_index,
        frame_timestamp=frame_timestamp,
        authenticity_score=authenticity_score,
        risk_level=risk_level,
        flags_raised=flags,
        heatmap_s3_url=heatmap_url,
        processing_time_ms=processing_time_ms,
        created_at=datetime.utcnow().isoformat(),
    )

    # Persist result
    store_segment_result(result)
    increment_segment_count(session_id)

    # ── Push alert for high-risk segments ──
    if risk_level == "high":
        _push_alert(session_id, result)

    logger.info(
        f"Segment {segment_index} analyzed: score={authenticity_score} "
        f"risk={risk_level} flags={flags} time={processing_time_ms}ms"
    )
    return result


def _push_alert(session_id: str, result: SegmentResult):
    """
    Push high-risk segment alert to Redis pub/sub channel.
    Frontend subscribes via SSE endpoint.
    Channel: "stream:{session_id}:alerts"
    """
    alert_data = {
        "segment_index": result.segment_index,
        "frame_timestamp": result.frame_timestamp,
        "authenticity_score": result.authenticity_score,
        "risk_level": result.risk_level,
        "flags_raised": result.flags_raised,
        "heatmap_url": result.heatmap_s3_url,
        "detected_at": result.created_at,
    }

    # [MOCK] In production:
    # redis_client.publish(f"stream:{session_id}:alerts", json.dumps(alert_data))
    logger.info(f"ALERT pushed for session {session_id}: segment {result.segment_index}")
