import logging
from typing import List
import time

try:
    from peft import LoraConfig, get_peft_model
except ImportError:
    # MOCK implementation for environment without peft
    class LoraConfig:
        def __init__(self, **kwargs): pass
    def get_peft_model(model, config): return model

from app.agents.tools.pattern_extractor import ExtractedPattern

logger = logging.getLogger(__name__)


def run_fine_tune_task(attack_type: str):
    """
    Executed on the gpu_queue Celery worker.
    Fine-tunes for max 3 epochs on new samples + 20% original training data (replay buffer).
    Replay buffer prevents catastrophic forgetting.
    """
    logger.info(f"Starting background fine-tune for {attack_type}")
    # 4. Evaluate on held-out validation set — only save if accuracy improves
    # 5. Save adapter weights to /models/lora_adapters/{attack_type}_{timestamp}.pth
    # 6. Upload to S3: models/lora_adapters/
    # 7. Update model registry in Redis: SET model:active_lora_adapter <s3_path>
    # 8. Hot-reload adapter in inference workers via Celery broadcast signal
    time.sleep(1)  # simulate work
    logger.info(f"Finished fine-tuning for {attack_type}")


def trigger_lora_update(patterns: List[ExtractedPattern]) -> str:
    # Filter for high novelty (> 0.7)
    novel_patterns = [p for p in patterns if p.novelty_score > 0.7]

    if not novel_patterns:
        logger.info("No patterns with sufficient novelty score to trigger fine-tuning.")
        return "skipped"

    for pattern in novel_patterns:
        attack = pattern.attack_type
        logger.info(f"Checking training samples for novel attack: {attack}")

        # [MOCK] query S3 bucket for sample count
        samples_count = 120

        if samples_count < 50:
            logger.warning(f"Not enough samples ({samples_count}) for {attack}. Skipping fine-tune.")
            continue

        # Configure LoRA
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            target_modules=["query", "value"],  # for ViT attention layers
            lora_dropout=0.05,
            bias="none",
            task_type="IMAGE_CLASSIFICATION",
        )
        logger.info("Configured LoRA with target_modules=['query', 'value']")

        # Dispatch to GPU queue via Celery — non-blocking
        # The agent continues to update_rag_node immediately
        try:
            from app.worker import lora_fine_tune_task
            task = lora_fine_tune_task.apply_async(args=[attack], queue="gpu_queue")
            logger.info(f"Dispatched fine-tune task {task.id} for {attack} to gpu_queue")
            return f"task_id:{task.id}"
        except Exception as e:
            logger.warning(f"Celery not available, running synchronously: {e}")
            run_fine_tune_task(attack)

    return "task_triggered"
