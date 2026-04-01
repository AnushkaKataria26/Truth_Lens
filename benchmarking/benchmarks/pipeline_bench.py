import time
import torch
import numpy as np
from dataclasses import dataclass

@dataclass
class PipelineResult:
    device: str
    media_type: str
    run_index: int
    ingestion_ms: float
    visual_ms: float
    audio_ms: float
    text_ms: float
    crossmodal_ms: float
    fusion_ms: float
    total_ms: float

def run_pipeline_benchmark(models: dict, device: torch.device, config, media_type: str) -> list[PipelineResult]:
    results = []

    for run_idx in range(config.pipeline_runs):
        timings = {}

        # Simulate ingestion (FFmpeg extraction — CPU bound, not GPU)
        t0 = time.perf_counter()
        synthetic_frames = [torch.randn(3, 224, 224) for _ in range(10)]  # 10 keyframes
        synthetic_audio = torch.randn(1, 128, 300)  # mel spectrogram
        synthetic_text_embedding = torch.randn(1, 384)  # sentence embedding
        timings["ingestion_ms"] = (time.perf_counter() - t0) * 1000

        # Visual inference
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t0 = time.perf_counter()
        frame_batch = torch.stack(synthetic_frames).to(device)
        with torch.no_grad():
            _ = models["efficientnetv2"](frame_batch)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        timings["visual_ms"] = (time.perf_counter() - t0) * 1000

        # Audio inference
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        t0 = time.perf_counter()
        audio_input = synthetic_audio.to(device)
        with torch.no_grad():
            _ = models["bilstm"](audio_input)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        timings["audio_ms"] = (time.perf_counter() - t0) * 1000

        # Text inference (LLM call simulated as fixed latency — actual LLM is API-based)
        timings["text_ms"] = 250.0  # realistic GPT-4 API latency estimate in ms

        # Cross-modal (SyncNet simulation)
        t0 = time.perf_counter()
        time.sleep(0.01)  # SyncNet ~10ms CPU estimate
        timings["crossmodal_ms"] = (time.perf_counter() - t0) * 1000

        # Fusion (numpy weighted average — CPU)
        t0 = time.perf_counter()
        _ = np.average([0.4, 0.6, 0.7, 0.5], weights=[0.36, 0.225, 0.18, 0.135])
        timings["fusion_ms"] = (time.perf_counter() - t0) * 1000

        total = sum(timings.values())

        results.append(PipelineResult(
            device=str(device),
            media_type=media_type,
            run_index=run_idx,
            **timings,
            total_ms=total,
        ))

    return results
