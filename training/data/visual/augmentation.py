"""
Visual Augmentation Strategies
================================
Albumentations-based augmentation pipelines for deepfake / manipulation
detection training.

Training augmentation — aggressive for deepfake robustness.
Validation/test — no augmentation (only resize + normalize).

JPEG compression augmentation is critical — deepfakes are often detected
via compression artefacts; augmenting with compression improves generalisation.
"""

from __future__ import annotations

import albumentations as A
from albumentations.pytorch import ToTensorV2


def get_train_transforms(input_size: int = 224) -> A.Compose:
    """Aggressive augmentation pipeline for training.

    Includes transforms that simulate social-media post-processing artefacts
    (JPEG compression, blur, noise) which are critical for generalisation in
    deepfake detection.
    """
    return A.Compose([
        A.Resize(input_size, input_size),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(
            brightness_limit=0.2,
            contrast_limit=0.2,
            p=0.5,
        ),
        A.GaussNoise(var_limit=(10, 50), p=0.3),
        # JPEG compression augmentation is critical — deepfakes are often
        # detected via compression artifacts; augmenting improves generalization
        A.ImageCompression(quality_lower=60, quality_upper=100, p=0.5),
        A.GaussianBlur(blur_limit=(3, 7), p=0.3),
        A.CoarseDropout(
            max_holes=8,
            max_height=16,
            max_width=16,
            p=0.3,
        ),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
        ToTensorV2(),
    ])


def get_val_transforms(input_size: int = 224) -> A.Compose:
    """Minimal deterministic pipeline for validation / test.

    Only resize + normalise — no stochastic augmentations.
    """
    return A.Compose([
        A.Resize(input_size, input_size),
        A.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
        ToTensorV2(),
    ])


def get_tta_transforms(input_size: int = 224) -> list[A.Compose]:
    """Test-Time Augmentation variants for inference ensembling.

    Returns a list of deterministic transform pipelines whose predictions
    can be averaged for more robust results.
    """
    base_norm = [
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ]
    return [
        # Original
        A.Compose([A.Resize(input_size, input_size), *base_norm]),
        # Horizontal flip
        A.Compose([A.Resize(input_size, input_size), A.HorizontalFlip(p=1.0), *base_norm]),
        # Slight crop
        A.Compose([
            A.RandomResizedCrop(height=input_size, width=input_size, scale=(0.9, 1.0)),
            *base_norm,
        ]),
    ]
