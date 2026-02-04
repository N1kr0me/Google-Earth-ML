import os
from typing import Dict

import torch
from PIL import Image
from torchvision import transforms

from gee_flood.data.tiles_repo import get_tile_by_id
from gee_flood.model.image_io import load_image_from_uri
from gee_flood.model.net import SimpleCNN


def _get_device() -> torch.device:
    device = os.getenv("INFERENCE_DEVICE", "cpu")
    return torch.device(device if torch.cuda.is_available() else "cpu")


def load_model(artifact_path: str):
    device = _get_device()
    checkpoint = torch.load(artifact_path, map_location=device)
    num_classes = checkpoint["config"]["num_classes"]
    model = SimpleCNN(num_classes=num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint["config"]


def predict_pil(model, config: Dict, image: Image.Image) -> Dict:
    image_size = config["image_size"]
    transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
        ]
    )
    x = transform(image).unsqueeze(0)
    device = _get_device()
    x = x.to(device)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pred = int(probs.argmax())
        confidence = float(probs.max())
    return {"prediction": pred, "confidence": confidence}


def predict_by_tile_id(tile_id: int) -> Dict:
    tile = get_tile_by_id(tile_id)
    if not tile:
        raise ValueError("Tile not found")

    artifact_path = os.getenv("MODEL_ARTIFACT_PATH", "artifacts/model_v1/model.pt")
    model, config = load_model(artifact_path)

    max_bytes = int(os.getenv("MAX_IMAGE_BYTES", "3145728"))
    image = load_image_from_uri(tile.image_uri, max_bytes=max_bytes)
    return predict_pil(model, config, image)


def predict_by_uri(uri: str) -> Dict:
    artifact_path = os.getenv("MODEL_ARTIFACT_PATH", "artifacts/model_v1/model.pt")
    model, config = load_model(artifact_path)

    max_bytes = int(os.getenv("MAX_IMAGE_BYTES", "3145728"))
    image = load_image_from_uri(uri, max_bytes=max_bytes)
    return predict_pil(model, config, image)
