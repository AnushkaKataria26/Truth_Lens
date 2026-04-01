from dataclasses import dataclass, field
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results" / "output"
MODELS_DIR = Path(__file__).parent.parent / "training" / "saved_models"

@dataclass
class BenchmarkConfig:
    # Devices to benchmark
    devices: list = field(default_factory=lambda: ["cpu", "cuda"])
    # cuda maps to ROCm on AMD hardware via PyTorch HIP backend

    # Latency benchmark settings
    warmup_runs: int = 10          # runs discarded before measurement begins
    measurement_runs: int = 100    # runs used for latency statistics
    batch_size_latency: int = 1    # single-sample latency (real-time use case)

    # Throughput benchmark settings
    throughput_duration_seconds: int = 30   # sustained load duration
    throughput_batch_sizes: list = field(default_factory=lambda: [1, 4, 8, 16, 32])
    concurrent_workers: list = field(default_factory=lambda: [1, 2, 4])

    # Input dimensions per model
    efficientnetv2_input: tuple = (3, 224, 224)    # C, H, W
    bilstm_input: tuple = (128, 300)               # n_mels, max_frames
    vit_input: tuple = (3, 384, 384)               # C, H, W

    # Pipeline benchmark
    pipeline_media_types: list = field(default_factory=lambda: ["video", "image", "audio"])
    pipeline_runs: int = 20

    # Precision modes
    precision_modes: list = field(default_factory=lambda: ["fp32", "fp16"])
    # fp16 = mixed precision / half precision — maps to ROCm fp16 on AMD

    # ONNX Runtime settings
    run_onnx_benchmark: bool = True
    onnx_execution_providers: list = field(
        default_factory=lambda: ["ROCMExecutionProvider", "CPUExecutionProvider"]
    )

    # Output
    results_json_path: Path = RESULTS_DIR / "benchmark_results.json"
    report_path: Path = RESULTS_DIR / "benchmark_report.txt"
    save_intermediate: bool = True   # save per-model results as they complete
