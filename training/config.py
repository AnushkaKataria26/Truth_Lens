"""
TruthLens Training — Centralised Configuration
================================================
All training hyperparameters, dataset paths, and hardware settings live here so
that every script in the /training tree imports a single source of truth.
"""

from dataclasses import dataclass, field
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "saved_models"
REGISTRY_DIR = BASE_DIR / "registry"
LOGS_DIR = BASE_DIR / "logs"


# ── Visual: EfficientNetV2-S  ────────────────────────────────────────────────
@dataclass
class VisualTrainingConfig:
    # Dataset
    ff_dataset_path: Path = DATA_DIR / "FaceForensics++"
    casia_dataset_path: Path = DATA_DIR / "CASIA-CMFD"
    processed_path: Path = PROCESSED_DIR / "visual"

    # Model
    model_name: str = "tf_efficientnetv2_s"     # timm model key
    pretrained: bool = True
    num_classes: int = 2                         # real / fake
    input_size: int = 224
    dropout_rate: float = 0.3

    # Training
    epochs: int = 30
    batch_size: int = 32
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    lr_scheduler: str = "cosine"                 # cosine annealing
    warmup_epochs: int = 3
    grad_clip: float = 1.0
    early_stopping_patience: int = 5
    val_interval: int = 1                        # validate every N epochs

    # Class balancing — FF++ is ~50/50 but manipulation types are imbalanced
    use_weighted_sampler: bool = True

    # Splits
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    seed: int = 42

    # Hardware
    device: str = "cuda"                         # maps to ROCm on AMD
    num_workers: int = 4
    pin_memory: bool = True
    mixed_precision: bool = True                 # torch.cuda.amp


# ── Audio: BiLSTM  ───────────────────────────────────────────────────────────
@dataclass
class AudioTrainingConfig:
    # Dataset
    asv_dataset_path: Path = DATA_DIR / "ASVspoof2021"
    processed_path: Path = PROCESSED_DIR / "audio"

    # Features
    sample_rate: int = 16000
    n_mels: int = 128
    n_fft: int = 2048
    hop_length: int = 512
    max_frames: int = 300                        # ~6 s at 16 kHz / 512 hop

    # Model
    input_size: int = 128                        # n_mels
    hidden_size: int = 256
    num_layers: int = 3
    bidirectional: bool = True
    dropout_rate: float = 0.4
    num_classes: int = 2                         # bonafide / spoof

    # Training
    epochs: int = 50
    batch_size: int = 64
    learning_rate: float = 5e-4
    weight_decay: float = 1e-4
    lr_scheduler: str = "plateau"                # ReduceLROnPlateau
    early_stopping_patience: int = 8
    device: str = "cuda"
    num_workers: int = 4
    mixed_precision: bool = True


# ── Visual: ViT-B/16  ────────────────────────────────────────────────────────
@dataclass
class ViTTrainingConfig:
    # Dataset — reuses FF++ + CASIA for pixel-anomaly detection
    processed_path: Path = PROCESSED_DIR / "visual"

    # Model
    model_name: str = "vit_base_patch16_384"     # timm model key
    pretrained: bool = True
    num_classes: int = 2
    input_size: int = 384
    dropout_rate: float = 0.1

    # Training — smaller LR for ViT fine-tuning
    epochs: int = 20
    batch_size: int = 8                          # 384 px is memory-intensive, reduced from 16 to 8 for OOM config
    learning_rate: float = 2e-5
    weight_decay: float = 1e-4
    layer_decay: float = 0.75                    # layer-wise LR decay for ViT
    warmup_epochs: int = 5
    early_stopping_patience: int = 4
    device: str = "cuda"
    num_workers: int = 2
    mixed_precision: bool = True


# ── LoRA Continual Learning  ─────────────────────────────────────────────────
@dataclass
class LoRATrainingConfig:
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: ["query", "value"])
    epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 1e-4
    replay_buffer_ratio: float = 0.20           # 20 % original data per batch
    min_new_samples: int = 50                    # min new samples to trigger fine-tune
    novelty_threshold: float = 0.70              # min novelty score from pattern extractor
