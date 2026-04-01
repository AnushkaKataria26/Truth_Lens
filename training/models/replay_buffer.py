# Prevents catastrophic forgetting during LoRA fine-tuning
# Stores a representative sample of original training data
# Mixed with new data during every fine-tuning run

import random
from pathlib import Path

class ReplayBuffer:
    def __init__(self, buffer_size: int = 5000, seed: int = 42):
        self.buffer_size = buffer_size
        self.buffer: list[tuple[Path, int]] = []
        random.seed(seed)

    def populate(self, training_samples: list[tuple[Path, int]]):
        # Reservoir sampling to get representative subset
        # Maintains class balance within buffer
        real_samples = [(p, l) for p, l in training_samples if l == 0]
        fake_samples = [(p, l) for p, l in training_samples if l == 1]

        per_class = self.buffer_size // 2
        self.buffer = (
            random.sample(real_samples, min(per_class, len(real_samples))) +
            random.sample(fake_samples, min(per_class, len(fake_samples)))
        )
        random.shuffle(self.buffer)
        print(f"Replay buffer populated: {len(self.buffer)} samples")

    def get_replay_samples(self, n: int) -> list[tuple[Path, int]]:
        return random.sample(self.buffer, min(n, len(self.buffer)))

    def save(self, path: Path, upload_s3: bool = True):
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [(str(p), l) for p, l in self.buffer]
        with open(path, "w") as f:
            json.dump(data, f)
            
        if upload_s3:
            try:
                import boto3
                s3_client = boto3.client('s3')
                s3_key = f"models/{path.name}"
                s3_client.upload_file(str(path), "truthlens-media", s3_key)
                print(f"Uploaded replay buffer to s3://truthlens-media/{s3_key}")
            except Exception as e:
                print(f"Failed to upload replay buffer to S3: {e}")

    def load(self, path: Path):
        import json
        with open(path) as f:
            data = json.load(f)
        self.buffer = [(Path(p), l) for p, l in data]
        print(f"Replay buffer loaded: {len(self.buffer)} samples")
