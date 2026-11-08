"""
SetuSentry SDNET2018 Fine-Tuning Pipeline
Trains MobileNetV2 on concrete crack classification benchmarks (e.g. SDNET2018).
SDNET2018 contains annotated images of cracked and non-cracked concrete
surfaces across Bridge Decks, Pavements, and Retaining Walls.
"""

from __future__ import annotations
import argparse
import os
import sys
import time
from typing import Dict, List, Tuple
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms

# Add parent directory to path to allow importing model.crack_detector
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from model.crack_detector import MobileNetV2CrackDetector


class ConcreteCrackDataset(Dataset):
    """
    Dataset loader for concrete crack imagery.
    Supports either standard ImageFolder layout:
       root/
         cracked/
         uncracked/
    or SDNET2018 directory structure:
       root/
         D/ (Decks) -> CD (Cracked Deck), UD (Uncracked Deck)
         P/ (Pavement) -> CP (Cracked Pavement), UP (Uncracked Pavement)
         W/ (Walls) -> CW (Cracked Wall), UW (Uncracked Wall)
    """

    def __init__(self, root_dir: str, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples: List[Tuple[str, int]] = []

        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"Dataset root directory not found: {root_dir}")

        self._discover_images()

    def _discover_images(self):
        valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
        # Walk directory and label based on standard SDNET naming or folder naming
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_exts:
                    full_path = os.path.join(root, file)
                    norm_path = full_path.replace("\\", "/").lower()

                    # Check if cracked or uncracked
                    if "/cracked/" in norm_path or "/cd/" in norm_path or "/cp/" in norm_path or "/cw/" in norm_path:
                        self.samples.append((full_path, 1))
                    elif "/uncracked/" in norm_path or "/non-cracked/" in norm_path or "/ud/" in norm_path or "/up/" in norm_path or "/uw/" in norm_path:
                        self.samples.append((full_path, 0))
                    else:
                        # Fallback heuristic on filename
                        if "crack" in file.lower() and "un" not in file.lower() and "non" not in file.lower():
                            self.samples.append((full_path, 1))
                        else:
                            self.samples.append((full_path, 0))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label


def get_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """Return training and validation torchvision transform pipelines."""
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transform, val_transform


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str
) -> Tuple[float, float]:
    """Train model for a single epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / max(total, 1)
    epoch_acc = correct / max(total, 1)
    return epoch_loss, epoch_acc


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: str
) -> Dict[str, float]:
    """Evaluate model on validation set."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    tp = fp = tn = fn = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            # Confusion counts for binary metrics
            preds_np = preds.cpu().numpy()
            labels_np = labels.cpu().numpy()
            tp += int(((preds_np == 1) & (labels_np == 1)).sum())
            fp += int(((preds_np == 1) & (labels_np == 0)).sum())
            tn += int(((preds_np == 0) & (labels_np == 0)).sum())
            fn += int(((preds_np == 0) & (labels_np == 1)).sum())

    val_loss = running_loss / max(total, 1)
    accuracy = correct / max(total, 1)
    precision = tp / max(tp + fp, 1) if (tp + fp) > 0 else 0.0
    recall = tp / max(tp + fn, 1) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / max(precision + recall, 1e-8) if (precision + recall) > 0 else 0.0

    return {
        "val_loss": val_loss,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "total_samples": total,
    }


def run_training(
    data_dir: str,
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-4,
    save_path: str = "model/mobilenetv2_crack_finetuned.pth",
    device: str = "cpu"
) -> None:
    """Execute complete training and validation cycle."""
    print(f"=== Starting SetuSentry SDNET2018 Fine-Tuning ===")
    print(f"Data directory: {data_dir}")
    print(f"Device: {device} | Epochs: {epochs} | Batch size: {batch_size} | LR: {lr}")

    if not os.path.exists(data_dir):
        print(f"Notice: Data directory '{data_dir}' does not exist.")
        print("To fine-tune with SDNET2018:")
        print(" 1. Download SDNET2018 from Utah State University DigitalCommons.")
        print(" 2. Unzip into data/SDNET2018/")
        print(" 3. Run: python model/train.py --data_dir data/SDNET2018 --epochs 20")
        return

    train_tf, val_tf = get_transforms()
    full_dataset = ConcreteCrackDataset(data_dir, transform=train_tf)
    total_len = len(full_dataset)
    print(f"Total discovered images: {total_len}")

    if total_len < 10:
        print("Warning: Insufficient samples found for training (<10). Aborting.")
        return

    # 80/20 train/val split
    val_len = max(int(0.2 * total_len), 1)
    train_len = total_len - val_len
    train_set, val_set = random_split(full_dataset, [train_len, val_len])

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)

    model = MobileNetV2CrackDetector(pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_f1 = 0.0
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        scheduler.step()
        metrics = evaluate(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        print(
            f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] - "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.3f} | "
            f"Val Loss: {metrics['val_loss']:.4f}, Val Acc: {metrics['accuracy']:.3f}, "
            f"F1: {metrics['f1']:.3f}, Recall: {metrics['recall']:.3f}"
        )

        if metrics["f1"] >= best_val_f1:
            best_val_f1 = metrics["f1"]
            torch.save(model.state_dict(), save_path)
            print(f"  --> Saved new best checkpoint to {save_path} (F1: {best_val_f1:.3f})")

    print("=== Training Complete ===")


def main():
    parser = argparse.ArgumentParser(description="SetuSentry Concrete Crack Detector Training Pipeline")
    parser.add_argument("--data_dir", type=str, default="data/SDNET2018", help="Path to SDNET2018 dataset")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--save_path", type=str, default="model/mobilenetv2_crack_finetuned.pth", help="Checkpoint output path")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cpu or cuda)")

    args = parser.parse_args()
    run_training(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        save_path=args.save_path,
        device=args.device,
    )


if __name__ == "__main__":
    main()
