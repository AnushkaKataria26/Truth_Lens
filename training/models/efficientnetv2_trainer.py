"""
EfficientNetV2-S Training Script
==================================
Fine-tunes a timm EfficientNetV2-S model for binary deepfake face detection.
Features: cosine LR schedule with warmup, mixed-precision, gradient clipping,
early stopping, weighted cross-entropy, and model registry integration.

Usage:
    python -m training.models.efficientnetv2_trainer --data-dir data/processed/visual/ff
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from torch.utils.data import DataLoader

import timm
from tqdm import tqdm

from training.config import MODELS_DIR, VisualTrainingConfig
from training.data.visual.augmentation import get_train_transforms, get_val_transforms
from training.data.visual.dataset import FaceForensicsDataset, build_weighted_sampler
from training.eval.metrics import compute_metrics

logger = logging.getLogger(__name__)


# ── Model factory ────────────────────────────────────────────────────────────

def build_efficientnetv2(config: VisualTrainingConfig) -> nn.Module:
    """Create a pretrained EfficientNetV2-S model from timm."""
    model = timm.create_model(
        config.model_name,
        pretrained=config.pretrained,
        num_classes=config.num_classes,
        drop_rate=config.dropout_rate,
    )
    return model


# ── Evaluation helper ────────────────────────────────────────────────────────

@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    mixed_precision: bool = True,
) -> dict[str, float]:
    """Run inference on a loader and return standard metrics (auc, eer, etc.)."""
    model.eval()
    all_preds: list[float] = []
    all_labels: list[int] = []

    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        with autocast(enabled=mixed_precision):
            logits = model(images)
        probs = torch.softmax(logits, dim=1)[:, 1]
        all_preds.extend(probs.cpu().tolist())
        all_labels.extend(labels.tolist())

    metrics = compute_metrics(all_labels, all_preds)
    # Alias for convenience
    metrics["auc"] = metrics["auc_roc"]
    return metrics


# ── Training entry point ─────────────────────────────────────────────────────

def train_efficientnetv2(
    config: VisualTrainingConfig,
    splits: dict[str, list[tuple[Path, int]]],
) -> Path:
    """Full training loop for EfficientNetV2-S.

    Args:
        config: training hyperparameters.
        splits: dict with ``"train"`` and ``"val"`` keys, each a list of
                ``(image_path, label)`` tuples.

    Returns:
        Path to the best checkpoint file.
    """
    device = torch.device(config.device if torch.cuda.is_available() else "cpu")
    model = build_efficientnetv2(config).to(device)

    # ── Loss: weighted cross-entropy for class imbalance
    train_labels = [s[1] for s in splits["train"]]
    real_count = train_labels.count(0)
    fake_count = train_labels.count(1)
    class_weights = torch.tensor([
        len(train_labels) / (2 * max(real_count, 1)),
        len(train_labels) / (2 * max(fake_count, 1)),
    ], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    scaler = GradScaler()

    # ── Warmup + cosine annealing schedule
    warmup_scheduler = LinearLR(
        optimizer, start_factor=0.1, total_iters=config.warmup_epochs,
    )
    cosine_scheduler = CosineAnnealingLR(
        optimizer, T_max=config.epochs - config.warmup_epochs,
    )
    scheduler = SequentialLR(
        optimizer,
        [warmup_scheduler, cosine_scheduler],
        milestones=[config.warmup_epochs],
    )

    # ── Data loaders
    train_dataset = FaceForensicsDataset(
        splits["train"], transforms=get_train_transforms(config.input_size),
    )
    val_dataset = FaceForensicsDataset(
        splits["val"], transforms=get_val_transforms(config.input_size),
    )

    sampler = build_weighted_sampler(splits["train"]) if config.use_weighted_sampler else None
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        sampler=sampler,
        shuffle=(sampler is None),
        num_workers=config.num_workers,
        pin_memory=config.pin_memory,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size * 2,
        shuffle=False,
        num_workers=config.num_workers,
    )

    best_val_auc = 0.0
    patience_counter = 0
    checkpoint_path = MODELS_DIR / "efficientnetv2_best.pth"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Training loop
    for epoch in range(config.epochs):
        model.train()
        train_loss = 0.0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{config.epochs}")
        for images, labels in pbar:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            with autocast(enabled=config.mixed_precision):
                outputs = model(images)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
            scaler.step(optimizer)
            scaler.update()
            train_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        scheduler.step()

        # ── Validation
        val_metrics = evaluate_model(model, val_loader, device, config.mixed_precision)
        avg_loss = train_loss / max(len(train_loader), 1)
        logger.info(
            "Epoch %d/%d | Train Loss: %.4f | Val AUC: %.4f | Val EER: %.4f",
            epoch + 1, config.epochs, avg_loss,
            val_metrics["auc"], val_metrics["eer"],
        )

        # ── Early stopping + checkpointing
        if val_metrics["auc"] > best_val_auc:
            best_val_auc = val_metrics["auc"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_auc": best_val_auc,
                "config": config.__dict__,
            }, checkpoint_path)
            logger.info("Saved best model → %s (AUC=%.4f)", checkpoint_path, best_val_auc)
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience:
                logger.info("Early stopping at epoch %d", epoch + 1)
                break

    # ── Register best checkpoint in model registry
    try:
        from training.registry.model_registry import ModelRegistry
        registry = ModelRegistry()
        registry.register(
            name="efficientnetv2",
            version=f"v{best_val_auc:.4f}",
            model_path=checkpoint_path,
            metrics={"auc_roc": best_val_auc},
            config=config.__dict__,
        )
    except Exception:
        logger.warning("Model registry not available — skipping registration", exc_info=True)

    return checkpoint_path


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Train EfficientNetV2-S")
    parser.add_argument(
        "--data-dir", type=Path, required=True,
        help="Preprocessed visual data directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from training.data.splits.generate_splits import generate_visual_splits
    splits = generate_visual_splits(args.data_dir)

    config = VisualTrainingConfig()
    train_efficientnetv2(config, splits)


if __name__ == "__main__":
    main()
