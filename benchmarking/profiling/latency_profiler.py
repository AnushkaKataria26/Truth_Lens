import torch
import time
import numpy as np
from dataclasses import dataclass

@dataclass
class LatencyResult:
    device: str
    model_name: str
    precision: str
    batch_size: int
    n_runs: int
    latencies_ms: list[float]
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    std_ms: float

def measure_latency(
    model,
    input_shape: tuple,
    device: torch.device,
    config,
    model_name: str,
    precision: str = "fp32",
) -> LatencyResult:
    model.eval()
    use_fp16 = (precision == "fp16" and device.type == "cuda")

    if use_fp16:
        model = model.half()

    dummy_input = torch.randn(config.batch_size_latency, *input_shape).to(device)
    if use_fp16:
        dummy_input = dummy_input.half()

    # Import locally to avoid circular dependencies if needed
    from benchmarking.profiling.warmup import warmup_model

    # Warmup
    warmup_model(model, input_shape, device, n_runs=config.warmup_runs,
                 batch_size=config.batch_size_latency)

    latencies_ms = []

    # Use CUDA events for GPU timing — more accurate than time.perf_counter on GPU
    if device.type == "cuda":
        for _ in range(config.measurement_runs):
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()
            with torch.no_grad():
                if use_fp16:
                    with torch.cuda.amp.autocast():
                        _ = model(dummy_input)
                else:
                    _ = model(dummy_input)
            end_event.record()
            torch.cuda.synchronize(device)
            latencies_ms.append(start_event.elapsed_time(end_event))
    else:
        # CPU timing with time.perf_counter
        for _ in range(config.measurement_runs):
            start = time.perf_counter()
            with torch.no_grad():
                _ = model(dummy_input)
            end = time.perf_counter()
            latencies_ms.append((end - start) * 1000)

    latencies = np.array(latencies_ms)

    return LatencyResult(
        device=str(device),
        model_name=model_name,
        precision=precision,
        batch_size=config.batch_size_latency,
        n_runs=config.measurement_runs,
        latencies_ms=latencies.tolist(),
        mean_ms=float(np.mean(latencies)),
        median_ms=float(np.median(latencies)),
        p95_ms=float(np.percentile(latencies, 95)),
        p99_ms=float(np.percentile(latencies, 99)),
        min_ms=float(np.min(latencies)),
        max_ms=float(np.max(latencies)),
        std_ms=float(np.std(latencies)),
    )
