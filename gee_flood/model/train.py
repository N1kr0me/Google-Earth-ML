import argparse
import os
import time
from dataclasses import dataclass
from typing import List

import numpy as np
import torch
import yaml
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from gee_flood.data.tiles_repo import assign_splits, get_tiles_by_split
from gee_flood.model.image_io import load_image_from_uri
from gee_flood.model.net import SimpleCNN


@dataclass
class TrainConfig:
    image_size: int
    batch_size: int
    epochs: int
    learning_rate: float
    num_classes: int
    artifact_path: str
    device: str


class TileDataset(Dataset):
    def __init__(self, tiles, image_size: int, max_bytes: int):
        self.tiles = tiles
        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ]
        )
        self.max_bytes = max_bytes

    def __len__(self) -> int:
        return len(self.tiles)

    def __getitem__(self, idx: int):
        tile = self.tiles[idx]
        image = load_image_from_uri(tile.image_uri, max_bytes=self.max_bytes)
        x = self.transform(image)
        y = torch.tensor(tile.label, dtype=torch.long)
        return x, y


def _load_config(path: str) -> TrainConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return TrainConfig(
        image_size=cfg["image_size"],
        batch_size=cfg["batch_size"],
        epochs=cfg["epochs"],
        learning_rate=cfg["learning_rate"],
        num_classes=cfg["num_classes"],
        artifact_path=cfg["artifact_path"],
        device=cfg.get("device", "cpu"),
    )


def _accuracy(preds: np.ndarray, labels: np.ndarray) -> float:
    return float((preds == labels).mean())


def _f1_binary(preds: np.ndarray, labels: np.ndarray) -> float:
    tp = ((preds == 1) & (labels == 1)).sum()
    fp = ((preds == 1) & (labels == 0)).sum()
    fn = ((preds == 0) & (labels == 1)).sum()
    denom = (2 * tp + fp + fn)
    return float((2 * tp) / denom) if denom > 0 else 0.0


def _evaluate(model, loader, device: str):
    model.eval()
    preds_all = []
    labels_all = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            preds_all.append(preds)
            labels_all.append(y.numpy())

    if not preds_all:
        return {"accuracy": 0.0, "f1": 0.0}

    preds_all = np.concatenate(preds_all)
    labels_all = np.concatenate(labels_all)
    return {
        "accuracy": _accuracy(preds_all, labels_all),
        "f1": _f1_binary(preds_all, labels_all),
    }


def train(config_path: str) -> None:
    cfg = _load_config(config_path)
    device = torch.device(cfg.device if torch.cuda.is_available() else "cpu")

    assign_splits()
    train_tiles = get_tiles_by_split("train")
    val_tiles = get_tiles_by_split("val")
    test_tiles = get_tiles_by_split("test")

    if not train_tiles:
        raise RuntimeError("No tiles found. Ingest data before training.")

    max_bytes = int(os.getenv("MAX_IMAGE_BYTES", "3145728"))
    train_ds = TileDataset(train_tiles, cfg.image_size, max_bytes=max_bytes)
    val_ds = TileDataset(val_tiles, cfg.image_size, max_bytes=max_bytes)
    test_ds = TileDataset(test_tiles, cfg.image_size, max_bytes=max_bytes)

    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=cfg.batch_size, shuffle=False)

    model = SimpleCNN(num_classes=cfg.num_classes).to(device)
    optimizer = optim.Adam(model.parameters(), lr=cfg.learning_rate)
    criterion = nn.CrossEntropyLoss()

    os.makedirs(os.path.dirname(cfg.artifact_path), exist_ok=True)
    run_id = time.strftime("%Y%m%d_%H%M%S")
    metrics_path = os.path.join(os.path.dirname(cfg.artifact_path), f"metrics_{run_id}.csv")

    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write("epoch,loss,val_accuracy,val_f1\n")

    for epoch in range(cfg.epochs):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        val_metrics = _evaluate(model, val_loader, str(device))
        avg_loss = total_loss / max(1, len(train_loader))

        with open(metrics_path, "a", encoding="utf-8") as f:
            f.write(f"{epoch},{avg_loss:.4f},{val_metrics['accuracy']:.4f},{val_metrics['f1']:.4f}\n")

        print(f"Epoch {epoch}: loss={avg_loss:.4f}, val_acc={val_metrics['accuracy']:.4f}")

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": cfg.__dict__,
        },
        cfg.artifact_path,
    )

    test_metrics = _evaluate(model, test_loader, str(device))
    print(f"Test accuracy: {test_metrics['accuracy']:.4f}, F1: {test_metrics['f1']:.4f}")

    # TODO: Run multiple experiments with different learning rates and augmentations.
    # Why it matters: hyperparameter tuning shows real ML rigor beyond a baseline.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/train_config.yaml")
    args = parser.parse_args()
    train(args.config)
