import torch
from pathlib import Path

from training.config import AudioTrainingConfig
from training.models.bilstm_trainer import BiLSTMClassifier

from benchmarking.profiling.latency_profiler import measure_latency
from benchmarking.profiling.throughput_profiler import measure_throughput
from benchmarking.profiling.memory_profiler import measure_memory

MODELS_DIR = Path(__file__).parent.parent.parent / "training" / "registry" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_bilstm(checkpoint_path: Path, device: torch.device) -> torch.nn.Module:
    train_cfg = AudioTrainingConfig()
    model = BiLSTMClassifier(train_cfg)
    if checkpoint_path.exists():
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        print("WARNING: checkpoint not found, using random weights (DEMO_MODE)")
    return model.to(device).eval()

def print_model_summary(model_name: str, device_name: str, results: dict):
    print(f"\n--- {model_name} on {device_name} Benchmark Complete ---")

def run_bilstm_benchmark(config, results: dict):
    input_shape = config.bilstm_input
    checkpoint = MODELS_DIR / "bilstm_best.pth"
    results["bilstm"] = {"latency": {}, "throughput": {}, "memory": {}}

    for device_str in config.devices:
        device = torch.device(device_str)
        if device_str == "cuda" and not torch.cuda.is_available():
            print(f"Skipping CUDA benchmark — GPU not available")
            continue

        model = load_bilstm(checkpoint, device)
        key = device_str

        precision_modes = getattr(config, "precision_modes", ["fp32", "fp16"])
        
        for precision in precision_modes:
            if precision == "fp16" and device_str == "cpu":
                continue

            lat = measure_latency(model, input_shape, device, config,
                                  "BiLSTM", precision)
            results["bilstm"]["latency"][f"{key}_{precision}"] = lat.__dict__

            mem = measure_memory(model, input_shape, device,
                                 config.batch_size_latency, "BiLSTM", precision)
            results["bilstm"]["memory"][f"{key}_{precision}"] = mem.__dict__
            
            model = load_bilstm(checkpoint, device)

        for bs in config.throughput_batch_sizes:
            tput = measure_throughput(model, input_shape, device, bs,
                                      config.throughput_duration_seconds, "BiLSTM")
            results["bilstm"]["throughput"][f"{key}_bs{bs}"] = tput.__dict__

        print_model_summary("BiLSTM", device_str, results["bilstm"])
