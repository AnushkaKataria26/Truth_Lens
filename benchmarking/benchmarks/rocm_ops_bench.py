import torch
import onnx
import onnxruntime as ort
import numpy as np
import time
from pathlib import Path
from benchmarking.profiling.warmup import warmup_onnx_session

def export_to_onnx(model, input_shape: tuple, model_name: str, output_path: Path):
    model.eval()
    dummy = torch.randn(1, *input_shape)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        model,
        dummy,
        output_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
    print(f"Exported {model_name} to ONNX: {output_path}")

    # Validate ONNX model
    onnx_model = onnx.load(str(output_path))
    onnx.checker.check_model(onnx_model)
    print(f"ONNX model validated: {model_name}")

def benchmark_onnx_session(
    onnx_path: Path,
    input_shape: tuple,
    providers: list,
    config,
    model_name: str,
) -> dict:
    session_opts = ort.SessionOptions()
    session_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(
        str(onnx_path),
        sess_options=session_opts,
        providers=providers,
    )

    input_name = session.get_inputs()[0].name
    dummy = np.random.randn(1, *input_shape).astype(np.float32)

    # Warmup
    warmup_onnx_session(session, input_name, input_shape, n_runs=config.warmup_runs)

    # Measure latency
    latencies = []
    for _ in range(config.measurement_runs):
        start = time.perf_counter()
        session.run(None, {input_name: dummy})
        end = time.perf_counter()
        latencies.append((end - start) * 1000)

    latencies = np.array(latencies)
    active_provider = session.get_providers()[0]

    return {
        "model_name": model_name,
        "provider": active_provider,
        "mean_ms": float(np.mean(latencies)),
        "median_ms": float(np.median(latencies)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "min_ms": float(np.min(latencies)),
        "max_ms": float(np.max(latencies)),
    }
