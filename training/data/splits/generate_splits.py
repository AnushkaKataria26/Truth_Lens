"""
Train / Val / Test Split Generator
====================================
Generates deterministic, stratified splits for visual deepfake datasets.

CRITICAL: splits are performed at the **VIDEO level**, not the frame level.
If frames from the same video appear in both train and test → data leakage.
All frames from a given video are assigned to exactly one split.

Usage:
    python -m training.data.splits.generate_splits
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

from training.config import PROCESSED_DIR, VisualTrainingConfig

logger = logging.getLogger(__name__)


def generate_visual_splits(
    processed_dir: Path,
    config: VisualTrainingConfig | None = None,
) -> dict[str, list[tuple[Path, int]]]:
    """Create stratified train / val / test splits at the video level.

    Frame files are expected to follow the naming convention produced by
    the FF++ preprocessor: ``{video_stem}_{frame_idx}.jpg``.

    Args:
        processed_dir: root of preprocessed images (contains ``real/`` and
                       ``fake/`` sub-directories).
        config: visual training configuration for ratios and seed.

    Returns:
        dict mapping split name → list of ``(image_path, label)`` tuples.
    """
    config = config or VisualTrainingConfig()

    # ── Collect all images and group by video stem
    all_images = list(processed_dir.glob("**/*.jpg"))
    if not all_images:
        logger.warning("No .jpg files found under %s", processed_dir)
        return {"train": [], "val": [], "test": []}

    video_groups: dict[str, dict] = {}
    for img_path in all_images:
        # Frame filenames: {video_stem}_{frame_idx}.jpg
        # Remove the trailing frame index to recover the video stem
        video_stem = "_".join(img_path.stem.split("_")[:-1])
        label = 0 if "real" in img_path.parts else 1

        if video_stem not in video_groups:
            video_groups[video_stem] = {"paths": [], "label": label}
        video_groups[video_stem]["paths"].append(img_path)

    video_stems = list(video_groups.keys())
    labels = [video_groups[v]["label"] for v in video_stems]

    # ── Stratified split at video level
    train_stems, temp_stems, _, temp_labels = train_test_split(
        video_stems,
        labels,
        test_size=(config.val_ratio + config.test_ratio),
        stratify=labels,
        random_state=config.seed,
    )

    relative_test = config.test_ratio / (config.val_ratio + config.test_ratio)
    val_stems, test_stems = train_test_split(
        temp_stems,
        temp_labels,
        test_size=relative_test,
        stratify=temp_labels,
        random_state=config.seed,
    )

    # ── Expand video stems back to frame-level samples
    def stems_to_samples(stems: list[str]) -> list[tuple[Path, int]]:
        samples: list[tuple[Path, int]] = []
        for stem in stems:
            group = video_groups[stem]
            for path in group["paths"]:
                samples.append((path, group["label"]))
        return samples

    splits = {
        "train": stems_to_samples(train_stems),
        "val": stems_to_samples(val_stems),
        "test": stems_to_samples(test_stems),
    }

    # ── Log split statistics
    for split_name, samples in splits.items():
        real_count = sum(1 for _, l in samples if l == 0)
        fake_count = sum(1 for _, l in samples if l == 1)
        logger.info(
            "%s: %d samples | real=%d fake=%d",
            split_name, len(samples), real_count, fake_count,
        )

    return splits


def generate_audio_splits(
    processed_dir: Path,
    config: VisualTrainingConfig | None = None,
) -> dict[str, list[tuple[Path, int]]]:
    """Create stratified splits for audio .npy files.

    Audio files don't have the same video-level leakage concern, so
    splitting is done at the file level.

    Args:
        processed_dir: directory containing per-class sub-dirs of .npy files.
        config: config for ratios and seed.

    Returns:
        dict mapping split name → list of ``(npy_path, label)`` tuples.
    """
    config = config or VisualTrainingConfig()

    all_files: list[tuple[Path, int]] = []
    for class_dir in sorted(processed_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        label = int(class_dir.name)
        for f in class_dir.glob("*.npy"):
            all_files.append((f, label))

    if not all_files:
        return {"train": [], "val": [], "test": []}

    paths, labels = zip(*all_files)
    paths_list = list(paths)
    labels_list = list(labels)

    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        paths_list, labels_list,
        test_size=(config.val_ratio + config.test_ratio),
        stratify=labels_list,
        random_state=config.seed,
    )

    relative_test = config.test_ratio / (config.val_ratio + config.test_ratio)
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths, temp_labels,
        test_size=relative_test,
        stratify=temp_labels,
        random_state=config.seed,
    )

    return {
        "train": list(zip(train_paths, train_labels)),
        "val": list(zip(val_paths, val_labels)),
        "test": list(zip(test_paths, test_labels)),
    }


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate train/val/test splits")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROCESSED_DIR / "visual" / "ff",
        help="Preprocessed data directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    splits = generate_visual_splits(args.data_dir)
    for name, samples in splits.items():
        print(f"{name}: {len(samples)} samples")


if __name__ == "__main__":
    main()
