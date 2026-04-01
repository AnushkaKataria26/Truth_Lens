import torch
import numpy as np
from pathlib import Path
from torch.cuda.amp import autocast
from torch.utils.data import DataLoader

from training.config import VisualTrainingConfig, AudioTrainingConfig, ViTTrainingConfig
from training.data.visual.dataset import FaceForensicsDataset
from training.data.audio.dataset import AudioDataset
from training.eval.metrics import compute_auc, compute_eer

# Importers for the model builders we made in 9-11
from training.models.efficientnetv2_trainer import build_efficientnetv2
from training.models.vit_trainer import build_vit
from training.models.bilstm_trainer import BiLSTMClassifier


def build_model(model_type: str, config):
    if model_type == "efficientnetv2":
        return build_efficientnetv2(config)
    elif model_type == "vit":
        return build_vit(config)
    elif model_type == "bilstm":
        return BiLSTMClassifier(config)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

def build_dataset(model_type: str, samples: list, config, augment: bool = False):
    if model_type in ("efficientnetv2", "vit"):
        from training.data.visual.augmentation import get_val_transforms
        return FaceForensicsDataset(samples, get_val_transforms(config.input_size))
    elif model_type == "bilstm":
        return AudioDataset(samples, augment=augment)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def evaluate_model(model: torch.nn.Module, dataloader: DataLoader, device: torch.device) -> dict:
    model.eval()
    all_labels, all_probs = [], []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device, non_blocking=True)
            with autocast(enabled=True):
                outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()
            all_probs.extend(probs)
            all_labels.extend(labels.numpy())

    return {
        "auc": compute_auc(all_labels, all_probs),
        "eer": compute_eer(all_labels, all_probs),
        "accuracy": float(np.mean((np.array(all_probs) > 0.5) == np.array(all_labels))),
    }

def run_test_evaluation(model_type: str, checkpoint_path: Path | str, test_splits: dict, config):
    checkpoint_path = Path(checkpoint_path)
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model = build_model(model_type, config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(config.device)

    test_dataset = build_dataset(model_type, test_splits["test"], config, augment=False)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size * 2, shuffle=False)

    metrics = evaluate_model(model, test_loader, torch.device(config.device))

    print(f"\n{'='*50}")
    print(f"TEST EVALUATION — {model_type.upper()}")
    print(f"AUC:      {metrics['auc']:.4f}")
    print(f"EER:      {metrics['eer']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"{'='*50}\n")

    return metrics

def update_registry_test_metrics(model_id: int, metrics: dict):
    try:
        from training.registry.model_registry import update_test_metrics
        update_test_metrics(model_id, metrics.get("auc", 0.0), metrics.get("eer", 1.0))
    except Exception as e:
        print(f"Failed to update test metrics in registry: {e}")

if __name__ == "__main__":
    import argparse
    from training.data.splits.generate_splits import generate_visual_splits, generate_audio_splits

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-type", required=True, choices=["efficientnetv2", "bilstm", "vit"])
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--model-id", type=int, help="Optional registry model ID to strictly update test metrics")
    args = parser.parse_args()

    # Default configs Based on model type
    if args.model_type == "efficientnetv2":
        config = VisualTrainingConfig()
        splits = generate_visual_splits(args.data_dir)
    elif args.model_type == "vit":
        config = ViTTrainingConfig()
        splits = generate_visual_splits(args.data_dir)
    else:
        config = AudioTrainingConfig()
        splits = generate_audio_splits(args.data_dir)
    
    metrics = run_test_evaluation(args.model_type, args.checkpoint, splits, config)
    if args.model_id is not None:
        update_registry_test_metrics(args.model_id, metrics)
