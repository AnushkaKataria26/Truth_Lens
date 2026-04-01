"""
Visual Dataset — PyTorch Dataset for Deepfake / Manipulation Detection
=======================================================================
Loads preprocessed face-crop images using PIL, applies Albumentations
transforms, and provides a weighted sampler factory for class balancing.

The dataset takes a pre-built list of ``(image_path, label)`` tuples rather
than reading from CSV, so it integrates directly with the video-level split
generator (which prevents train/test leakage).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from torch.utils.data import Dataset, WeightedRandomSampler


class FaceForensicsDataset(Dataset):
    """Image dataset for deepfake detection.

    Args:
        samples: list of ``(image_path, label)`` tuples where
                 label is 0 (real) or 1 (fake).
        transforms: optional Albumentations transform pipeline.
    """

    def __init__(
        self,
        samples: list[tuple[Path, int]],
        transforms=None,
    ):
        self.samples = samples
        self.transforms = transforms

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, label = self.samples[idx]
        image = np.array(Image.open(img_path).convert("RGB"))

        if self.transforms:
            augmented = self.transforms(image=image)
            image = augmented["image"]

        return image, label


def build_weighted_sampler(
    samples: list[tuple[Path, int]],
) -> WeightedRandomSampler:
    """Create a WeightedRandomSampler that equalises class frequencies.

    Args:
        samples: list of ``(image_path, label)`` tuples.

    Returns:
        A ``WeightedRandomSampler`` that up-weights the minority class.
    """
    labels = [s[1] for s in samples]
    class_counts = np.bincount(labels)
    class_weights = 1.0 / class_counts
    sample_weights = [class_weights[label] for label in labels]
    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )
