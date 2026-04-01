import os
import torch
import torch.nn as nn
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Dataset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db_models import Base, TrainingData

# DB Config for Text Modality
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./truthlens_train.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TextDataset(Dataset):
    def __init__(self, records):
        self.records = records
        self.classes = ["real", "fake"]
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        
    def __len__(self):
        return len(self.records)
        
    def __getitem__(self, idx):
        record = self.records[idx]
        text_content = record.text_content
        label = self.class_to_idx.get(record.label, 0)
        
        # Simple char-level hash encoding for demonstration of text training
        # In production: Use HuggingFace AutoTokenizer
        tensor = torch.zeros(256)
        if text_content:
            for i, char in enumerate(text_content[:256]):
                tensor[i] = ord(char) / 255.0
                
        return tensor, torch.tensor(label, dtype=torch.long)

class AudioVideoDummyDataset(Dataset):
    """
    Dummy dataset reader for Audio and Video pending torchaudio/torchvision.io
    In a real scenario, extracts frames/waveforms natively.
    """
    def __init__(self, root_dir):
        self.samples = []
        self.classes = ["real", "fake"]
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        
        for cls in self.classes:
            cls_dir = os.path.join(root_dir, cls)
            if os.path.isdir(cls_dir):
                for f in os.listdir(cls_dir):
                    self.samples.append((os.path.join(cls_dir, f), self.class_to_idx[cls]))
                    
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, idx):
        # Return a dummy tensor representing the extracted features (1D for audio, 4D for video)
        # For simplicity in this unified script, we return a 1D feature array of size 512
        _, label = self.samples[idx]
        return torch.randn(512), torch.tensor(label, dtype=torch.long)

def _train_loop(model, dataloader, modality_name):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    model.train()
    print(f"Starting training phase for modality: {modality_name.upper()}...")
    
    for batch_idx, (inputs, targets) in enumerate(dataloader):
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        print(f"[{modality_name.upper()}] Batch {batch_idx+1}/{len(dataloader)} completed. Loss: {loss.item():.4f}")

def train_image_model(dataset_dir):
    print("\n--- Training IMAGE Model ---")
    img_dir = os.path.join(dataset_dir, "image")
    if not os.path.exists(img_dir) or not any(os.scandir(img_dir)):
        print(f"Skipping Image: No data in {img_dir}")
        return
        
    weights = EfficientNet_V2_S_Weights.DEFAULT
    model = efficientnet_v2_s(weights=weights)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 2)
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = datasets.ImageFolder(root=img_dir, transform=transform)
    if len(dataset) == 0:
        return
        
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    _train_loop(model, dataloader, "image")
    
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), os.path.join('models', 'efficientnetv2_image.pth'))
    print("Saved Image Model.")

def train_text_model():
    print("\n--- Training TEXT Model ---")
    db = SessionLocal()
    records = db.query(TrainingData).filter(TrainingData.modality == "text").all()
    db.close()
    
    if not records:
        print("Skipping Text: No text data found in DB.")
        return
        
    dataset = TextDataset(records)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Simple linear text classifier
    model = nn.Sequential(
        nn.Linear(256, 128),
        nn.ReLU(),
        nn.Linear(128, 2)
    )
    
    _train_loop(model, dataloader, "text")
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), os.path.join('models', 'text_classifier.pth'))
    print("Saved Text Model.")

def train_audio_model(dataset_dir):
    print("\n--- Training AUDIO Model ---")
    audio_dir = os.path.join(dataset_dir, "audio")
    if not os.path.exists(audio_dir) or not any(os.scandir(audio_dir)):
        print(f"Skipping Audio: No data in {audio_dir}")
        return
        
    dataset = AudioVideoDummyDataset(audio_dir)
    if len(dataset) == 0:
        return
        
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    model = nn.Sequential(
        nn.Linear(512, 128),
        nn.ReLU(),
        nn.Linear(128, 2)
    )
    
    _train_loop(model, dataloader, "audio")
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), os.path.join('models', 'audio_classifier.pth'))
    print("Saved Audio Model.")

def train_video_model(dataset_dir):
    print("\n--- Training VIDEO Model ---")
    video_dir = os.path.join(dataset_dir, "video")
    if not os.path.exists(video_dir) or not any(os.scandir(video_dir)):
        print(f"Skipping Video: No data in {video_dir}")
        return
        
    dataset = AudioVideoDummyDataset(video_dir)
    if len(dataset) == 0:
        return
        
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    model = nn.Sequential(
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Linear(256, 2)
    )
    
    _train_loop(model, dataloader, "video")
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), os.path.join('models', 'video_classifier.pth'))
    print("Saved Video Model.")

def train_all_models():
    dataset_dir = os.path.join(os.path.dirname(__file__), "data", "dataset")
    print(f"Starting Multimodal Real-Data Training Pipeline (Dataset dir: {dataset_dir})")
    
    train_image_model(dataset_dir)
    train_text_model()
    train_audio_model(dataset_dir)
    train_video_model(dataset_dir)
    
    print("\nAll available modalities trained and saved!")

if __name__ == "__main__":
    train_all_models()
