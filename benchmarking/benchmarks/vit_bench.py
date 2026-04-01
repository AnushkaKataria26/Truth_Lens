import torch
from pathlib import Path

from training.config import ViTTrainingConfig
from training.models.vit_trainer import build_vit

from benchmarking.profiling.latency_profiler import measure_latency
from benchmarking.profiling.throughput_profiler import measure_throughput
from benchmarking.profiling.memory_profiler import measure_memory

MODELS_DIR = Path(__file__).parent.parent.parent / "training" / "registry" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_vit(checkpoint_path: Path, device: torch.device) -> torch.nn.Module:
    train_cfg = ViTTrainingConfig(pretrained=False)
    model = build_vit(train_cfg)
    if checkpoint_path.exists():
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        print("WARNING: checkpoint not found, using random weights (DEMO_MODE)")
    return model.to(device).eval()

def print_model_summary(model_name: str, device_name: str, results: dict):
    print(f"\n--- {model_name} on {device_name} Benchmark Complete ---")

def run_vit_benchmark(config, results: dict):
    input_shape = config.vit_input
    checkpoint = MODELS_DIR / "vit_b16_best.pth"
    results["vit_b16"] = {"latency": {}, "throughput": {}, "memory": {}}

    for device_str in config.devices:
        device = torch.device(device_str)
        if device_str == "cuda" and not torch.cuda.is_available():
            print(f"Skipping CUDA benchmark — GPU not available")
            continue

        model = load_vit(checkpoint, device)
        key = device_str

        precision_modes = getattr(config, "precision_modes", ["fp32", "fp16"])
        
        for precision in precision_modes:
            if precision == "fp16" and device_str == "cpu":
                continue

            lat = measure_latency(model, input_shape, device, config,
                                  "ViT-B/16", precision)
            results["vit_b16"]["latency"][f"{key}_{precision}"] = lat.__dict__

            mem = measure_memory(model, input_shape, device,
                                 config.batch_size_latency, "ViT-B/16", precision)
            results["vit_b16"]["memory"][f"{key}_{precision}"] = mem.__dict__
            
            model = load_vit(checkpoint, device)

        # Cap max batch size aggressively because ViT causes OOM readily
        safe_throughput_batch_sizes = [b for b in config.throughput_batch_sizes if b <= 8]
        if not safe_throughput_batch_sizes:
            safe_throughput_batch_sizes = [1]

        for bs in safe_throughput_batch_sizes:
            tput = measure_throughput(model, input_shape, device, bs,
                                      config.throughput_duration_seconds, "ViT-B/16")
            results["vit_b16"]["throughput"][f"{key}_bs{bs}"] = tput.__dict__

        print_model_summary("ViT-B/16", device_str, results["vit_b16"])
