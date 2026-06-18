"""
Extract MediaPipe Holistic 225‑dim features from HKSL‑LEX videos,
generate gloss‑to‑ID mapping, and produce the manifest expected by dataset.py.

Usage:
    python src/extract_hksllex_rich_features.py \
        --json data.json \
        --video_dir /path/to/videos \
        --out_dir data
"""

import argparse
import csv
import json
import os
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import torch
from PIL import Image, ImageSequence


# ------------------------------------------------------------------------------
# MediaPipe setup (lazy initialised inside each worker)
# ------------------------------------------------------------------------------

def _init_holistic():
    """Create a new MediaPipe Holistic instance inside a worker process."""
    mp_holistic = mp.solutions.holistic
    return mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )


# ------------------------------------------------------------------------------
# Frame extraction helpers
# ------------------------------------------------------------------------------

def _extract_frames_from_mp4(video_path: str, max_frames: int = 1000) -> List[np.ndarray]:
    """Read all frames from an .mp4 video using OpenCV."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret or len(frames) >= max_frames:
            break
        # Convert BGR to RGB (MediaPipe expects RGB)
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames


def _extract_frames_from_webp(video_path: str, max_frames: int = 1000) -> List[np.ndarray]:
    """Read all frames from an animated .webp using PIL."""
    img = Image.open(video_path)
    frames = []
    for frame in ImageSequence.Iterator(img):
        # Convert to RGB numpy array
        frame_np = np.array(frame.convert('RGB'))
        frames.append(frame_np)
        if len(frames) >= max_frames:
            break
    return frames


# ------------------------------------------------------------------------------
# 225‑dim landmark extraction (gold standard)
# ------------------------------------------------------------------------------

# Indices for the 11 pose joints (MediaPipe Pose landmark indices)
# Selected: nose(0), left_shoulder(11), right_shoulder(12), left_elbow(13),
# right_elbow(14), left_wrist(15), right_wrist(16), left_hip(23), right_hip(24),
# left_index(19), right_index(20)  (index finger tips)
_POSE_INDICES = [0, 11, 12, 13, 14, 15, 16, 23, 24, 19, 20]

# Indices for the 22 face landmarks (MediaPipe FaceMesh indices)
# Selected for grammatical facial markers: eyebrows, eyes, lips.
_FACE_INDICES = [
    46, 53, 52, 65, 55,   # left eyebrow
    285, 276, 283, 282, 295,  # right eyebrow
    33, 133, 159, 145,  # left eye
    362, 263, 386, 374,  # right eye
    61, 291, 13, 14,  # mouth corners + upper/lower lip
]


def _extract_landmarks(frame: np.ndarray, holistic) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Run MediaPipe Holistic on a single RGB frame.
    Returns (hand_landmarks, pose_landmarks, face_landmarks) as arrays of shape (N,3)
    or None if the frame is invalid.
    """
    results = holistic.process(frame)
    if not results.pose_landmarks and not results.left_hand_landmarks and not results.right_hand_landmarks:
        # No meaningful landmarks; fallback to all zeros.
        pass

    # ---------- Hands (126 dims) ----------
    # Left hand: 21 points x3, right hand: 21 points x3.
    def _hand_array(hand_landmarks):
        if hand_landmarks:
            arr = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
            return arr.flatten()  # 63 dims
        return np.zeros(63, dtype=np.float32)

    left_hand = _hand_array(results.left_hand_landmarks)
    right_hand = _hand_array(results.right_hand_landmarks)
    hands = np.concatenate([left_hand, right_hand])  # 126

    # ---------- Pose (33 dims) ----------
    if results.pose_landmarks:
        # Take only the selected 11 joints
        pose_pts = np.array([[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark])
        pose_selected = pose_pts[_POSE_INDICES]  # (11,3)
        pose = pose_selected.flatten()  # 33
    else:
        pose = np.zeros(33, dtype=np.float32)

    # ---------- Face (66 dims) ----------
    if results.face_landmarks:
        face_pts = np.array([[lm.x, lm.y, lm.z] for lm in results.face_landmarks.landmark])
        face_selected = face_pts[_FACE_INDICES]  # (22,3)
        face = face_selected.flatten()  # 66
    else:
        face = np.zeros(66, dtype=np.float32)

    return hands, pose, face


def _frame_to_feature(frame: np.ndarray, holistic) -> Optional[np.ndarray]:
    """Convert one RGB frame to a 225‑dim feature vector."""
    landmarks = _extract_landmarks(frame, holistic)
    if landmarks is None:
        return None
    hands, pose, face = landmarks
    return np.concatenate([hands, pose, face])  # 126+33+66 = 225


# ------------------------------------------------------------------------------
# Video processing worker (runs in a separate process)
# ------------------------------------------------------------------------------

@dataclass
class VideoResult:
    """Container for the extracted data of one video."""
    id: str
    english: str
    chinese: str
    cantonese: str
    feature_path: str   # relative path to saved .pt file
    input_length: int   # number of frames
    target_ids: List[int]   # mapping will be applied later


def _process_video(
    entry: dict,
    video_dir: str,
    features_dir: str,
    gloss_to_id: Dict[str, int],
) -> Optional[VideoResult]:
    """
    Process a single entry from data.json.
    This function is called by each worker process.
    """
    # Extract metadata
    meta = entry.get("HKU_HKSLLEX_ID", {})
    vid = meta.get("id")
    if not vid:
        return None

    translations = entry.get("translation", {})
    en_gloss = translations.get("EN-GB", {}).get("primary")
    zh_gloss = translations.get("ZH-HK", {}).get("primary")
    yue_gloss = translations.get("ZH-Yue", {}).get("primary")
    if not en_gloss:
        warnings.warn(f"Entry {vid} has no EN-GB primary gloss, skipping.")
        return None

    # Find video file
    video_files = entry.get("videoFile", {})
    mp4_name = video_files.get("nameOSF")
    webp_name = video_files.get("nameGIF")
    video_path = None
    if mp4_name:
        candidate = os.path.join(video_dir, mp4_name)
        if os.path.isfile(candidate):
            video_path = candidate
    if not video_path and webp_name:
        candidate = os.path.join(video_dir, webp_name)
        if os.path.isfile(candidate):
            video_path = candidate
    if not video_path:
        warnings.warn(f"Video not found for {vid} (tried {mp4_name}, {webp_name}), skipping.")
        return None

    # Extract frames based on extension
    ext = os.path.splitext(video_path)[1].lower()
    if ext == '.mp4':
        frames = _extract_frames_from_mp4(video_path)
    elif ext in ('.webp', '.gif'):
        frames = _extract_frames_from_webp(video_path)
    else:
        warnings.warn(f"Unsupported video format for {vid}: {ext}, skipping.")
        return None

    if not frames:
        warnings.warn(f"No frames extracted from {vid}, skipping.")
        return None

    # Initialise MediaPipe Holistic inside the worker (critical for multiprocessing)
    holistic = _init_holistic()

    # Extract features frame by frame
    feature_list = []
    for frame in frames:
        feat = _frame_to_feature(frame, holistic)
        if feat is None:
            # If detection completely fails, we still want a zero vector
            feat = np.zeros(225, dtype=np.float32)
        feature_list.append(feat)

    # Stack into (T, 225)
    features = np.stack(feature_list, axis=0)  # (T, 225)
    input_length = features.shape[0]

    # Save as .pt tensor
    os.makedirs(features_dir, exist_ok=True)
    feat_path = os.path.join(features_dir, f"{vid}.pt")
    torch.save(torch.from_numpy(features).float(), feat_path)

    # Target IDs: we only have one gloss per video, but it could be multiple? 
    # The dataset.py expects a list of ints; we'll treat it as a single token.
    target_id = gloss_to_id.get(en_gloss)
    if target_id is None:
        # This should not happen if we pre‑built the mapping.
        target_id = 0  # fallback blank? Better to skip.
        warnings.warn(f"Gloss '{en_gloss}' not in mapping, skipping.")
        return None

    return VideoResult(
        id=vid,
        english=en_gloss,
        chinese=zh_gloss or "",
        cantonese=yue_gloss or "",
        feature_path=os.path.relpath(feat_path, start=os.getcwd()),
        input_length=input_length,
        target_ids=[target_id],
    )


# ------------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------------

def build_gloss_mapping(entries: List[dict]) -> Dict[str, int]:
    """Extract all unique EN-GB primary glosses and map them to IDs starting from 1."""
    gloss_set = set()
    for entry in entries:
        en = entry.get("translation", {}).get("EN-GB", {}).get("primary")
        if en:
            gloss_set.add(en)
    # Sort for deterministic order
    sorted_glosses = sorted(gloss_set)
    mapping = {gloss: idx + 1 for idx, gloss in enumerate(sorted_glosses)}  # blank=0
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Extract HKSL-LEX features")
    parser.add_argument("--json", required=True, help="Path to data.json")
    parser.add_argument("--video_dir", required=True, help="Directory containing video files")
    parser.add_argument("--out_dir", default="data", help="Output directory (default: data)")
    parser.add_argument("--num_workers", type=int, default=8,
                        help="Number of worker processes (default: 8)")
    args = parser.parse_args()

    # Load JSON
    with open(args.json, 'r', encoding='utf-8') as f:
        data = json.load(f)  # Expects a list of entries

    if not isinstance(data, list):
        raise ValueError("data.json must contain a JSON array.")

    print(f"Loaded {len(data)} entries.")

    # Build gloss mapping
    gloss_to_id = build_gloss_mapping(data)
    os.makedirs(os.path.join(args.out_dir), exist_ok=True)
    mapping_path = os.path.join(args.out_dir, "gloss_to_id.json")
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(gloss_to_id, f, indent=2, ensure_ascii=False)
    print(f"Gloss mapping saved to {mapping_path} ({len(gloss_to_id)} classes)")

    # Prepare directories
    features_dir = os.path.join(args.out_dir, "features")
    os.makedirs(features_dir, exist_ok=True)

    # Process videos in parallel
    results = []  # List of VideoResult
    with ProcessPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {}
        for entry in data:
            future = executor.submit(
                _process_video,
                entry,
                args.video_dir,
                features_dir,
                gloss_to_id,
            )
            futures[future] = entry

        for future in as_completed(futures):
            entry = futures[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
                    print(f"Processed {result.id} (frames={result.input_length})")
            except Exception as e:
                print(f"Error processing entry: {e}")

    print(f"Successfully processed {len(results)} videos.")

    # Generate manifest.csv
    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "path", "target", "input_lengths",
            "english_gloss", "chinese_gloss", "cantonese_gloss"
        ])
        for res in results:
            # target column: space-separated integers (CTC expects sequence)
            target_str = " ".join(str(t) for t in res.target_ids)
            writer.writerow([
                res.feature_path,
                target_str,
                res.input_length,
                res.english,
                res.chinese,
                res.cantonese,
            ])

    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()