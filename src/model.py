import math
from typing import Optional

import torch
from torch import nn
import torch.nn.functional as F


class InputProjection(nn.Module):
    """Project [B, T, 225] into a compact hidden space."""

    def __init__(self, in_dim: int = 225, hidden_dim: int = 128, dropout: float = 0.1) -> None:
        super().__init__()
        dims = [in_dim, 192, 160, 144, hidden_dim]
        layers = []
        for idx in range(len(dims) - 1):
            layers.append(nn.Linear(dims[idx], dims[idx + 1]))
            layers.append(nn.LayerNorm(dims[idx + 1]))
            layers.append(nn.GELU())
            layers.append(nn.Dropout(dropout))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class LowRankMultiheadAttention(nn.Module):
    """Multi-head attention with low-rank KV compression.

    Uses a shared low-rank projection for keys and values to reduce KV memory.
    """

    def __init__(self, dim: int, num_heads: int, kv_rank: int, dropout: float = 0.1) -> None:
        super().__init__()
        if dim % num_heads != 0:
            raise ValueError("dim must be divisible by num_heads")
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = 1.0 / math.sqrt(self.head_dim)

        self.q_proj = nn.Linear(dim, dim, bias=False)
        self.kv_down = nn.Linear(dim, kv_rank, bias=False)
        self.k_proj = nn.Linear(kv_rank, dim, bias=False)
        self.v_proj = nn.Linear(kv_rank, dim, bias=False)
        self.out_proj = nn.Linear(dim, dim, bias=False)
        self.attn_dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x: [B, T, D]
        bsz, tlen, dim = x.shape
        q = self.q_proj(x)
        kv_latent = self.kv_down(x)
        k = self.k_proj(kv_latent)
        v = self.v_proj(kv_latent)

        # [B, T, D] -> [B, H, T, Hd]
        q = q.view(bsz, tlen, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(bsz, tlen, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(bsz, tlen, self.num_heads, self.head_dim).transpose(1, 2)

        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        if key_padding_mask is not None:
            # key_padding_mask: [B, T] with True at padded positions.
            mask = key_padding_mask[:, None, None, :]
            attn_scores = attn_scores.masked_fill(mask, float("-inf"))

        attn_probs = torch.softmax(attn_scores, dim=-1)
        attn_probs = self.attn_dropout(attn_probs)
        ctx = torch.matmul(attn_probs, v)

        # [B, H, T, Hd] -> [B, T, D]
        ctx = ctx.transpose(1, 2).contiguous().view(bsz, tlen, dim)
        out = self.out_proj(ctx)

        if key_padding_mask is not None:
            out = out.masked_fill(key_padding_mask.unsqueeze(-1), 0.0)
        return out


class MLADecoderLayer(nn.Module):
    def __init__(self, dim: int, num_heads: int, kv_rank: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = LowRankMultiheadAttention(dim, num_heads, kv_rank, dropout)
        self.dropout = nn.Dropout(dropout)

        self.norm2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, key_padding_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        attn_out = self.attn(self.norm1(x), key_padding_mask=key_padding_mask)
        x = x + self.dropout(attn_out)
        ffn_out = self.ffn(self.norm2(x))
        x = x + ffn_out
        return x


class SignLanguageModel(nn.Module):
    """CTC-ready sequence model with low-rank attention."""

    def __init__(
        self,
        num_classes: int,
        input_dim: int = 225,
        hidden_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        kv_rank: int = 16,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_proj = InputProjection(in_dim=input_dim, hidden_dim=hidden_dim, dropout=dropout)
        self.layers = nn.ModuleList(
            [MLADecoderLayer(hidden_dim, num_heads, kv_rank, dropout) for _ in range(num_layers)]
        )
        self.classifier = nn.Linear(hidden_dim, num_classes + 1)

    def forward(self, x: torch.Tensor, input_lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x: [B, T, 225]
        h = self.input_proj(x)

        key_padding_mask = None
        if input_lengths is not None:
            # True means padded position.
            time_index = torch.arange(h.shape[1], device=h.device)
            key_padding_mask = time_index[None, :] >= input_lengths[:, None]

        for layer in self.layers:
            h = layer(h, key_padding_mask=key_padding_mask)

        logits = self.classifier(h)
        # log_probs: [B, T, C]
        return F.log_softmax(logits, dim=-1)
