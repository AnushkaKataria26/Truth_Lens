"""
ViT-B/16 Training Script — Pixel Anomaly Detection
=====================================================
Fine-tunes a ViT-B/16 model (via timm) for binary deepfake/manipulation
detection at 384 px. Uses layer-wise learning rate decay to preserve pretrained
representations, gradient accumulation (4 steps) for effective batch size 64,
and standard cosine warmup scheduling.

Usage:
    python -m training.models.vit_trainer --data-dir data/processed/visual/ff
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

from training.config import MODELS_DIR, ViTTrainingConfig
from training.data.visual.augmentation import get_train_transforms, get_val_transforms
from training.data.visual.dataset import FaceForensicsDataset, build_weighted_sampler
from training.eval.metrics import compute_metrics

logger = logging.getLogger(__name__)


# ── Model factory ────────────────────────────────────────────────────────────

def build_vit(config: ViTTrainingConfig) -> nn.Module:
    """Create a pretrained ViT-B/16 model from timm."""
    model = timm.create_model(
        config.model_name,
        pretrained=config.pretrained,
        num_classes=config.num_classes,
        img_size=config.input_size,
        drop_rate=config.dropout_rate,
    )
    return model


# ── Layer-wise LR decay ─────────────────────────────────────────────────────

def get_layer_wise_lr_params(
    model: nn.Module,
    base_lr: float,
    layer_decay: float,
    num_layers: int = 12,
) -> list[dict]:
    """Build parameter groups with layer-wise LR decay for ViT-B/16.

    ViT-B/16 has 12 transformer blocks. Each block ``i`` gets
    ``base_lr * (layer_decay ** (num_layers - i))``.
    Patch embedding / cls token get the lowest LR; the classification head
    gets the full ``base_lr``.

    Args:
        model: timm ViT model.
        base_lr: base learning rate for the head.
        layer_decay: multiplicative decay per layer (e.g. 0.75).
        num_layers: number of transformer blocks (12 for ViT-B).

    Returns:
        List of parameter-group dicts suitable for ``AdamW``.
    """
    param_groups: list[dict] = []

    # Track which params are assigned to avoid duplicates
    assigned: set[str] = set()

    # Embeddings — lowest LR
    embed_params = []
    for name, param in model.named_parameters():
        if "patch_embed" in name or "cls_token" in name or "pos_embed" in name:
            embed_params.append(param)
            assigned.add(name)
    if embed_params:
        param_groups.append({
            "params": embed_params,
            "lr": base_lr * (layer_decay ** num_layers),
        })

    # Transformer blocks
    for i in range(num_layers):
        layer_params = []
        layer_lr = base_lr * (layer_decay ** (num_layers - i))
        for name, param in model.named_parameters():
            if f"blocks.{i}." in name and name not in assigned:
                layer_params.append(param)
                assigned.add(name)
        if layer_params:
            param_groups.append({"params": layer_params, "lr": layer_lr})

    # Head — full LR
    head_params = []
    for name, param in model.named_parameters():
        if name not in assigned:
            head_params.append(param)
            assigned.add(name)
    if head_params:
        param_groups.append({"params": head_params, "lr": base_lr})

    return param_groups


# ── Evaluation helper ────────────────────────────────────────────────────────

@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    mixed_precision: bool = True,
) -> dict[str, float]:
    """Evaluate ViT on a loader and return metrics dict."""
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
    metrics["auc"] = metrics["auc_roc"]
    return metrics


# ── Training entry point ─────────────────────────────────────────────────────

def train_vit(
    config: ViTTrainingConfig,
    splits: dict[str, list[tuple[Path, int]]],
    accumulate_steps: int = 4,
) -> Path:
    """Full training loop for ViT-B/16 with gradient accumulation.

    Args:
        config: ViT training hyperparameters.
        splits: dict with ``"train"`` and ``"val"`` keys.
        accumulate_steps: gradient accumulation steps to simulate a larger
                         effective batch size (default 4 × 16 = 64).

    Returns:
        Path to the best checkpoint file.
    """
    device = torch.device(config.device if torch.cuda.is_available() else "cpu")
    model = build_vit(config).to(device)

    # ── Loss: weighted cross-entropy
    train_labels = [s[1] for s in splits["train"]]
    real_count = train_labels.count(0)
    fake_count = train_labels.count(1)
    class_weights = torch.tensor([
        len(train_labels) / (2 * max(real_count, 1)),
        len(train_labels) / (2 * max(fake_count, 1)),
    ], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # ── Optimizer with layer-wise LR decay
    param_groups = get_layer_wise_lr_params(
        model, config.learning_rate, config.layer_decay,
    )
    optimizer = AdamW(param_groups, weight_decay=config.weight_decay)
    scaler = GradScaler()

    # ── Warmup + cosine schedule
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

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,          # 16
        shuffle=True,
        num_workers=config.num_workers,
        pin_memory=True,
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
    checkpoint_path = MODELS_DIR / "vit_best.pth"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Training loop with gradient accumulation
    for epoch in range(config.epochs):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        pbar = tqdm(train_loader, desc=f"ViT [{epoch + 1}/{config.epochs}]")
        for batch_idx, (images, labels) in enumerate(pbar):
            images, labels = images.to(device), labels.to(device)

            with autocast(enabled=config.mixed_precision):
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss = loss / accumulate_steps        # scale for accumulation

            scaler.scale(loss).backward()

            # Step every accumulate_steps batches
            if (batch_idx + 1) % accumulate_steps == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()

            train_loss += loss.item() * accumulate_steps  # unscale for logging
            pbar.set_postfix(loss=f"{loss.item() * accumulate_steps:.4f}")

        # Flush any remaining accumulated gradients
        if (batch_idx + 1) % accumulate_steps != 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

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

    # ── Register in model registry
    try:
        from training.registry.model_registry import ModelRegistry
        registry = ModelRegistry()
        registry.register(
            name="vit_b16",
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
    parser = argparse.ArgumentParser(description="Train ViT-B/16")
    parser.add_argument(
        "--data-dir", type=Path, required=True,
        help="Preprocessed visual data directory",
    )
    parser.add_argument(
        "--accumulate", type=int, default=8,
        help="Gradient accumulation steps (default: 8 → effective batch=64)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from training.data.splits.generate_splits import generate_visual_splits
    splits = generate_visual_splits(args.data_dir)

    config = ViTTrainingConfig()
    train_vit(config, splits, accumulate_steps=args.accumulate)


if __name__ == "__main__":
    main()
