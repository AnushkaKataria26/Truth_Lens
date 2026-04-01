"""
Audio Dataset — PyTorch Dataset for Synthetic-Audio Detection
==============================================================
Loads preprocessed mel-spectrogram .npy files (saved as dicts by the ASV
preprocessor) with optional waveform-level augmentation applied before
mel extraction, or spectrogram-level augmentation applied post-load.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, WeightedRandomSampler


class AudioDataset(Dataset):
    """Mel-spectrogram dataset for audio classification.

    Each ``.npy`` file is a dict with keys:
        ``{"mel": ndarray, "label": int, "system_id": str}``

    Args:
        samples: list of ``(npy_path, label)`` tuples where
                 label is 0 (bonafide) or 1 (spoof).
        augment: whether to apply spectrogram augmentation (freq/time masking).
    """

    def __init__(
        self,
        samples: list[tuple[Path, int]],
        augment: bool = False,
    ):
        self.samples = samples
        self.augment = augment

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        path, label = self.samples[idx]
        data = np.load(str(path), allow_pickle=True).item()
        spec = data["mel"]  # (n_mels, T), float32 in [0, 1]

        if self.augment:
            spec = self._spec_augment(spec)

        # Add channel dimension: (1, n_mels, T)
        tensor = torch.from_numpy(spec).unsqueeze(0).float()
        return tensor, label

    @staticmethod
    def _spec_augment(
        spec: np.ndarray,
        num_freq_masks: int = 2,
        freq_mask_size: int = 15,
        num_time_masks: int = 2,
        time_mask_size: int = 20,
    ) -> np.ndarray:
        """Apply SpecAugment: frequency and time masking."""
        spec = spec.copy()
        n_mels, n_frames = spec.shape

        # Frequency masks
        for _ in range(num_freq_masks):
            f = np.random.randint(1, min(freq_mask_size, n_mels))
            f0 = np.random.randint(0, n_mels - f)
            spec[f0 : f0 + f, :] = 0.0

        # Time masks
        for _ in range(num_time_masks):
            t = np.random.randint(1, min(time_mask_size, n_frames))
            t0 = np.random.randint(0, n_frames - t)
            spec[:, t0 : t0 + t] = 0.0

        return spec


def build_audio_weighted_sampler(
    samples: list[tuple[Path, int]],
) -> WeightedRandomSampler:
    """Create a WeightedRandomSampler for class balance."""
    labels = np.array([s[1] for s in samples])
    class_counts = np.bincount(labels)
    class_weights = 1.0 / class_counts
    sample_weights = [class_weights[l] for l in labels]
    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True,
    )
