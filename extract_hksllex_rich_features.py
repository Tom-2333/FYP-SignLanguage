"""
Extract MediaPipe Holistic 225-dim features from HKSL-LEX videos,
generate gloss-to-ID mapping, and produce the manifest expected by dataset.py.
Updated for MediaPipe 0.10.x Tasks API (robust landmark extraction).

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
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import numpy as np
import torch
from PIL import Image, ImageSequence


# ------------------------------------------------------------------------------
# MediaPipe setup (lazy initialised inside each worker)
# ------------------------------------------------------------------------------

MODEL_PATH = 'holistic_landmarker.task'


def _init_holistic():
    """Create a new MediaPipe HolisticLandmarker instance inside a worker process."""
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HolisticLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        min_face_detection_confidence=0.5,
        min_face_suppression_threshold=0.3,
        min_pose_detection_confidence=0.5,
        min_pose_suppression_threshold=0.3,
        # Hand confidence is handled internally by the model
    )
    return vision.HolisticLandmarker.create_from_options(options)


# ------------------------------------------------------------------------------
# Frame extraction helpers
# ------------------------------------------------------------------------------

def _extract_frames_from_mp4(video_path: str, max_frames: int = 1000) -> List[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret or len(frames) >= max_frames:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames


def _extract_frames_from_webp(video_path: str, max_frames: int = 1000) -> List[np.ndarray]:
    img = Image.open(video_path)
    frames = []
    for frame in ImageSequence.Iterator(img):
        frame_np = np.array(frame.convert('RGB'))
        frames.append(frame_np)
        if len(frames) >= max_frames:
            break
    return frames


# ------------------------------------------------------------------------------
# 225-dim landmark extraction (gold standard)
# ------------------------------------------------------------------------------

_POSE_INDICES = [0, 11, 12, 13, 14, 15, 16, 23, 24, 19, 20]

_FACE_INDICES = [
    46, 53, 52, 65, 55,
    285, 276, 283, 282, 295,
    33, 133, 159, 145,
    362, 263, 386, 374,
    61, 291, 13, 14,
]


def _normalize_landmark_list(landmark_data):
    """
    Convert various possible return formats into a list of NormalizedLandmark.
    Handles:
      - NormalizedLandmarkList (has .landmark)
      - list of NormalizedLandmarkList (take first)
      - list of NormalizedLandmark (return as is)
      - None
    """
    if not landmark_data:
        return None
    # Single NormalizedLandmarkList object
    if hasattr(landmark_data, 'landmark'):
        return landmark_data.landmark
    # List of NormalizedLandmarkList objects
    if isinstance(landmark_data, list) and landmark_data:
        if hasattr(landmark_data[0], 'landmark'):
            return landmark_data[0].landmark
        # Assume list of NormalizedLandmark
        return landmark_data
    return None


def _extract_landmarks(frame: np.ndarray, holistic: vision.HolisticLandmarker,
                       timestamp_ms: int) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = holistic.detect_for_video(mp_image, timestamp_ms)

    # ---------- Hands (126 dims) ----------
    def _hand_array(points):
        if points:
            arr = np.array([[lm.x, lm.y, lm.z] for lm in points])
            return arr.flatten()
        return np.zeros(63, dtype=np.float32)

    left_hand = _hand_array(_normalize_landmark_list(result.left_hand_landmarks))
    right_hand = _hand_array(_normalize_landmark_list(result.right_hand_landmarks))
    hands = np.concatenate([left_hand, right_hand])  # 126

    # ---------- Pose (33 dims) ----------
    pose_points = _normalize_landmark_list(result.pose_landmarks)
    if pose_points:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in pose_points])
        pose_selected = pts[_POSE_INDICES]
        pose = pose_selected.flatten()  # 33
    else:
        pose = np.zeros(33, dtype=np.float32)

    # ---------- Face (66 dims) ----------
    face_points = _normalize_landmark_list(result.face_landmarks)
    if face_points:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in face_points])
        face_selected = pts[_FACE_INDICES]
        face = face_selected.flatten()  # 66
    else:
        face = np.zeros(66, dtype=np.float32)

    return hands, pose, face


def _frame_to_feature(frame: np.ndarray, holistic: vision.HolisticLandmarker,
                      timestamp_ms: int) -> Optional[np.ndarray]:
    landmarks = _extract_landmarks(frame, holistic, timestamp_ms)
    if landmarks is None:
        return None
    hands, pose, face = landmarks
    return np.concatenate([hands, pose, face])  # 225


# ------------------------------------------------------------------------------
# Video processing worker
# ------------------------------------------------------------------------------

@dataclass
class VideoResult:
    id: str
    english: str
    chinese: str
    cantonese: str
    feature_path: str
    input_length: int
    target_ids: List[int]


def _process_video(
    entry: dict,
    video_dir: str,
    features_dir: str,
    gloss_to_id: Dict[str, int],
) -> Optional[VideoResult]:
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

    holistic = _init_holistic()

    feature_list = []
    fps = 30.0
    frame_duration_ms = 1000.0 / fps
    for idx, frame in enumerate(frames):
        timestamp_ms = int(idx * frame_duration_ms)
        feat = _frame_to_feature(frame, holistic, timestamp_ms)
        if feat is None:
            feat = np.zeros(225, dtype=np.float32)
        feature_list.append(feat)

    features = np.stack(feature_list, axis=0)
    input_length = features.shape[0]

    os.makedirs(features_dir, exist_ok=True)
    feat_path = os.path.join(features_dir, f"{vid}.pt")
    torch.save(torch.from_numpy(features).float(), feat_path)

    target_id = gloss_to_id.get(en_gloss)
    if target_id is None:
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
    gloss_set = set()
    for entry in entries:
        en = entry.get("translation", {}).get("EN-GB", {}).get("primary")
        if en:
            gloss_set.add(en)
    sorted_glosses = sorted(gloss_set)
    return {gloss: idx + 1 for idx, gloss in enumerate(sorted_glosses)}


def main():
    parser = argparse.ArgumentParser(description="Extract HKSL-LEX features")
    parser.add_argument("--json", required=True, help="Path to data.json")
    parser.add_argument("--video_dir", required=True, help="Directory containing video files")
    parser.add_argument("--out_dir", default="data", help="Output directory")
    parser.add_argument("--num_workers", type=int, default=8, help="Number of worker processes")
    parser.add_argument("--model_path", default=None, help="Path to holistic_landmarker.task")
    args = parser.parse_args()

    if args.model_path:
        globals()['MODEL_PATH'] = args.model_path

    with open(args.json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("data.json must contain a JSON array.")

    print(f"Loaded {len(data)} entries.")

    gloss_to_id = build_gloss_mapping(data)
    os.makedirs(args.out_dir, exist_ok=True)
    mapping_path = os.path.join(args.out_dir, "gloss_to_id.json")
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(gloss_to_id, f, indent=2, ensure_ascii=False)
    print(f"Gloss mapping saved to {mapping_path} ({len(gloss_to_id)} classes)")

    features_dir = os.path.join(args.out_dir, "features")
    os.makedirs(features_dir, exist_ok=True)

    results = []
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

    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["path", "target", "input_lengths",
                         "english_gloss", "chinese_gloss", "cantonese_gloss"])
        for res in results:
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