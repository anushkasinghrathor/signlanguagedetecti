"""
PyTorch LSTM Architecture for Dynamic Sign Language Recognition
--------------------------------------------------------------
Processes temporal sequences of 30 frames x 126 landmark features.

# INVARIANT: Input shape must be (batch_size, sequence_length=30, input_dim=126).
# INVARIANT: Output shape is (batch_size, num_classes).
"""

import torch
import torch.nn as nn


class SignLanguageLSTM(nn.Module):
    """
    Stacked 2-layer LSTM with dropout and a dense classification head.
    """

    def __init__(
        self,
        input_size: int = 126,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 3,
        dropout: float = 0.2,
    ):
        super(SignLanguageLSTM, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes

        # LSTM Layer
        # WHY: 2 stacked layers with 128 hidden units capture multi-scale temporal
        # motion dynamics (e.g. wrist movement vs simultaneous finger curl).
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Tensor of shape (batch_size, seq_len=30, input_size=126)
        Returns:
            logits: Tensor of shape (batch_size, num_classes)
        """
        # LSTM forward pass: out shape (batch_size, seq_len, hidden_size)
        out, _ = self.lstm(x)

        # Extract last time-step feature vector representing entire motion sequence
        last_step = out[:, -1, :]

        # Classification logits
        logits = self.classifier(last_step)
        return logits
