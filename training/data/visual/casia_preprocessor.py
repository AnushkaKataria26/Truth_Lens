"""
CASIA-CMFD Preprocessing Pipeline
===================================
Normalises CASIA Copy-Move Forgery Detection images: resize, optional face
crop, and organise into real / tampered directories.

Usage:
    python -m training.data.visual.casia_preprocessor
"""

import argparse
import logging
import shutil
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm

from training.config import VisualTrainingConfig

logger = logging.getLogger(__name__)

# CASIA v2 directory layout
AUTHENTIC_DIRS = ["Au"]
TAMPERED_DIRS = ["Tp"]


class CASIAPreprocessor:
    """Resize and organise CASIA-CMFD images for training."""

    def __init__(self, config: VisualTrainingConfig | None = None):
        self.config = config or VisualTrainingConfig()
        self.input_dir = self.config.casia_dataset_path
        self.output_dir = self.config.processed_path / "casia"
        self.target_size = self.config.input_size

    # ── public API ───────────────────────────────────────────────────────
    def run(self) -> dict:
        """Process the full CASIA-CMFD dataset.

        Returns:
            dict with counts: {"real": N, "fake": M}
        """
        stats = {"real": 0, "fake": 0}

        # Authentic images
        for d in AUTHENTIC_DIRS:
            auth_path = self.input_dir / d
            if auth_path.exists():
                stats["real"] += self._process_dir(auth_path, label="real")

        # Tampered images
        for d in TAMPERED_DIRS:
            tamp_path = self.input_dir / d
            if tamp_path.exists():
                stats["fake"] += self._process_dir(tamp_path, label="fake")

        logger.info("CASIA preprocessing complete: %s", stats)
        return stats

    # ── internals ────────────────────────────────────────────────────────
    def _process_dir(self, src_dir: Path, label: str) -> int:
        """Resize all images in *src_dir* and save under the label folder."""
        out_dir = self.output_dir / label
        out_dir.mkdir(parents=True, exist_ok=True)
        saved = 0

        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        images = [
            p for p in sorted(src_dir.iterdir())
            if p.suffix.lower() in image_extensions
        ]

        for img_path in tqdm(images, desc=f"CASIA {label}"):
            result = self._process_image(img_path)
            if result is not None:
                out_path = out_dir / f"{img_path.stem}.jpg"
                cv2.imwrite(str(out_path), result)
                saved += 1
        return saved

    def _process_image(self, img_path: Path) -> np.ndarray | None:
        """Read, validate, resize a single image."""
        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning("Could not read %s — skipping", img_path)
            return None

        # Resize preserving aspect ratio then centre-crop
        h, w = img.shape[:2]
        target = self.target_size
        scale = target / min(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Centre crop
        y_start = (new_h - target) // 2
        x_start = (new_w - target) // 2
        img = img[y_start : y_start + target, x_start : x_start + target]
        return img


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess CASIA-CMFD")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    preprocessor = CASIAPreprocessor()
    preprocessor.run()


if __name__ == "__main__":
    main()
