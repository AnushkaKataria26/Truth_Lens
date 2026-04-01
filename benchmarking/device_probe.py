import torch
import subprocess
import platform
import psutil
from pathlib import Path

def probe_environment() -> dict:
    env = {}

    # System info
    env["os"] = platform.platform()
    env["python_version"] = platform.python_version()
    env["cpu_model"] = get_cpu_model()
    env["cpu_physical_cores"] = psutil.cpu_count(logical=False)
    env["cpu_logical_cores"] = psutil.cpu_count(logical=True)
    env["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)

    # PyTorch info
    env["torch_version"] = torch.__version__
    env["cuda_available"] = torch.cuda.is_available()
    # On AMD with ROCm, torch.cuda.is_available() returns True
    # torch.version.hip is set if ROCm backend is active

    if torch.cuda.is_available():
        env["gpu_count"] = torch.cuda.device_count()
        env["gpu_devices"] = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            env["gpu_devices"].append({
                "index": i,
                "name": props.name,
                "total_memory_gb": round(props.total_memory / (1024**3), 2),
                "compute_capability": f"{props.major}.{props.minor}",
                "multi_processor_count": props.multi_processor_count,
            })

        # Detect ROCm specifically
        hip_version = getattr(torch.version, "hip", None)
        env["rocm_version"] = hip_version if hip_version else "Not detected (CUDA backend)"
        env["backend"] = "ROCm/HIP" if hip_version else "CUDA"

        # rocm-smi output for AMD GPU details
        try:
            rocm_smi = subprocess.run(
                ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
                capture_output=True, text=True, timeout=5,
            )
            env["rocm_smi_output"] = rocm_smi.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            env["rocm_smi_output"] = "rocm-smi not available"
    else:
        env["gpu_count"] = 0
        env["gpu_devices"] = []
        env["rocm_version"] = "N/A"
        env["backend"] = "CPU only"

    # ONNX Runtime providers
    try:
        import onnxruntime as ort
        env["onnxruntime_version"] = ort.__version__
        env["onnxruntime_providers"] = ort.get_available_providers()
    except ImportError:
        env["onnxruntime_version"] = "not installed"
        env["onnxruntime_providers"] = []

    return env

def get_cpu_model() -> str:
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ["cat", "/proc/cpuinfo"],
                capture_output=True, text=True,
            )
            for line in result.stdout.split("\n"):
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"

def print_environment(env: dict):
    print("\n" + "="*60)
    print("TRUTHLENS — AMD GPU BENCHMARK ENVIRONMENT")
    print("="*60)
    print(f"OS:              {env['os']}")
    print(f"CPU:             {env['cpu_model']}")
    print(f"CPU Cores:       {env['cpu_physical_cores']} physical / {env['cpu_logical_cores']} logical")
    print(f"RAM:             {env['ram_total_gb']} GB")
    print(f"PyTorch:         {env['torch_version']}")
    print(f"Backend:         {env['backend']}")
    print(f"ROCm Version:    {env['rocm_version']}")
    if env["gpu_devices"]:
        for gpu in env["gpu_devices"]:
            print(f"GPU [{gpu['index']}]:         {gpu['name']} | {gpu['total_memory_gb']} GB VRAM")
    print(f"ONNX Runtime:    {env['onnxruntime_version']}")
    print("="*60 + "\n")
