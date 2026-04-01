"""
Audio Augmentation Strategies
==============================
Waveform-level augmentations for synthetic-audio detection training.
Each augmentation is applied independently with a configurable probability.

Includes: Gaussian noise, time stretch, pitch shift, and room reverb
(FIR impulse approximation).
"""

from __future__ import annotations

import librosa
import numpy as np


# ── Individual augmentation functions ────────────────────────────────────────

def add_gaussian_noise(
    waveform: np.ndarray,
    sr: int,
    snr_db: float = 20.0,
) -> np.ndarray:
    """Add Gaussian noise at a specified SNR (dB)."""
    signal_power = np.mean(waveform ** 2)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = np.random.normal(0, np.sqrt(noise_power), waveform.shape)
    return waveform + noise


def time_stretch(
    waveform: np.ndarray,
    sr: int,
    rate: float | None = None,
) -> np.ndarray:
    """Randomly stretch / compress the waveform in time.

    Args:
        rate: stretch factor. If None, sampled uniformly from [0.9, 1.1].
    """
    rate = rate if rate is not None else np.random.uniform(0.9, 1.1)
    return librosa.effects.time_stretch(waveform, rate=rate)


def pitch_shift(
    waveform: np.ndarray,
    sr: int,
    n_steps: float | None = None,
) -> np.ndarray:
    """Shift pitch by a random number of semitones.

    Args:
        n_steps: semitones to shift. If None, sampled from [-2, 2].
    """
    n_steps = n_steps if n_steps is not None else np.random.uniform(-2, 2)
    return librosa.effects.pitch_shift(waveform, sr=sr, n_steps=n_steps)


def add_room_reverb(
    waveform: np.ndarray,
    sr: int,
    decay: float = 0.3,
) -> np.ndarray:
    """Simple FIR reverb approximation using exponential impulse response.

    Args:
        decay: exponential decay parameter for the impulse response.
    """
    impulse_len = int(sr * 0.05)  # 50 ms impulse
    impulse = np.random.exponential(decay, impulse_len)
    impulse /= impulse.sum()
    return np.convolve(waveform, impulse, mode="same")


# ── Composite augmentation ──────────────────────────────────────────────────

def augment_waveform(
    waveform: np.ndarray,
    sr: int,
    p: float = 0.4,
) -> np.ndarray:
    """Apply each augmentation independently with probability *p*.

    Args:
        waveform: 1-D audio waveform.
        sr: sample rate in Hz.
        p: probability of applying each individual augmentation.

    Returns:
        Augmented waveform.
    """
    augmentations = [
        add_gaussian_noise,
        time_stretch,
        pitch_shift,
        add_room_reverb,
    ]
    for aug_fn in augmentations:
        if np.random.random() < p:
            waveform = aug_fn(waveform, sr)
    return waveform
