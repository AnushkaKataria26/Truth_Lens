"""
Dataset Download & Verification
=================================
Automated download of training datasets with checksum verification
and progress bars. Uses ``requests`` for streaming downloads.

Datasets:
  1. FaceForensics++ — requires registration (download_FF++.py from authors)
     Download: original videos + c23 (lightly compressed) split
     Manipulation types: Deepfakes, Face2Face, FaceSwap, NeuralTextures, FaceShifter
     Size: ~1.4 TB full, ~300 GB c23 compressed — use c23 for training

  2. ASVspoof 2021 LA partition
     Available at: https://www.asvspoof.org/index2021.html
     Download: train, dev, eval sets + metadata files
     Size: ~30 GB

  3. CASIA-CMFD (copy-move forgery detection)
     Available at: https://github.com/namtpham/casia2groundtruth
     Size: ~2 GB

Usage:
    python -m training.data.download_datasets --dataset all
    python -m training.data.download_datasets --dataset asvspoof
    python -m training.data.download_datasets --dataset ff++
"""

import argparse
import hashlib
import logging
import tarfile
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from training.config import DATA_DIR

logger = logging.getLogger(__name__)

# ── Per-file checksums ───────────────────────────────────────────────────────
# Replace placeholder values with real checksums from the official sites
# after obtaining dataset access.
DATASET_CHECKSUMS = {
    "ASVspoof2021_LA_train.tar.gz": "sha256:<checksum_from_official_site>",
    "ASVspoof2021_LA_dev.tar.gz": "sha256:<checksum_from_official_site>",
    "ASVspoof2021_LA_eval.tar.gz": "sha256:<checksum_from_official_site>",
}

# ── FF++ download instructions ──────────────────────────────────────────────
FF_DOWNLOAD_INSTRUCTIONS = """
FaceForensics++ requires dataset access approval.
1. Fill form at: https://docs.google.com/forms/d/e/1FAIpQLSdRRR3L5zAv6tQ_CKxmK4W96tAab_pfBu2EKAgQbeDVhmXagg/viewform
2. You will receive download_FF++.py by email
3. Run: python download_FF++.py {ff_dataset_path} -d all -c c23 -t videos
4. Place output at: {ff_dataset_path}
"""

# ── Dataset registry ─────────────────────────────────────────────────────────
DATASETS = {
    "ff++": {
        "description": "FaceForensics++ (c23 compression)",
        "url": None,  # requires author-provided script
        "output_dir": DATA_DIR / "FaceForensics++",
        "archive_type": "zip",
        "partitions": None,  # manual download
        "instructions": FF_DOWNLOAD_INSTRUCTIONS.format(
            ff_dataset_path=DATA_DIR / "FaceForensics++",
        ),
    },
    "casia": {
        "description": "CASIA Copy-Move Forgery Detection v2",
        "url": "https://github.com/namtpham/casia2groundtruth",  # placeholder
        "output_dir": DATA_DIR / "CASIA-CMFD",
        "archive_type": "zip",
        "partitions": None,
        "instructions": (
            "CASIA-CMFD may require institutional access.\n"
            "Place the Tp and Au directories under data/raw/CASIA-CMFD/"
        ),
    },
    "asvspoof": {
        "description": "ASVspoof 2021 Logical Access",
        "url": "https://www.asvspoof.org/index2021.html",  # placeholder base
        "output_dir": DATA_DIR / "ASVspoof2021",
        "archive_type": "tar.gz",
        "partitions": [
            # (filename, url_placeholder)
            ("ASVspoof2021_LA_train.tar.gz", None),
            ("ASVspoof2021_LA_dev.tar.gz", None),
            ("ASVspoof2021_LA_eval.tar.gz", None),
        ],
        "instructions": (
            "ASVspoof 2021 requires registration at https://www.asvspoof.org/.\n"
            "Download the LA partition (train, dev, eval) and extract under "
            "data/raw/ASVspoof2021/"
        ),
    },
}


# ── Download helpers ─────────────────────────────────────────────────────────

def download_file(
    url: str,
    dest_path: Path,
    expected_checksum: str | None = None,
    timeout: int = 60,
) -> None:
    """Stream-download a URL to *dest_path* with tqdm progress.

    Args:
        url: source URL.
        dest_path: local destination path.
        expected_checksum: optional ``algorithm:hexdigest`` string.
        timeout: connection timeout in seconds.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))

    with (
        open(dest_path, "wb") as f,
        tqdm(total=total, unit="B", unit_scale=True, desc=dest_path.name) as bar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    if expected_checksum:
        verify_checksum(dest_path, expected_checksum)


def verify_checksum(file_path: Path, expected: str) -> None:
    """Verify file integrity against an ``algorithm:hexdigest`` checksum.

    Args:
        file_path: path to the file to verify.
        expected: checksum in ``algorithm:hexdigest`` format (e.g. ``sha256:abc123``).

    Raises:
        ValueError: if the computed checksum does not match.
    """
    algorithm, expected_hash = expected.split(":", 1)
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected_hash:
        raise ValueError(
            f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual}"
        )
    logger.info("Checksum verified: %s ✓", file_path.name)


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """Extract a .tar.gz, .tgz, or .zip archive.

    Args:
        archive_path: path to the archive file.
        dest_dir: directory to extract into.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.suffix in (".gz", ".tgz") or str(archive_path).endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(dest_dir)
    elif archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as z:
            z.extractall(dest_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
    logger.info("Extracted: %s → %s", archive_path.name, dest_dir)


# ── High-level API ───────────────────────────────────────────────────────────

def download_dataset(name: str, force: bool = False) -> None:
    """Download and verify a single dataset by registry key.

    For datasets that require manual download (FF++, ASVspoof), prints
    instructions instead of attempting an automated download.
    """
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset: {name}. Choose from: {list(DATASETS)}")

    info = DATASETS[name]
    output_dir = Path(info["output_dir"])

    # Skip if already present
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        logger.info("%s already exists — skipping (use --force to re-download)", name)
        return

    # If no URL available → print manual instructions
    if info["url"] is None:
        logger.warning(
            "Automated download not available for %s.\n%s",
            name, info["instructions"],
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle multi-partition datasets (e.g. ASVspoof train/dev/eval)
    partitions = info.get("partitions")
    if partitions:
        for filename, url in partitions:
            if url is None:
                logger.warning(
                    "No download URL for %s — download manually.\n%s",
                    filename, info["instructions"],
                )
                continue
            archive_path = output_dir / filename
            checksum = DATASET_CHECKSUMS.get(filename)
            download_file(url, archive_path, expected_checksum=checksum)
            extract_archive(archive_path, output_dir)
            archive_path.unlink()
    else:
        # Single-archive download
        archive_name = f"{name}_download.{info['archive_type']}"
        archive_path = output_dir.parent / archive_name

        logger.info("Downloading %s …", info["description"])
        download_file(info["url"], archive_path)
        extract_archive(archive_path, output_dir)
        archive_path.unlink()

    logger.info("Download and extraction complete for %s", name)


def download_all(force: bool = False) -> None:
    """Download all registered datasets."""
    for name in DATASETS:
        try:
            download_dataset(name, force=force)
        except Exception:
            logger.error("Failed to download %s", name, exc_info=True)


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Download training datasets")
    parser.add_argument(
        "--dataset",
        default="all",
        choices=["all", *DATASETS.keys()],
        help="Which dataset to download",
    )
    parser.add_argument("--force", action="store_true", help="Re-download even if present")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.dataset == "all":
        download_all(force=args.force)
    else:
        download_dataset(args.dataset, force=args.force)


if __name__ == "__main__":
    main()
