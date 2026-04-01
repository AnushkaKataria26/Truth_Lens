"""
FaceForensics++ Preprocessing Pipeline
=======================================
Extracts frames from FF++ videos, detects and crops faces using MTCNN,
resizes to the target resolution, and saves organised by label with
per-manipulation-type sub-directories.

Input:  raw video files organised in the FF++ directory structure
Output: face crops → PROCESSED_DIR/visual/ff/{real|fake}/{manipulation_type}/

Usage:
    python -m training.data.visual.ff_preprocessor
    python -m training.data.visual.ff_preprocessor --frames 30 --compression c23
"""

import argparse
import logging
from pathlib import Path

import cv2
import numpy as np
from facenet_pytorch import MTCNN
from PIL import Image
from tqdm import tqdm

from training.config import VisualTrainingConfig

logger = logging.getLogger(__name__)

# FF++ manipulation methods — including FaceShifter
MANIPULATION_METHODS = [
    "Deepfakes",
    "Face2Face",
    "FaceSwap",
    "NeuralTextures",
    "FaceShifter",
]

REAL_SUBDIR = "original_sequences/youtube"


class FaceForensicsPreprocessor:
    """Extract, detect, crop faces from FaceForensics++ video dataset."""

    def __init__(self, config: VisualTrainingConfig | None = None):
        self.config = config or VisualTrainingConfig()
        self.input_dir = self.config.ff_dataset_path
        self.output_dir = self.config.processed_path / "ff"
        self.target_size = self.config.input_size

        # MTCNN face detector — keep_all=False returns only the largest face
        self.detector = MTCNN(
            image_size=self.target_size,
            margin=20,
            keep_all=False,
            post_process=False,       # raw pixel values, not normalised
            device=self.config.device if self.config.device != "cuda" else "cpu",
        )

    # ── public API ───────────────────────────────────────────────────────
    def run(
        self,
        frames_per_video: int = 30,
        compression: str = "c23",
    ) -> dict:
        """Process the full FF++ dataset.

        Args:
            frames_per_video: max evenly-spaced frames to sample per video.
            compression: quality level — c0 (raw), c23, or c40.

        Returns:
            dict with counts: {"real": N, "fake": M, "skipped": K}
        """
        stats = {"real": 0, "fake": 0, "skipped": 0}

        # ── Process real sequences
        real_video_dir = self.input_dir / REAL_SUBDIR / compression / "videos"
        if real_video_dir.exists():
            stats["real"] = self._process_video_list(
                video_dir=real_video_dir,
                label="real",
                sub_label="youtube",
                frames_per_video=frames_per_video,
            )
        else:
            logger.warning("Real video dir not found: %s", real_video_dir)

        # ── Process each manipulation method
        for manip_type in MANIPULATION_METHODS:
            fake_video_dir = (
                self.input_dir / "manipulated_sequences" / manip_type
                / compression / "videos"
            )
            if fake_video_dir.exists():
                count = self._process_video_list(
                    video_dir=fake_video_dir,
                    label="fake",
                    sub_label=manip_type,
                    frames_per_video=frames_per_video,
                )
                stats["fake"] += count
            else:
                logger.warning("Fake video dir not found: %s", fake_video_dir)

        logger.info("FF++ preprocessing complete: %s", stats)
        return stats

    # ── internals ────────────────────────────────────────────────────────

    def _process_video_list(
        self,
        video_dir: Path,
        label: str,
        sub_label: str,
        frames_per_video: int,
    ) -> int:
        """Process all .mp4 videos in a directory and return saved-face count.

        Output path: ``output_dir/{label}/{sub_label}/{video_stem}_{frame_idx}.jpg``
        """
        out_dir = self.output_dir / label / sub_label
        out_dir.mkdir(parents=True, exist_ok=True)
        saved = 0

        videos = sorted(video_dir.glob("*.mp4"))
        for video_path in tqdm(videos, desc=f"FF++ {label}/{sub_label}"):
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                cap.release()
                continue

            # Sample evenly-spaced frames
            n_sample = min(frames_per_video, total_frames)
            frame_indices = np.linspace(0, total_frames - 1, n_sample, dtype=int)

            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_tensor = self._detect_face(frame_rgb)
                if face_tensor is None:
                    continue

                # Convert tensor (C, H, W) → PIL Image for saving
                face_np = face_tensor.permute(1, 2, 0).numpy().astype(np.uint8)
                face_img = Image.fromarray(face_np)

                fname = f"{video_path.stem}_{frame_idx:05d}.jpg"
                face_img.save(out_dir / fname, quality=95)
                saved += 1

            cap.release()
            logger.debug("Processed %s: %d faces", video_path.name, saved)

        return saved

    def _detect_face(self, rgb: np.ndarray) -> "torch.Tensor | None":
        """Detect the largest face and return the cropped tensor, or None."""
        try:
            face_tensor = self.detector(rgb)
            return face_tensor  # (C, H, W) uint8 or None
        except Exception:
            logger.debug("Face detection failed for a frame", exc_info=True)
            return None


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess FaceForensics++")
    parser.add_argument("--frames", type=int, default=30, help="Max frames per video")
    parser.add_argument("--compression", default="c23", choices=["c0", "c23", "c40"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    preprocessor = FaceForensicsPreprocessor()
    preprocessor.run(frames_per_video=args.frames, compression=args.compression)


if __name__ == "__main__":
    main()
