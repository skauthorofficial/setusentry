"""
SetuSentry MobileNetV2 Crack Classifier
Defines a transfer-learning convolutional neural network architecture
for bridge concrete surface crack detection using a MobileNetV2 backbone.
"""

from __future__ import annotations
import os
import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import MobileNet_V2_Weights


class MobileNetV2CrackDetector(nn.Module):
    """
    MobileNetV2 with custom binary classification head for concrete crack detection.
    Classes: 0 = Non-Cracked, 1 = Cracked.
    """

    def __init__(self, pretrained: bool = True, dropout: float = 0.3):
        super().__init__()
        weights = MobileNet_V2_Weights.DEFAULT if pretrained else None
        self.backbone = models.mobilenet_v2(weights=weights)

        # In_features from the last linear layer of MobileNetV2 (1280)
        in_features = self.backbone.classifier[1].in_features

        # Replace classifier with custom head suited for binary classification
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(p=dropout / 2),
            nn.Linear(256, 2),  # 2 classes: Non-Cracked, Cracked
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw class logits."""
        return self.backbone(x)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract high-level feature map representations from the convolutional backbone."""
        features = self.backbone.features(x)
        features = nn.functional.adaptive_avg_pool2d(features, (1, 1))
        return torch.flatten(features, 1)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return softmax probabilities for [Non-Cracked, Cracked]."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return torch.softmax(logits, dim=1)


def build_crack_model(weights_path: str = None, device: str = "cpu") -> MobileNetV2CrackDetector:
    """
    Factory function to instantiate MobileNetV2CrackDetector.
    Optionally loads fine-tuned weights from a checkpoint file if present.
    """
    model = MobileNetV2CrackDetector(pretrained=True)
    if weights_path and os.path.exists(weights_path):
        try:
            state_dict = torch.load(weights_path, map_location=device)
            model.load_state_dict(state_dict)
            print(f"[MobileNetV2CrackDetector] Loaded fine-tuned weights from {weights_path}")
        except Exception as e:
            print(f"[MobileNetV2CrackDetector] Warning: Could not load weights from {weights_path}: {e}")

    model.to(device)
    model.eval()
    return model
