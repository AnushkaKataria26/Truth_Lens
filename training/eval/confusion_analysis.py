"""
Confusion & Failure-Case Analysis
====================================
Per-class confusion matrix generation, worst-performing class identification,
and failure-case extraction for deepfake / spoof detection models.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server use

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

logger = logging.getLogger(__name__)

CLASS_NAMES = {0: "Real / Bonafide", 1: "Fake / Spoof"}


def generate_confusion_report(
    labels: list[int],
    scores: list[float],
    threshold: float = 0.5,
    class_names: dict[int, str] | None = None,
) -> dict:
    """Build a structured confusion report.

    Returns:
        dict with keys: confusion_matrix, classification_report,
        per_class_accuracy, worst_class.
    """
    names = class_names or CLASS_NAMES
    preds = [1 if s >= threshold else 0 for s in scores]
    cm = confusion_matrix(labels, preds)
    report_str = classification_report(
        labels, preds, target_names=[names.get(i, str(i)) for i in sorted(names)],
        zero_division=0,
    )

    # Per-class accuracy
    per_class_acc: dict[str, float] = {}
    for cls_idx in sorted(names):
        cls_mask = [l == cls_idx for l in labels]
        cls_labels = [labels[i] for i, m in enumerate(cls_mask) if m]
        cls_preds = [preds[i] for i, m in enumerate(cls_mask) if m]
        acc = sum(1 for a, b in zip(cls_labels, cls_preds) if a == b) / max(len(cls_labels), 1)
        per_class_acc[names[cls_idx]] = round(acc, 4)

    worst_class = min(per_class_acc, key=per_class_acc.get)  # type: ignore[arg-type]

    return {
        "confusion_matrix": cm.tolist(),
        "classification_report": report_str,
        "per_class_accuracy": per_class_acc,
        "worst_class": worst_class,
    }


def extract_failure_cases(
    labels: list[int],
    scores: list[float],
    paths: list[str],
    threshold: float = 0.5,
    top_n: int = 50,
) -> dict[str, list[dict]]:
    """Extract the most-confident failure cases for analysis.

    Returns:
        dict with keys:
            false_positives: real samples predicted as fake (sorted by score desc).
            false_negatives: fake samples predicted as real (sorted by score asc).
    """
    false_positives: list[dict] = []
    false_negatives: list[dict] = []

    for label, score, path in zip(labels, scores, paths):
        pred = 1 if score >= threshold else 0
        if label == 0 and pred == 1:
            false_positives.append({"path": path, "score": score, "label": label})
        elif label == 1 and pred == 0:
            false_negatives.append({"path": path, "score": score, "label": label})

    # Sort: FPs by highest confidence, FNs by lowest score (most confident misses)
    false_positives.sort(key=lambda x: x["score"], reverse=True)
    false_negatives.sort(key=lambda x: x["score"])

    return {
        "false_positives": false_positives[:top_n],
        "false_negatives": false_negatives[:top_n],
    }


def plot_confusion_matrix(
    labels: list[int],
    scores: list[float],
    output_path: str | Path,
    threshold: float = 0.5,
    class_names: dict[int, str] | None = None,
) -> None:
    """Save a confusion-matrix heatmap to disk.

    Args:
        output_path: destination file (e.g. ``confusion.png``).
    """
    names = class_names or CLASS_NAMES
    preds = [1 if s >= threshold else 0 for s in scores]
    cm = confusion_matrix(labels, preds)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=[names.get(i, str(i)) for i in sorted(names)],
        yticklabels=[names.get(i, str(i)) for i in sorted(names)],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Confusion matrix saved → %s", output_path)
