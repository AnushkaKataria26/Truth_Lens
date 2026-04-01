import json
from pathlib import Path
import numpy as np

def print_latency_comparison(results: dict):
    models = ["efficientnetv2", "bilstm", "vit_b16"]  # Adjusted 'vit' to 'vit_b16' to match Section 7 loop mapping
    print("\n" + "="*70)
    print("INFERENCE LATENCY COMPARISON — CPU vs AMD GPU (ROCm)")
    print("="*70)
    print(f"{'Model':<20} {'Precision':<10} {'CPU (ms)':<15} {'GPU (ms)':<15} {'Speedup':<10}")
    print("-"*70)

    for model in models:
        model_results = results.get(model, {}).get("latency", {})
        for precision in ["fp32", "fp16"]:
            cpu_key = f"cpu_{precision}"
            gpu_key = f"cuda_{precision}"
            cpu_mean = model_results.get(cpu_key, {}).get("mean_ms")
            gpu_mean = model_results.get(gpu_key, {}).get("mean_ms")

            if cpu_mean is None:
                continue

            if gpu_mean:
                speedup = cpu_mean / gpu_mean
                gpu_str = f"{gpu_mean:.2f}"
                speedup_str = f"{speedup:.1f}x"
            else:
                gpu_str = "N/A"
                speedup_str = "N/A"

            print(f"{model:<20} {precision:<10} {cpu_mean:<15.2f} {gpu_str:<15} {speedup_str:<10}")

    print("="*70)

def print_throughput_comparison(results: dict):
    print("\n" + "="*70)
    print("SUSTAINED THROUGHPUT — AMD GPU (samples/second)")
    print("="*70)
    print(f"{'Model':<20} {'Batch Size':<12} {'GPU (samp/s)':<18} {'CPU (samp/s)':<18}")
    print("-"*70)

    models = ["efficientnetv2", "bilstm", "vit_b16"]
    for model in models:
        tput_results = results.get(model, {}).get("throughput", {})
        for bs in [1, 8, 32]:
            gpu_key = f"cuda_bs{bs}"
            cpu_key = f"cpu_bs{bs}"
            gpu_sps = tput_results.get(gpu_key, {}).get("samples_per_second")
            cpu_sps = tput_results.get(cpu_key, {}).get("samples_per_second")
            
            # Print row if gpu or cpu is present, skip otherwise to keep table clean for ViT limited bs
            if not gpu_sps and not cpu_sps:
                continue
                
            gpu_str = f"{gpu_sps:.1f}" if gpu_sps else "N/A"
            cpu_str = f"{cpu_sps:.1f}" if cpu_sps else "N/A"
            print(f"{model:<20} {bs:<12} {gpu_str:<18} {cpu_str:<18}")

    print("="*70)

def print_pipeline_summary(pipeline_results: list):
    if not pipeline_results:
        return

    totals = [r.total_ms for r in pipeline_results]
    visuals = [r.visual_ms for r in pipeline_results]
    audios = [r.audio_ms for r in pipeline_results]

    print("\n" + "="*70)
    print("END-TO-END PIPELINE BENCHMARK")
    print("="*70)
    print(f"Media type:        {pipeline_results[0].media_type}")
    print(f"Device:            {pipeline_results[0].device}")
    print(f"Runs:              {len(pipeline_results)}")
    print(f"Mean total:        {np.mean(totals):.1f} ms")
    print(f"P95 total:         {np.percentile(totals, 95):.1f} ms")
    print(f"  Visual module:   {np.mean(visuals):.1f} ms")
    print(f"  Audio module:    {np.mean(audios):.1f} ms")
    print(f"  Text (API est.): 250.0 ms")
    print("="*70)

def save_results_json(results: dict, env: dict, pipeline_results: list, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "environment": env,
        "benchmark_results": results,
        "pipeline_results": [r.__dict__ for r in pipeline_results],
        "summary": build_summary(results, pipeline_results),
    }
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved: {path}")

def build_summary(results: dict, pipeline_results: list) -> dict:
    summary = {"speedups": {}, "throughput_gpu": {}}
    for model in ["efficientnetv2", "bilstm", "vit_b16"]:
        cpu = results.get(model, {}).get("latency", {}).get("cpu_fp32", {}).get("mean_ms")
        gpu = results.get(model, {}).get("latency", {}).get("cuda_fp32", {}).get("mean_ms")
        if cpu and gpu:
            summary["speedups"][model] = round(cpu / gpu, 2)
        gpu_tput = results.get(model, {}).get("throughput", {}).get("cuda_bs32", {}).get("samples_per_second")
        if gpu_tput:
            summary["throughput_gpu"][model] = round(gpu_tput, 1)
    if pipeline_results:
        totals = [r.total_ms for r in pipeline_results]
        summary["pipeline_mean_ms"] = round(float(np.mean(totals)), 1)
        summary["pipeline_p95_ms"] = round(float(np.percentile(totals, 95)), 1)
    return summary
