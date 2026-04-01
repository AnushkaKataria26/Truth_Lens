import timm
import torch
from pathlib import Path

from benchmarking.profiling.latency_profiler import measure_latency
from benchmarking.profiling.throughput_profiler import measure_throughput
from benchmarking.profiling.memory_profiler import measure_memory
from benchmarking.results.results_formatter import print_latency_table, print_memory_profile, print_throughput_table

MODELS_DIR = Path(__file__).parent.parent.parent / "training" / "registry" / "models"
# Create fallback path if needed
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_efficientnetv2(checkpoint_path: Path, device: torch.device) -> torch.nn.Module:
    model = timm.create_model("tf_efficientnetv2_s", pretrained=False, num_classes=2)
    if checkpoint_path.exists():
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        print("WARNING: checkpoint not found, using random weights (DEMO_MODE)")
    return model.to(device).eval()

def print_model_summary(model_name: str, device_name: str, results: dict):
    print(f"\n--- {model_name} on {device_name} Benchmark Complete ---")

def run_efficientnetv2_benchmark(config, results: dict):
    input_shape = config.efficientnetv2_input
    checkpoint = MODELS_DIR / "efficientnetv2_best.pth"
    results["efficientnetv2"] = {"latency": {}, "throughput": {}, "memory": {}}

    for device_str in config.devices:
        device = torch.device(device_str)
        if device_str == "cuda" and not torch.cuda.is_available():
            print(f"Skipping CUDA benchmark — GPU not available")
            continue

        model = load_efficientnetv2(checkpoint, device)
        key = device_str

        # Test both specified precisions if supported
        precision_modes = getattr(config, "precision_modes", ["fp32", "fp16"])
        
        for precision in precision_modes:
            if precision == "fp16" and device_str == "cpu":
                continue  # fp16 not supported on CPU in PyTorch

            lat = measure_latency(model, input_shape, device, config,
                                  "EfficientNetV2-S", precision)
            results["efficientnetv2"]["latency"][f"{key}_{precision}"] = lat.__dict__

            mem = measure_memory(model, input_shape, device,
                                 config.batch_size_latency, "EfficientNetV2-S", precision)
            results["efficientnetv2"]["memory"][f"{key}_{precision}"] = mem.__dict__
            
            # Revert model to specific precision base for next loops if altered
            model = load_efficientnetv2(checkpoint, device)

        for bs in config.throughput_batch_sizes:
            tput = measure_throughput(model, input_shape, device, bs,
                                      config.throughput_duration_seconds, "EfficientNetV2-S")
            results["efficientnetv2"]["throughput"][f"{key}_bs{bs}"] = tput.__dict__

        print_model_summary("EfficientNetV2-S", device_str, results["efficientnetv2"])
