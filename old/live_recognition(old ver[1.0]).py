#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import numpy as np
import onnxruntime as ort
import json
import os
from collections import deque

# --------------- 設定路徑 ---------------
MODEL_PATH = 'holistic_landmarker.task'          # MediaPipe 模型
ONNX_PATH = 'sign_language_mla.onnx'             # ONNX 模型
GLOSS_MAP_PATH = 'data/gloss_to_id.json'         # gloss 對照表

# --------------- 載入 gloss 對照 ---------------
with open(GLOSS_MAP_PATH, 'r', encoding='utf-8') as f:
    gloss_to_id = json.load(f)
id_to_gloss = {v: k for k, v in gloss_to_id.items()}
id_to_gloss[0] = '<blank>'

# --------------- 初始化 MediaPipe Holistic ---------------
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HolisticLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    min_face_detection_confidence=0.5,
    min_face_suppression_threshold=0.3,
    min_pose_detection_confidence=0.5,
    min_pose_suppression_threshold=0.3,
)
holistic = vision.HolisticLandmarker.create_from_options(options)

# --------------- 初始化 ONNX 推論引擎 ---------------
ort_session = ort.InferenceSession(ONNX_PATH)

# --------------- 參數 ---------------
SEQUENCE_LENGTH = 60          # 模型輸入的固定幀數
FEATURE_DIM = 225             # 特徵維度
STEP_SIZE = 2                 # 每隔多少幀進行一次推論（降低 CPU 負擔）
WINDOW_STRIDE = 30            # 滑動窗口步幅（可重疊）
frame_buffer = deque(maxlen=SEQUENCE_LENGTH)   # 儲存特徵的佇列
frame_counter = 0

# --------------- 特徵抽取 (與 extract 腳本相同) ---------------
_POSE_INDICES = [0, 11, 12, 13, 14, 15, 16, 23, 24, 19, 20]
_FACE_INDICES = [
    46, 53, 52, 65, 55,
    285, 276, 283, 282, 295,
    33, 133, 159, 145,
    362, 263, 386, 374,
    61, 291, 13, 14,
]

def _normalize_landmark_list(landmark_data):
    if not landmark_data:
        return None
    if hasattr(landmark_data, 'landmark'):
        return landmark_data.landmark
    if isinstance(landmark_data, list) and landmark_data:
        if hasattr(landmark_data[0], 'landmark'):
            return landmark_data[0].landmark
        return landmark_data
    return None

def extract_225_features(frame_rgb, timestamp_ms):
    """從 RGB 影像抽取 225 維 Holistic 特徵"""
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    result = holistic.detect_for_video(mp_image, timestamp_ms)

    def _hand_array(points):
        if points:
            arr = np.array([[lm.x, lm.y, lm.z] for lm in points])
            return arr.flatten()
        return np.zeros(63, dtype=np.float32)

    left_hand = _hand_array(_normalize_landmark_list(result.left_hand_landmarks))
    right_hand = _hand_array(_normalize_landmark_list(result.right_hand_landmarks))
    hands = np.concatenate([left_hand, right_hand])

    if result.pose_landmarks:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in _normalize_landmark_list(result.pose_landmarks)])
        pose = pts[_POSE_INDICES].flatten()
    else:
        pose = np.zeros(33, dtype=np.float32)

    if result.face_landmarks:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in _normalize_landmark_list(result.face_landmarks)])
        face = pts[_FACE_INDICES].flatten()
    else:
        face = np.zeros(66, dtype=np.float32)

    return np.concatenate([hands, pose, face])  # 225

# --------------- CTC 貪婪解碼 ---------------
def ctc_greedy_decode(log_probs):
    """log_probs: (T, C) numpy array"""
    pred_ids = np.argmax(log_probs, axis=1)
    decoded = []
    prev = -1
    for idx in pred_ids:
        if idx != prev and idx != 0:  # skip blank and repeated
            decoded.append(idx)
        prev = idx
    return [id_to_gloss.get(i, '?') for i in decoded]

# --------------- 主迴圈 ---------------
cap = cv2.VideoCapture(0)  # 0 為預設鏡頭
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

fps_time = 0
current_text = ""

print("即時手語辨識啟動，按 'q' 離開")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)  # 鏡像翻轉
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 計算時間戳（毫秒），使用系統時間或幀計數近似
    timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)

    # 抽取特徵
    feature = extract_225_features(frame_rgb, timestamp_ms)
    frame_buffer.append(feature)

    # 每隔 STEP_SIZE 幀進行一次推論
    frame_counter += 1
    if frame_counter % STEP_SIZE == 0 and len(frame_buffer) == SEQUENCE_LENGTH:
        # 準備模型輸入： (1, T, 225)
        input_tensor = np.array(frame_buffer, dtype=np.float32)[np.newaxis, :, :]
        lengths = np.array([SEQUENCE_LENGTH], dtype=np.int64)

        # ONNX 推論
        log_probs = ort_session.run(None, {
            "input": input_tensor,
            "input_lengths": lengths
        })[0]  # shape (1, T, num_classes+1)

        # 解碼
        current_text = ' '.join(ctc_greedy_decode(log_probs[0]))

    # 顯示結果
    cv2.putText(frame, f"Gloss: {current_text}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # FPS
    if fps_time == 0:
        fps_time = cv2.getTickCount()
    else:
        new_time = cv2.getTickCount()
        fps = cv2.getTickFrequency() / (new_time - fps_time)
        fps_time = new_time
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

    cv2.imshow('Live Sign Language Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()