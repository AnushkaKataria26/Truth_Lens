import torch

def warmup_model(model, input_shape: tuple, device: torch.device,
                 n_runs: int = 10, batch_size: int = 1):
    model.eval()
    dummy_input = torch.randn(batch_size, *input_shape).to(device)

    with torch.no_grad():
        for _ in range(n_runs):
            _ = model(dummy_input)

    # Synchronize GPU before starting measurement
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    print(f"Warmup complete: {n_runs} runs on {device}")

def warmup_onnx_session(session, input_name: str, input_shape: tuple, n_runs: int = 10):
    import numpy as np
    dummy = np.random.randn(1, *input_shape).astype(np.float32)
    for _ in range(n_runs):
        session.run(None, {input_name: dummy})
    print(f"ONNX warmup complete: {n_runs} runs")
