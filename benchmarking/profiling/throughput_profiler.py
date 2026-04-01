import torch
import time
import threading
from dataclasses import dataclass

from benchmarking.profiling.warmup import warmup_model

@dataclass
class ThroughputResult:
    device: str
    model_name: str
    batch_size: int
    concurrent_workers: int
    samples_per_second: float
    batches_per_second: float
    duration_seconds: float
    total_samples_processed: int

def measure_throughput(
    model,
    input_shape: tuple,
    device: torch.device,
    batch_size: int,
    duration_seconds: int,
    model_name: str,
    n_workers: int = 1,
) -> ThroughputResult:
    model.eval()
    dummy_input = torch.randn(batch_size, *input_shape).to(device)
    total_batches = 0
    stop_event = threading.Event()

    def inference_worker():
        nonlocal total_batches
        with torch.no_grad():
            while not stop_event.is_set():
                _ = model(dummy_input)
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                total_batches += 1

    # Warmup before throughput measurement
    warmup_model(model, input_shape, device, n_runs=5, batch_size=batch_size)

    threads = [threading.Thread(target=inference_worker) for _ in range(n_workers)]
    start_time = time.perf_counter()
    for t in threads:
        t.start()

    time.sleep(duration_seconds)
    stop_event.set()
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start_time
    total_samples = total_batches * batch_size

    return ThroughputResult(
        device=str(device),
        model_name=model_name,
        batch_size=batch_size,
        concurrent_workers=n_workers,
        samples_per_second=total_samples / elapsed,
        batches_per_second=total_batches / elapsed,
        duration_seconds=elapsed,
        total_samples_processed=total_samples,
    )
