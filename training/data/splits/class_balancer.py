"""
Class Balancing Utilities
==========================
Weighted sampler factory, oversampling, and undersampling helpers for
handling class imbalance in deepfake / spoof detection datasets.
"""

from __future__ import annotations

import logging
import random
from collections import Counter

import numpy as np
import torch
from torch.utils.data import Dataset, WeightedRandomSampler

logger = logging.getLogger(__name__)


# ── Weighted sampler factory ─────────────────────────────────────────────────

def make_weighted_sampler(
    labels: list[int] | np.ndarray,
    replacement: bool = True,
) -> WeightedRandomSampler:
    """Create a WeightedRandomSampler that equalises class frequencies.

    Args:
        labels: per-sample integer labels.
        replacement: whether to sample with replacement.

    Returns:
        A ``WeightedRandomSampler`` whose per-sample weights invert the
        class frequency so that minority classes are up-weighted.
    """
    labels_arr = np.asarray(labels)
    class_counts = np.bincount(labels_arr)
    class_weights = 1.0 / class_counts.astype(np.float64)
    sample_weights = class_weights[labels_arr]

    logger.info(
        "Class distribution: %s  →  sample-weight range [%.4f, %.4f]",
        dict(zip(range(len(class_counts)), class_counts.tolist())),
        sample_weights.min(),
        sample_weights.max(),
    )

    return WeightedRandomSampler(
        weights=torch.from_numpy(sample_weights).double(),
        num_samples=len(labels_arr),
        replacement=replacement,
    )


# ── Oversampling ─────────────────────────────────────────────────────────────

def oversample_minority(
    paths: list[str],
    labels: list[int],
    target_ratio: float = 1.0,
    seed: int = 42,
) -> tuple[list[str], list[int]]:
    """Duplicate minority-class samples until the desired ratio is reached.

    Args:
        paths: file paths (or any sample identifiers).
        labels: integer labels parallel to *paths*.
        target_ratio: desired minority / majority ratio. 1.0 = balanced.
        seed: random seed for reproducibility.

    Returns:
        (paths, labels) with minority duplicates appended.
    """
    rng = random.Random(seed)
    counts = Counter(labels)
    majority_count = max(counts.values())
    target_count = int(majority_count * target_ratio)

    new_paths, new_labels = list(paths), list(labels)

    for cls, cnt in counts.items():
        if cnt >= target_count:
            continue
        deficit = target_count - cnt
        cls_indices = [i for i, l in enumerate(labels) if l == cls]
        extra = rng.choices(cls_indices, k=deficit)
        for idx in extra:
            new_paths.append(paths[idx])
            new_labels.append(labels[idx])

    logger.info(
        "Oversampled: %s → %s",
        dict(counts),
        dict(Counter(new_labels)),
    )
    return new_paths, new_labels


# ── Undersampling ────────────────────────────────────────────────────────────

def undersample_majority(
    paths: list[str],
    labels: list[int],
    target_ratio: float = 1.0,
    seed: int = 42,
) -> tuple[list[str], list[int]]:
    """Reduce majority-class samples to achieve the desired ratio.

    Args:
        paths: file paths.
        labels: integer labels parallel to *paths*.
        target_ratio: desired minority / majority ratio. 1.0 = balanced.
        seed: random seed.

    Returns:
        (paths, labels) with majority samples trimmed.
    """
    rng = random.Random(seed)
    counts = Counter(labels)
    minority_count = min(counts.values())
    target_count = int(minority_count / target_ratio) if target_ratio > 0 else minority_count

    new_paths: list[str] = []
    new_labels: list[int] = []

    for cls in sorted(counts):
        cls_indices = [i for i, l in enumerate(labels) if l == cls]
        keep = min(len(cls_indices), target_count)
        sampled = rng.sample(cls_indices, keep)
        for idx in sampled:
            new_paths.append(paths[idx])
            new_labels.append(labels[idx])

    logger.info(
        "Undersampled: %s → %s",
        dict(counts),
        dict(Counter(new_labels)),
    )
    return new_paths, new_labels


# ── Introspection helper ────────────────────────────────────────────────────

def log_class_distribution(labels: list[int] | np.ndarray, name: str = "") -> dict[int, int]:
    """Log and return class counts."""
    counts = Counter(int(l) for l in labels)
    logger.info("Class distribution%s: %s", f" ({name})" if name else "", dict(counts))
    return dict(counts)
