"""
ASVspoof 2021 Preprocessing Pipeline
======================================
Processes ASVspoof 2021 LA partition: loads FLAC audio, resamples to 16 kHz,
extracts log-mel spectrograms (128 mel bins), normalises to [0, 1],
pads/truncates to a fixed frame length, and saves as .npy dicts containing
mel spectrogram + label + system_id metadata.

Input:  FLAC audio files + metadata protocol files
Output: ``.npy`` files with ``{"mel": ..., "label": ..., "system_id": ...}``

Usage:
    python -m training.data.audio.asv_preprocessor
    python -m training.data.audio.asv_preprocessor --split train
"""

import argparse
import logging
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from tqdm import tqdm

from training.config import AudioTrainingConfig

logger = logging.getLogger(__name__)


def preprocess_asv_split(
    asv_root: Path,
    split: str,
    config: AudioTrainingConfig | None = None,
) -> int:
    """Preprocess a single ASVspoof 2021 LA split.

    Args:
        asv_root: root directory of the ASVspoof 2021 dataset.
        split: one of ``"train"``, ``"dev"``, ``"eval"``.
        config: audio training configuration (uses defaults if None).

    Returns:
        Number of files successfully processed.

    The metadata protocol file columns (space-separated, no header):
        speaker_id  file_name  system_id  -  label
    where label is ``bonafide`` or ``spoof``.
    """
    config = config or AudioTrainingConfig()

    audio_dir = asv_root / f"ASVspoof2021_LA_{split}" / "flac"
    meta_file = (
        asv_root / "ASVspoof2021_LA_cm_protocols"
        / f"ASVspoof2021.LA.cm.{split}.trl.txt"
    )

    if not meta_file.exists():
        logger.warning("Protocol file not found: %s", meta_file)
        return 0

    # Parse metadata — space-separated, no header
    meta = pd.read_csv(
        meta_file,
        sep=" ",
        header=None,
        names=["speaker_id", "file_name", "system_id", "dash", "label"],
    )

    output_dir = config.processed_path / split
    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    for _, row in tqdm(meta.iterrows(), total=len(meta), desc=f"ASVspoof {split}"):
        audio_path = audio_dir / f"{row.file_name}.flac"
        if not audio_path.exists():
            continue

        try:
            # Load audio at target sample rate
            waveform, _ = librosa.load(
                str(audio_path), sr=config.sample_rate, mono=True,
            )
        except Exception:
            logger.warning("Failed to load %s", audio_path, exc_info=True)
            continue

        # Extract mel spectrogram
        mel = librosa.feature.melspectrogram(
            y=waveform,
            sr=config.sample_rate,
            n_mels=config.n_mels,
            n_fft=config.n_fft,
            hop_length=config.hop_length,
        )
        mel_db = librosa.power_to_db(mel, ref=np.max)

        # Pad or truncate to fixed length
        if mel_db.shape[1] < config.max_frames:
            pad_width = config.max_frames - mel_db.shape[1]
            mel_db = np.pad(
                mel_db,
                ((0, 0), (0, pad_width)),
                mode="constant",
                constant_values=-80,
            )
        else:
            mel_db = mel_db[:, : config.max_frames]

        # Normalise to [0, 1]
        mel_min = mel_db.min()
        mel_max = mel_db.max()
        mel_normalized = (mel_db - mel_min) / (mel_max - mel_min + 1e-8)

        label = 0 if row.label == "bonafide" else 1

        # Save as dict: mel + label + system_id
        out_path = output_dir / f"{row.file_name}.npy"
        np.save(out_path, {
            "mel": mel_normalized.astype(np.float32),
            "label": label,
            "system_id": row.system_id,
        })
        processed += 1

    logger.info("ASVspoof %s split preprocessed: %d / %d files", split, processed, len(meta))
    return processed


def preprocess_all_splits(
    asv_root: Path,
    config: AudioTrainingConfig | None = None,
) -> dict[str, int]:
    """Preprocess all ASVspoof 2021 LA splits (train, dev, eval)."""
    config = config or AudioTrainingConfig()
    results: dict[str, int] = {}
    for split in ("train", "dev", "eval"):
        results[split] = preprocess_asv_split(asv_root, split, config)
    return results


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess ASVspoof 2021 LA")
    parser.add_argument(
        "--split",
        default="all",
        choices=["all", "train", "dev", "eval"],
        help="Which split to preprocess",
    )
    parser.add_argument(
        "--asv-root",
        type=Path,
        default=None,
        help="Override ASVspoof root directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    config = AudioTrainingConfig()
    root = args.asv_root or config.asv_dataset_path

    if args.split == "all":
        results = preprocess_all_splits(root, config)
        logger.info("All splits done: %s", results)
    else:
        n = preprocess_asv_split(root, args.split, config)
        logger.info("%s: %d files processed", args.split, n)


if __name__ == "__main__":
    main()
