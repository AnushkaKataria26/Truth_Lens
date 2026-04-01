# TruthLens AMD GPU Benchmarking Suite

This module is designed to comprehensively measure the performance of the TruthLens application models (EfficientNetV2, BiLSTM, ViT) and entire multi-modal fusion pipelines across standard CPUs and AMD ROCm GPUs.

## Execution

The benchmark suite orchestrator should be run directly on the AMD GPU hardware instance:
```bash
python -m benchmarking.benchmark_runner
```
**Important:** Do *not* trigger the live benchmark from an HTTP request (the `/run` endpoint utilizes a Celery background dispatch to prevent blocking). Wait fully for the suite to complete (estimated 5-15 minutes). The FastAPI server will automatically serve the JSON telemetry output from `/api/v1/benchmark/results` once finished.

## Installation & Hardware Expectations

The benchmark suite relies on native PyTorch HIP pathways (`torch.cuda` calls translate directly to AMD ROCm). 
Install dependencies via:
```bash
pip install -r benchmarking/requirements_benchmark.txt
```

### AMD ROCm ONNX Runtime

`onnxruntime-rocm` is NOT available on standard PyPI. To evaluate the `ROCMExecutionProvider` graphs (Section 8), you must pull the wheel directly from AMD:
```bash
pip install --pre onnxruntime-rocm -f https://repo.radeon.com/rocm/manylinux/rocm-rel-6.1/
```

### Expected Hardware Speedups (vs CPU)
Depending on your specific AMD instinct/Radeon GPU, expect the following telemetry ceilings during `fp16` evaluation:
* **EfficientNetV2-S:** 14-25x 
* **ViT-B/16:** 18-35x
* **BiLSTM:** 5-10x

### Implementation Details
* **Precision Timing:** GPU latency is measured strictly using asynchronous `torch.cuda.Event` boundaries wrapping the forward passes, ensuring perfect hardware alignment.
* **Warmup JIT Cycles:** The suite forces explicit model warmup iterations (N=5-10) before tracking metrics to discard Pytorch JIT and graph caching overheads naturally.
* **Concurrency:** Sustained throughput tests simulate heavy frontend traffic by spawning threads across independent continuous `torch.no_grad()` evaluation loops.
