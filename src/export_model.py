"""
Export a trained CTC model to ONNX for mobile deployment.
The sequence dimension is fixed to 60 to match the dataset's fixed window.

Usage:
    python src/export_model.py \
        --checkpoint checkpoints/best.pt \
        --gloss_map data/gloss_to_id.json \
        --output sign_language_mla.onnx
"""

import argparse
import json
import torch

# Import the model definition from model.py (assumed to be in the same package)
from model import SignLanguageModel


def main():
    parser = argparse.ArgumentParser(description="Export model to ONNX")
    parser.add_argument("--checkpoint", required=True, help="Path to trained .pt checkpoint")
    parser.add_argument("--gloss_map", required=True, help="Path to gloss_to_id.json")
    parser.add_argument("--output", default="sign_language_mla.onnx", help="Output ONNX file")
    parser.add_argument("--opset", type=int, default=14, help="ONNX opset version")
    args = parser.parse_args()

    # Load gloss mapping to determine number of classes
    with open(args.gloss_map, 'r', encoding='utf-8') as f:
        gloss_to_id = json.load(f)
    num_classes = len(gloss_to_id)  # IDs start at 1, blank is 0, so total classes = max_id

    # Instantiate the model (same architecture as training)
    model = SignLanguageModel(
        num_classes=num_classes,
        input_dim=225,
        hidden_dim=128,
        num_layers=4,
        num_heads=4,
        kv_rank=16,
        dropout=0.1,  # dropout is ignored in eval mode anyway
    )

    # Load trained weights
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    if "model" in checkpoint:
        state_dict = checkpoint["model"]
    else:
        state_dict = checkpoint  # fallback if saved as direct state_dict

    model.load_state_dict(state_dict)
    model.eval()

    # Prepare dummy inputs (fixed sequence length = 60)
    dummy_input = torch.randn(1, 60, 225, dtype=torch.float32)
    dummy_lengths = torch.tensor([60], dtype=torch.long)

    # Export to ONNX
    with torch.no_grad():
        torch.onnx.export(
            model,
            (dummy_input, dummy_lengths),
            args.output,
            input_names=["input", "input_lengths"],
            output_names=["log_probs"],
            dynamic_axes={
                "input": {0: "batch_size"},      # batch can vary
                "input_lengths": {0: "batch_size"},
                "log_probs": {0: "batch_size", 1: "time"}  # but time is fixed to 60
            },
            opset_version=args.opset,
            do_constant_folding=True,
            verbose=False,
        )

    print(f"Model exported to {args.output} with {num_classes} classes (including blank).")
    print("ONNX input shape: (batch, 60, 225), output shape: (batch, 60, num_classes+1)")


if __name__ == "__main__":
    main()