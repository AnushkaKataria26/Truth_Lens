from sklearn.metrics import roc_auc_score, roc_curve
import numpy as np

def compute_auc(labels: list, scores: list) -> float:
    if len(set(labels)) < 2:
        return 0.0
    return float(roc_auc_score(labels, scores))

def compute_eer(labels: list, scores: list) -> float:
    if len(set(labels)) < 2:
        return 1.0
    # Equal Error Rate: point where FAR == FRR
    fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
    fnr = 1 - tpr
    # Find threshold where |FPR - FNR| is minimized
    eer_idx = np.argmin(np.abs(fpr - fnr))
    eer = (fpr[eer_idx] + fnr[eer_idx]) / 2
    return float(eer)

def compute_video_level_accuracy(
    frame_scores: dict,   # {video_stem: [frame_fake_prob, ...]}
    video_labels: dict,   # {video_stem: 0|1}
    aggregation: str = "mean",
) -> float:
    if not frame_scores:
        return 0.0
        
    correct = 0
    for stem, scores in frame_scores.items():
        if aggregation == "mean":
            video_score = np.mean(scores)
        elif aggregation == "max":
            video_score = np.max(scores)
        else:
            video_score = np.mean(scores)
            
        pred = 1 if video_score > 0.5 else 0
        if pred == video_labels.get(stem, -1):
            correct += 1
            
    return float(correct / len(frame_scores))

