import argparse
import os
from typing import Optional

import torch
from torch import nn

from dataset import make_dataloader
from model import SignLanguageModel


def train_one_epoch(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    grad_clip: Optional[float] = None,
) -> float:
    model.train()
    total_loss = 0.0

    for x, targets, input_lengths, target_lengths in loader:
        x = x.to(device)
        targets = targets.to(device)
        input_lengths = input_lengths.to(device)
        target_lengths = target_lengths.to(device)

        log_probs = model(x, input_lengths=input_lengths)
        # CTC expects [T, B, C], so permute time and batch.
        log_probs = log_probs.permute(1, 0, 2)

        loss = criterion(log_probs, targets, input_lengths, target_lengths)
        optimizer.zero_grad()
        loss.backward()
        if grad_clip is not None:
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        total_loss += loss.item() * x.size(0)

    return total_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    total_loss = 0.0

    for x, targets, input_lengths, target_lengths in loader:
        x = x.to(device)
        targets = targets.to(device)
        input_lengths = input_lengths.to(device)
        target_lengths = target_lengths.to(device)

        log_probs = model(x, input_lengths=input_lengths)
        log_probs = log_probs.permute(1, 0, 2)

        loss = criterion(log_probs, targets, input_lengths, target_lengths)
        total_loss += loss.item() * x.size(0)

    return total_loss / len(loader.dataset)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-manifest", type=str, required=True)
    parser.add_argument("--val-manifest", type=str, default=None)
    parser.add_argument("--num-classes", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--save-path", type=str, default="checkpoints/best.pt")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)

    train_loader = make_dataloader(
        args.train_manifest,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        seq_len=60,
        feature_dim=225,
        time_warp_enabled=True,
        warp_prob=0.6,
    )

    val_loader = None
    if args.val_manifest:
        val_loader = make_dataloader(
            args.val_manifest,
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=args.num_workers,
            seq_len=60,
            feature_dim=225,
            time_warp_enabled=False,
        )

    model = SignLanguageModel(
        num_classes=args.num_classes,
        input_dim=225,
        hidden_dim=128,
        num_layers=4,
        num_heads=4,
        kv_rank=16,
        dropout=0.1,
    ).to(device)

    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-2)

    best_val = float("inf")
    os.makedirs(os.path.dirname(args.save_path), exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
            grad_clip=args.grad_clip,
        )

        if val_loader is not None:
            val_loss = evaluate(model, val_loader, criterion, device)
            if val_loss < best_val:
                best_val = val_loss
                torch.save({"model": model.state_dict()}, args.save_path)
            print(f"Epoch {epoch:03d} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f}")
        else:
            print(f"Epoch {epoch:03d} | train_loss={train_loss:.4f}")


if __name__ == "__main__":
    main()
