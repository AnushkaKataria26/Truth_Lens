import torch
import psutil
import os
from dataclasses import dataclass

@dataclass
class MemoryResult:
    device: str
    model_name: str
    batch_size: int
    precision: str
    model_params_millions: float
    model_size_mb: float
    peak_gpu_memory_mb: float     # 0 if CPU
    gpu_memory_reserved_mb: float
    cpu_process_memory_mb: float

def measure_memory(
    model,
    input_shape: tuple,
    device: torch.device,
    batch_size: int,
    model_name: str,
    precision: str = "fp32",
) -> MemoryResult:
    param_count = sum(p.numel() for p in model.parameters())
    model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.empty_cache()

    dummy_input = torch.randn(batch_size, *input_shape).to(device)
    if precision == "fp16" and device.type == "cuda":
        model = model.half()
        dummy_input = dummy_input.half()

    with torch.no_grad():
        _ = model(dummy_input)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
        peak_gpu_mb = torch.cuda.max_memory_allocated(device) / (1024**2)
        reserved_mb = torch.cuda.memory_reserved(device) / (1024**2)
    else:
        peak_gpu_mb = 0.0
        reserved_mb = 0.0

    process = psutil.Process(os.getpid())
    cpu_mem_mb = process.memory_info().rss / (1024**2)

    return MemoryResult(
        device=str(device),
        model_name=model_name,
        batch_size=batch_size,
        precision=precision,
        model_params_millions=round(param_count / 1e6, 2),
        model_size_mb=round(model_size_mb, 2),
        peak_gpu_memory_mb=round(peak_gpu_mb, 2),
        gpu_memory_reserved_mb=round(reserved_mb, 2),
        cpu_process_memory_mb=round(cpu_mem_mb, 2),
    )
