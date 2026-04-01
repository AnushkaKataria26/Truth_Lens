"""
LoRA Continual Fine-Tuning Script
====================================
Applies LoRA adapters (via PEFT) to query/value layers of a pretrained model
and trains with mixed replay-buffer batches for catastrophic-forgetting
prevention.

Usage:
    python -m training.models.lora_trainer \
        --base-model saved_models/efficientnetv2/best_model.pt \
        --new-data-csv new_data.csv \
        --replay-buffer replay_buffer.json
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
from peft import LoraConfig, get_peft_model, TaskType
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.utils.data import DataLoader, ConcatDataset, Subset
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

import timm

from training.config import LOGS_DIR, MODELS_DIR, LoRATrainingConfig, VisualTrainingConfig
from training.data.visual.augmentation import get_train_transforms, get_val_transforms
from training.data.visual.dataset import FaceForensicsDataset
from training.eval.metrics import compute_metrics
from training.models.replay_buffer import ReplayBuffer

logger = logging.getLogger(__name__)


class LoRATrainer:
    """LoRA continual-learning trainer.

    Wraps any timm model with PEFT LoRA adapters and trains on a mix of
    new data + replay-buffer samples.
    """

    def __init__(
        self,
        base_model_path: str | Path,
        new_samples: list[tuple[Path, int]],
        replay_buffer_path: str | Path | None = None,
        val_samples: list[tuple[Path, int]] | None = None,
        lora_config: LoRATrainingConfig | None = None,
        visual_config: VisualTrainingConfig | None = None,
    ):
        self.lora_cfg = lora_config or LoRATrainingConfig()
        self.vis_cfg = visual_config or VisualTrainingConfig()
        self.device = torch.device(self.vis_cfg.device if torch.cuda.is_available() else "cpu")

        self.new_samples = new_samples
        self.val_samples = val_samples

        # ── Load base model from checkpoint
        self.model = self._load_base_model(base_model_path)

        # ── Apply LoRA adapters
        peft_config = LoraConfig(
            r=self.lora_cfg.lora_r,
            lora_alpha=self.lora_cfg.lora_alpha,
            lora_dropout=self.lora_cfg.lora_dropout,
            target_modules=self.lora_cfg.target_modules,
            bias="none",
        )
        self.model = get_peft_model(self.model, peft_config)
        self.model.to(self.device)
        self.model.print_trainable_parameters()

        # ── Replay buffer
        self.replay_buffer: ReplayBuffer | None = None
        if replay_buffer_path and Path(replay_buffer_path).exists():
            self.replay_buffer = ReplayBuffer.load(replay_buffer_path)

        # ── Optimiser (only LoRA params are trainable)
        self.optimizer = AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=self.lora_cfg.learning_rate,
        )

        self.criterion = nn.CrossEntropyLoss()
        self.scaler = GradScaler(enabled=self.vis_cfg.mixed_precision)

        self.log_dir = LOGS_DIR / "lora"
        self.writer = SummaryWriter(log_dir=str(self.log_dir))

        self.ckpt_dir = MODELS_DIR / "lora"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)

    # ── public API ───────────────────────────────────────────────────────
    def train(self) -> dict:
        """Run LoRA fine-tuning with replay mixing."""
        train_loader = self._make_mixed_loader()
        val_loader = self._make_val_loader() if self.val_samples else None

        best_metrics: dict = {}
        for epoch in range(1, self.lora_cfg.epochs + 1):
            train_loss = self._train_epoch(train_loader, epoch)
            self.writer.add_scalar("lora/train_loss", train_loss, epoch)
            logger.info("LoRA Epoch %d/%d  loss=%.4f", epoch, self.lora_cfg.epochs, train_loss)

            if val_loader:
                metrics = self._validate(val_loader, epoch)
                self.writer.add_scalar("lora/val_auc", metrics.get("auc_roc", 0.0), epoch)
                best_metrics = metrics

        # Save adapter weights
        adapter_path = self.ckpt_dir / "lora_adapter"
        self.model.save_pretrained(str(adapter_path))
        logger.info("LoRA adapter saved → %s", adapter_path)

        self.writer.close()
        return best_metrics

    # ── loops ────────────────────────────────────────────────────────────
    def _train_epoch(self, loader: DataLoader, epoch: int) -> float:
        self.model.train()
        total_loss = 0.0
        n = 0

        for images, labels in tqdm(loader, desc=f"LoRA [{epoch}]"):
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            self.optimizer.zero_grad(set_to_none=True)
            with autocast(enabled=self.vis_cfg.mixed_precision):
                logits = self.model(images)
                loss = self.criterion(logits, labels)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total_loss += loss.item()
            n += 1

        return total_loss / max(n, 1)

    @torch.no_grad()
    def _validate(self, loader: DataLoader, epoch: int) -> dict:
        self.model.eval()
        all_preds, all_labels = [], []

        for images, labels in loader:
            images = images.to(self.device, non_blocking=True)
            with autocast(enabled=self.vis_cfg.mixed_precision):
                logits = self.model(images)
            probs = torch.softmax(logits, dim=1)[:, 1]
            all_preds.extend(probs.cpu().tolist())
            all_labels.extend(labels.tolist())

        return compute_metrics(all_labels, all_preds)

    # ── helpers ──────────────────────────────────────────────────────────
    def _load_base_model(self, ckpt_path: str | Path) -> nn.Module:
        """Load a timm model from a training checkpoint."""
        checkpoint = torch.load(ckpt_path, map_location="cpu")
        config = checkpoint.get("config", {})
        model_name = config.get("model_name", self.vis_cfg.model_name)
        num_classes = config.get("num_classes", self.vis_cfg.num_classes)

        model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
        model.load_state_dict(checkpoint["model_state_dict"])
        return model

    def _make_mixed_loader(self) -> DataLoader:
        """Create a DataLoader that mixes new data with replay-buffer samples."""
        transform = get_train_transforms(self.vis_cfg.input_size)
        new_dataset = FaceForensicsDataset(self.new_samples, transforms=transform)

        if self.replay_buffer and self.replay_buffer.size > 0:
            # Sample replay items proportional to config ratio
            n_replay = int(len(new_dataset) * self.lora_cfg.replay_buffer_ratio)
            replay_samples = self.replay_buffer.sample_balanced(n_replay)

            # Convert replay buffer samples to (Path, label) tuples
            replay_tuples = [(Path(s.path), s.label) for s in replay_samples]
            replay_dataset = FaceForensicsDataset(replay_tuples, transforms=transform)
            combined = ConcatDataset([new_dataset, replay_dataset])
        else:
            combined = new_dataset

        return DataLoader(
            combined,
            batch_size=self.lora_cfg.batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True,
            drop_last=True,
        )

    def _make_val_loader(self) -> DataLoader | None:
        if self.val_samples is None:
            return None
        transform = get_val_transforms(self.vis_cfg.input_size)
        dataset = FaceForensicsDataset(self.val_samples, transforms=transform)
        return DataLoader(dataset, batch_size=self.lora_cfg.batch_size, shuffle=False, num_workers=2)


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA continual fine-tuning")
    parser.add_argument("--base-model", required=True, help="Path to base model checkpoint")
    parser.add_argument("--new-data-dir", type=Path, required=True, help="Directory with new training samples")
    parser.add_argument("--replay-buffer", default=None, help="Path to replay buffer JSON")
    parser.add_argument("--val-data-dir", type=Path, default=None, help="Validation data dir")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    from training.data.splits.generate_splits import generate_visual_splits
    new_splits = generate_visual_splits(args.new_data_dir)
    val_samples = None
    if args.val_data_dir:
        val_splits = generate_visual_splits(args.val_data_dir)
        val_samples = val_splits["val"]

    trainer = LoRATrainer(
        base_model_path=args.base_model,
        new_samples=new_splits["train"],
        replay_buffer_path=args.replay_buffer,
        val_samples=val_samples,
    )
    result = trainer.train()
    logger.info("LoRA training complete: %s", result)


if __name__ == "__main__":
    main()
