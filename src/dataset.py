import csv
import json
import os
import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, Union

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


@dataclass
class Sample:
    path: str
    target: List[int]


def _parse_target(value: Union[str, Sequence[int]]) -> List[int]:
    if isinstance(value, (list, tuple)):
        return [int(v) for v in value]
    if isinstance(value, str):
        tokens = [t for t in value.replace(",", " ").split() if t]
        return [int(t) for t in tokens]
    raise TypeError(f"Unsupported target type: {type(value)}")


def _resolve_path(root: str, path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(root, path))


def load_manifest(manifest_path: str) -> List[Sample]:
    """Load samples from a CSV/JSON/JSONL manifest.

    Expected fields:
      - path: path to a sequence file (.npy/.npz/.pt)
      - target: space or comma separated label ids (CTC targets, no blanks)
    """
    ext = os.path.splitext(manifest_path)[1].lower()
    root = os.path.dirname(os.path.abspath(manifest_path))
    samples: List[Sample] = []

    if ext == ".jsonl":
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                path = _resolve_path(root, obj["path"])
                target = _parse_target(obj["target"])
                samples.append(Sample(path=path, target=target))
    elif ext == ".json":
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for obj in data:
            path = _resolve_path(root, obj["path"])
            target = _parse_target(obj["target"])
            samples.append(Sample(path=path, target=target))
    elif ext == ".csv":
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = _resolve_path(root, row["path"])
                target = _parse_target(row["target"])
                samples.append(Sample(path=path, target=target))
    else:
        raise ValueError(f"Unsupported manifest extension: {ext}")

    if not samples:
        raise ValueError("Manifest contains no samples.")
    return samples


def _load_sequence(path: str) -> torch.Tensor:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".npy", ".npz"):
        arr = np.load(path)
        if isinstance(arr, np.lib.npyio.NpzFile):
            arr = arr["arr_0"]
        return torch.from_numpy(arr).float()
    if ext in (".pt", ".pth"):
        obj = torch.load(path, map_location="cpu")
        if isinstance(obj, torch.Tensor):
            return obj.float()
        return torch.tensor(obj, dtype=torch.float32)
    raise ValueError(f"Unsupported sequence file extension: {ext}")


def _flatten_if_needed(seq: torch.Tensor, feature_dim: int) -> torch.Tensor:
    if seq.ndim == 3 and seq.shape[1:] == (75, 3):
        return seq.reshape(seq.shape[0], feature_dim)
    if seq.ndim == 2 and seq.shape[1] == feature_dim:
        return seq
    if seq.ndim == 2 and seq.shape[0] == feature_dim:
        return seq.transpose(0, 1)
    if seq.ndim == 1 and seq.numel() == feature_dim:
        return seq.view(1, feature_dim)
    raise ValueError(f"Unsupported sequence shape: {tuple(seq.shape)}")


def time_warp(seq: torch.Tensor, factor: float) -> torch.Tensor:
    """Scale the time axis with linear interpolation.

    Input shape: [T, D]
    Output shape: [T', D]
    """
    if seq.shape[0] < 2:
        return seq
    new_len = max(2, int(round(seq.shape[0] * factor)))
    # [T, D] -> [1, D, T] for 1D linear interpolation along time.
    seq_t = seq.transpose(0, 1).unsqueeze(0)
    warped = F.interpolate(seq_t, size=new_len, mode="linear", align_corners=False)
    return warped.squeeze(0).transpose(0, 1)


class SignLanguageDataset(Dataset):
    """Dataset for fixed-window CTC training with optional time warping."""

    def __init__(
        self,
        manifest: Union[str, Sequence[Sample]],
        seq_len: int = 60,
        feature_dim: int = 225,
        time_warp_enabled: bool = True,
        warp_prob: float = 0.5,
        warp_range: Tuple[float, float] = (0.8, 1.2),
    ) -> None:
        self.samples = load_manifest(manifest) if isinstance(manifest, str) else list(manifest)
        self.seq_len = int(seq_len)
        self.feature_dim = int(feature_dim)
        self.time_warp_enabled = bool(time_warp_enabled)
        self.warp_prob = float(warp_prob)
        self.warp_range = warp_range

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        sample = self.samples[idx]
        seq = _load_sequence(sample.path)
        seq = _flatten_if_needed(seq, self.feature_dim)

        if self.time_warp_enabled and random.random() < self.warp_prob:
            factor = random.uniform(*self.warp_range)
            seq = time_warp(seq, factor)

        # Actual length after warping, before padding/truncation.
        input_len = min(seq.shape[0], self.seq_len)

        if seq.shape[0] >= self.seq_len:
            seq = seq[: self.seq_len]
        else:
            pad = torch.zeros(self.seq_len - seq.shape[0], self.feature_dim, dtype=seq.dtype)
            seq = torch.cat([seq, pad], dim=0)

        target = torch.tensor(sample.target, dtype=torch.long)
        target_len = int(target.numel())
        return seq, target, input_len, target_len


def collate_ctc(batch: Iterable[Tuple[torch.Tensor, torch.Tensor, int, int]]):
    xs, targets, input_lengths, target_lengths = zip(*batch)
    x = torch.stack(xs, dim=0)
    input_lengths = torch.tensor(input_lengths, dtype=torch.long)
    target_lengths = torch.tensor(target_lengths, dtype=torch.long)
    # CTC expects targets concatenated into a 1D tensor.
    targets = torch.cat(list(targets), dim=0)
    return x, targets, input_lengths, target_lengths


def make_dataloader(
    manifest: Union[str, Sequence[Sample]],
    batch_size: int = 16,
    shuffle: bool = True,
    num_workers: int = 4,
    **dataset_kwargs,
) -> DataLoader:
    dataset = SignLanguageDataset(manifest, **dataset_kwargs)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
        collate_fn=collate_ctc,
    )
