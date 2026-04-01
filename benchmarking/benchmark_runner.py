import torch
import json
from pathlib import Path

from benchmarking.config import BenchmarkConfig
from benchmarking.device_probe import probe_environment, print_environment
from benchmarking.benchmarks.efficientnetv2_bench import run_efficientnetv2_benchmark, load_efficientnetv2, MODELS_DIR as EFF_MODELS_DIR
from benchmarking.benchmarks.bilstm_bench import run_bilstm_benchmark, load_bilstm, MODELS_DIR as AUDIO_MODELS_DIR
from benchmarking.benchmarks.vit_bench import run_vit_benchmark, load_vit, MODELS_DIR as VIT_MODELS_DIR
from benchmarking.benchmarks.pipeline_bench import run_pipeline_benchmark
from benchmarking.benchmarks.rocm_ops_bench import export_to_onnx, benchmark_onnx_session

from benchmarking.results.results_formatter import (
    print_latency_comparison, 
    print_throughput_comparison,
    print_pipeline_summary, 
    save_results_json,
)
from benchmarking.results.report_generator import generate_demo_report

RESULTS_DIR = Path("benchmarking/results/output")

def load_model_for_export(model_name: str) -> torch.nn.Module:
    device = torch.device("cpu")
    if model_name == "EfficientNetV2-S":
        return load_efficientnetv2(EFF_MODELS_DIR / "efficientnetv2_best.pth", device)
    elif model_name == "BiLSTM":
        return load_bilstm(AUDIO_MODELS_DIR / "bilstm_best.pth", device)
    else:
        raise ValueError(f"Unknown model export: {model_name}")

def load_all_models_for_pipeline(config: BenchmarkConfig) -> dict:
    device = torch.device(config.devices[0] if config.devices else "cpu")
    return {
        "efficientnetv2": load_efficientnetv2(EFF_MODELS_DIR / "efficientnetv2_best.pth", device),
        "bilstm": load_bilstm(AUDIO_MODELS_DIR / "bilstm_best.pth", device),
        "vit": load_vit(VIT_MODELS_DIR / "vit_b16_best.pth", device)
    }

def main():
    config = BenchmarkConfig()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Environment probe
    env = probe_environment()
    print_environment(env)

    results = {}

    # Step 2: Per-model benchmarks
    print("\n[1/4] Benchmarking EfficientNetV2-S...")
    run_efficientnetv2_benchmark(config, results)

    print("\n[2/4] Benchmarking BiLSTM...")
    run_bilstm_benchmark(config, results)

    print("\n[3/4] Benchmarking ViT-B/16...")
    run_vit_benchmark(config, results)

    # Step 3: ONNX benchmarks (if enabled)
    # Support checking if run_onnx_benchmark exists on config, default False if missing
    run_onnx = getattr(config, "run_onnx_benchmark", False)
    
    if run_onnx and torch.cuda.is_available():
        print("\n[3.5/4] Benchmarking ONNX Runtime...")
        results["onnx"] = {}
        # ONNX exporting execution blocks
        onnx_execution_providers = getattr(config, "onnx_execution_providers", ["CUDAExecutionProvider", "CPUExecutionProvider"])
        
        for model_name, input_shape in [
            ("EfficientNetV2-S", config.efficientnetv2_input),
            ("BiLSTM", config.bilstm_input),
        ]:
            onnx_path = RESULTS_DIR / f"{model_name.lower().replace('-', '')}.onnx"
            # Export if not already exported
            if not onnx_path.exists():
                model = load_model_for_export(model_name)
                export_to_onnx(model, input_shape, model_name, onnx_path)
            for provider in onnx_execution_providers:
                try:
                    onnx_result = benchmark_onnx_session(
                        onnx_path, input_shape, [provider], config, model_name
                    )
                    results["onnx"][f"{model_name}_{provider}"] = onnx_result
                    print(f"  {model_name} | {provider}: {onnx_result['mean_ms']:.2f} ms")
                except Exception as e:
                    print(f"  {model_name} | {provider}: FAILED — {e}")

    # Step 4: Full pipeline benchmark
    print("\n[4/4] Running end-to-end pipeline benchmark...")
    models = load_all_models_for_pipeline(config)
    pipeline_results = []
    
    pipeline_media_types = getattr(config, "pipeline_media_types", ["video_mp4_deepfake"])
    
    for device_str in config.devices:
        device = torch.device(device_str)
        if device_str == "cuda" and not torch.cuda.is_available():
            continue
        for media_type in pipeline_media_types:
            batch = run_pipeline_benchmark(models, device, config, media_type)
            pipeline_results.extend(batch)
            print_pipeline_summary([r for r in batch if r.device == device_str])

    # Free heavy pipeline models
    del models
    torch.cuda.empty_cache()

    # Step 5: Print comparison tables
    print_latency_comparison(results)
    print_throughput_comparison(results)

    # Step 6: Save outputs
    save_results_json(results, env, pipeline_results, config.results_json_path)
    generate_demo_report(results, env, pipeline_results, config.report_path)

    print("\nBenchmark complete.")

if __name__ == "__main__":
    main()
