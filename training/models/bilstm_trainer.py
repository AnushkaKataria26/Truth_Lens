"""
BiLSTM Training Script — Synthetic Audio Detection
=====================================================
Trains a BiLSTM with attention pooling for ASVspoof 2021 bonafide/spoof
classification. Uses ReduceLROnPlateau, weighted cross-entropy, GradScaler,
and early stopping by EER (standard for ASVspoof benchmarks).

Usage:
    python -m training.models.bilstm_trainer --data-dir data/processed/audio
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.utils.data import DataLoader

from tqdm import tqdm

from training.config import MODELS_DIR, AudioTrainingConfig
from training.data.audio.dataset import AudioDataset, build_audio_weighted_sampler
from training.eval.metrics import compute_metrics

logger = logging.getLogger(__name__)


# ── Model ────────────────────────────────────────────────────────────────────

class BiLSTMClassifier(nn.Module):
    """BiLSTM with attention pooling for audio classification.

    Input tensor shape: ``(batch, 1, n_mels, max_frames)``.
    The channel dimension is squeezed, then the mel/time axes are transposed
    so the LSTM processes time steps sequentially.
    """

    def __init__(self, config: AudioTrainingConfig):
        super().__init__()
        # Input: (batch, time_steps, n_mels) — treat mel frames as sequence
        self.lstm = nn.LSTM(
            input_size=config.input_size,         # n_mels = 128
            hidden_size=config.hidden_size,       # 256
            num_layers=config.num_layers,         # 3
            batch_first=True,
            bidirectional=config.bidirectional,   # True → output dim = 512
            dropout=config.dropout_rate if config.num_layers > 1 else 0,
        )
        lstm_output_dim = config.hidden_size * (2 if config.bidirectional else 1)

        # Attention mechanism: weighted pooling over time steps
        # Helps model focus on anomalous frames rather than averaging all
        self.attention = nn.Sequential(
            nn.Linear(lstm_output_dim, 128),
            nn.Tanh(),
            nn.Linear(128, 1),
        )

        self.classifier = nn.Sequential(
            nn.Linear(lstm_output_dim, 128),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(128, config.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 1, n_mels, max_frames)
        # squeeze channel → (batch, n_mels, max_frames)
        if x.dim() == 4:
            x = x.squeeze(1)
        # transpose → (batch, max_frames, n_mels)
        x = x.transpose(1, 2)

        lstm_out, _ = self.lstm(x)  # (batch, max_frames, lstm_output_dim)

        # Attention pooling
        attn_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = (attn_weights * lstm_out).sum(dim=1)  # (batch, lstm_output_dim)

        return self.classifier(context)


# ── Evaluation helper ────────────────────────────────────────────────────────

@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    mixed_precision: bool = True,
) -> dict[str, float]:
    """Evaluate BiLSTM on a loader and return metrics dict."""
    model.eval()
    all_preds: list[float] = []
    all_labels: list[int] = []

    for spectrograms, labels in loader:
        spectrograms = spectrograms.to(device, non_blocking=True)
        with autocast(enabled=mixed_precision):
            logits = model(spectrograms)
        probs = torch.softmax(logits, dim=1)[:, 1]
        all_preds.extend(probs.cpu().tolist())
        all_labels.extend(labels.tolist())

    metrics = compute_metrics(all_labels, all_preds)
    metrics["auc"] = metrics["auc_roc"]
    return metrics


# ── Training entry point ─────────────────────────────────────────────────────

def train_bilstm(
    config: AudioTrainingConfig,
    splits: dict[str, list[tuple[Path, int]]],
) -> Path:
    """Full training loop for BiLSTM audio model.

    Args:
        config: audio training hyperparameters.
        splits: dict with ``"train"`` and ``"val"`` keys, each a list of
                ``(npy_path, label)`` tuples.

    Returns:
        Path to the best checkpoint file.
    """
    device = torch.device(config.device if torch.cuda.is_available() else "cpu")
    model = BiLSTMClassifier(config).to(device)

    # ── Loss: ASVspoof is heavily imbalanced (many more spoofs than bonafide)
    train_labels = [s[1] for s in splits["train"]]
    bonafide_count = train_labels.count(0)
    spoof_count = train_labels.count(1)
    class_weights = torch.tensor([
        spoof_count / max(bonafide_count, 1),   # upweight minority bonafide class
        1.0,
    ], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3, verbose=True,
    )
    scaler = GradScaler()

    # ── Data loaders
    train_dataset = AudioDataset(splits["train"], augment=True)
    val_dataset = AudioDataset(splits["val"], augment=False)

    sampler = build_audio_weighted_sampler(splits["train"])
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        sampler=sampler,
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

    best_eer = 1.0
    patience_counter = 0
    checkpoint_path = MODELS_DIR / "bilstm_best.pth"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Training loop
    for epoch in range(config.epochs):
        model.train()
        train_loss = 0.0

        pbar = tqdm(train_loader, desc=f"BiLSTM [{epoch + 1}/{config.epochs}]")
        for spectrograms, labels in pbar:
            spectrograms = spectrograms.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad()

            with autocast(enabled=config.mixed_precision):
                outputs = model(spectrograms)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        avg_train_loss = train_loss / max(len(train_loader), 1)

        # ── Validation — EER is the primary metric for ASVspoof
        val_metrics = evaluate_model(model, val_loader, device, config.mixed_precision)
        scheduler.step(val_metrics["eer"])

        logger.info(
            "Epoch %d/%d | Train Loss: %.4f | Val AUC: %.4f | Val EER: %.4f",
            epoch + 1, config.epochs, avg_train_loss,
            val_metrics["auc"], val_metrics["eer"],
        )

        # ── Save best by lowest EER (standard for ASVspoof benchmark)
        if val_metrics["eer"] < best_eer:
            best_eer = val_metrics["eer"]
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_eer": best_eer,
                "val_auc": val_metrics["auc"],
                "config": config.__dict__,
            }, checkpoint_path)
            logger.info("Saved best model → %s (EER=%.4f)", checkpoint_path, best_eer)
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
            name="bilstm",
            version=f"eer{best_eer:.4f}",
            model_path=checkpoint_path,
            metrics={"eer": best_eer, "auc_roc": val_metrics.get("auc", 0.0)},
            config=config.__dict__,
        )
    except Exception:
        logger.warning("Model registry not available — skipping registration", exc_info=True)

    return checkpoint_path


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Train BiLSTM audio model")
    parser.add_argument(
        "--data-dir", type=Path, required=True,
        help="Preprocessed audio data directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from training.data.splits.generate_splits import generate_audio_splits
    splits = generate_audio_splits(args.data_dir)

    config = AudioTrainingConfig()
    train_bilstm(config, splits)


if __name__ == "__main__":
    main()
