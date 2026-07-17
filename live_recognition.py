#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
即時手語辨識 (Live Sign Language Recognition)
結合 MediaPipe Holistic (225維) + ONNX CTC 模型 + 骨架繪圖。
支援 Intel OpenVINO GPU 加速，若不可用則自動降級為 CPU。
"""

import cv2
import numpy as np
import onnxruntime as ort
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import json
import time
from collections import deque
from PIL import Image, ImageDraw, ImageFont

# ================== 設定路徑 ==================
MODEL_PATH = 'holistic_landmarker.task'      # MediaPipe 模型
ONNX_PATH = 'model/sign_language_mla.onnx'         # ONNX CTC 模型
GLOSS_MAP_PATH = 'data/gloss_to_id.json'     # gloss → ID

# ================== 載入 gloss 對照表 ==================
with open(GLOSS_MAP_PATH, 'r', encoding='utf-8') as f:
    gloss_to_id = json.load(f)
id_to_gloss = {v: k for k, v in gloss_to_id.items()}
id_to_gloss[0] = '<blank>'

# ================== 初始化 MediaPipe Holistic (Tasks API) ==================
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
holistic_options = vision.HolisticLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    min_face_detection_confidence=0.5,
    min_face_suppression_threshold=0.3,
    min_pose_detection_confidence=0.5,
    min_pose_suppression_threshold=0.3,
)
holistic = vision.HolisticLandmarker.create_from_options(holistic_options)

# ================== 初始化 ONNX 推論 (使用 DirectML 加速 Intel GPU) ==================
providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
ort_session = ort.InferenceSession(ONNX_PATH, providers=providers)
print(f"🧠 ONNX 執行引擎: {ort_session.get_providers()}")

# ================== 參數 ==================
SEQUENCE_LENGTH = 60          # 模型訓練時的固定幀數
FEATURE_DIM = 225
STEP_SIZE = 2                 # 每 N 幀推論一次，可調高提升流暢度

frame_buffer = deque(maxlen=SEQUENCE_LENGTH)
frame_counter = 0
current_text = ""

# 時間戳計數器（使用 perf_counter 保證遞增）
start_time_ns = time.perf_counter_ns()

def get_timestamp_ms():
    """返回自程式啟動後的毫秒數，保證單調遞增"""
    return (time.perf_counter_ns() - start_time_ns) // 1_000_000

# 中文字型候選
FONT_CANDIDATES = [
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_CACHE = {}

def get_chinese_font(size):
    if size not in FONT_CACHE:
        for path in FONT_CANDIDATES:
            try:
                FONT_CACHE[size] = ImageFont.truetype(path, size)
                break
            except:
                continue
        else:
            FONT_CACHE[size] = ImageFont.load_default()
    return FONT_CACHE[size]

def draw_chinese_text(img, text, pos, size=30, color=(0,255,0)):
    """在 OpenCV 圖片上繪製中文文字"""
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    draw.text(pos, text, font=get_chinese_font(size), fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ================== 225 維特徵抽取 (從 result 直接提取) ==================
POSE_INDICES = [0, 11, 12, 13, 14, 15, 16, 23, 24, 19, 20]
FACE_INDICES = [
    46, 53, 52, 65, 55,
    285, 276, 283, 282, 295,
    33, 133, 159, 145,
    362, 263, 386, 374,
    61, 291, 13, 14,
]

def normalize_landmark_list(landmark_data):
    """從各種可能的 landmarks 格式提取標準點列表 (list of NormalizedLandmark)"""
    if not landmark_data:
        return None
    # 如果是 NormalizedLandmarkList (有 .landmark)
    if hasattr(landmark_data, 'landmark'):
        return landmark_data.landmark
    # 如果是 list，且第一個元素有 .landmark，取第一個
    if isinstance(landmark_data, list) and landmark_data:
        if hasattr(landmark_data[0], 'landmark'):
            return landmark_data[0].landmark
        # 否則假設它已經是 NormalizedLandmark 的列表
        return landmark_data
    return None

def landmarks_to_xy(points, img_shape):
    """將 NormalizedLandmark 列表轉換為畫面上的 (x,y) 座標"""
    if not points:
        return []
    h, w = img_shape[:2]
    return [(int(lm.x * w), int(lm.y * h)) for lm in points]

def extract_features_from_result(result):
    """從 HolisticLandmarkerResult 抽取 225 維特徵（避免重複呼叫 detect）"""
    def hand_array(points):
        if points:
            arr = np.array([[lm.x, lm.y, lm.z] for lm in points])
            return arr.flatten()
        return np.zeros(63, dtype=np.float32)

    left_hand = hand_array(normalize_landmark_list(result.left_hand_landmarks))
    right_hand = hand_array(normalize_landmark_list(result.right_hand_landmarks))
    hands = np.concatenate([left_hand, right_hand])

    pose_points = normalize_landmark_list(result.pose_landmarks)
    if pose_points:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in pose_points])
        pose = pts[POSE_INDICES].flatten()
    else:
        pose = np.zeros(33, dtype=np.float32)

    face_points = normalize_landmark_list(result.face_landmarks)
    if face_points:
        pts = np.array([[lm.x, lm.y, lm.z] for lm in face_points])
        face = pts[FACE_INDICES].flatten()
    else:
        face = np.zeros(66, dtype=np.float32)

    return np.concatenate([hands, pose, face])

# ================== CTC 解碼 ==================
def ctc_greedy_decode(log_probs):
    pred_ids = np.argmax(log_probs, axis=1)
    decoded = []
    prev = -1
    for idx in pred_ids:
        if idx != prev and idx != 0:
            decoded.append(idx)
        prev = idx
    return [id_to_gloss.get(i, '?') for i in decoded]

# ================== 骨架連接定義 (手部、姿勢) ==================
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),       # 食指
    (0, 9), (9, 10), (10, 11), (11, 12),  # 中指
    (0, 13), (13, 14), (14, 15), (15, 16),# 無名指
    (0, 17), (17, 18), (18, 19), (19, 20),# 小指
    (5, 9), (9, 13), (13, 17)             # 掌心橫線
]

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15),          # 左臂
    (12, 14), (14, 16),                    # 右臂
    (11, 23), (12, 24), (23, 24),          # 軀幹
    (23, 25), (25, 27),                    # 左腿
    (24, 26), (26, 28),                    # 右腿
    (0, 11), (0, 12)                       # 頭到肩
]

# ================== 骨架繪圖函式 (使用點列表) ==================
def draw_hand_landmarks(img, points_list):
    """繪製手部骨架，points 為 (x,y) 座標列表"""
    for points in points_list:
        if len(points) != 21:  # 手部應有 21 點
            continue
        # 畫點
        for (x, y) in points:
            cv2.circle(img, (x, y), 4, (0, 255, 0), -1)
        # 畫連線
        for (start_idx, end_idx) in HAND_CONNECTIONS:
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(img, points[start_idx], points[end_idx], (255, 0, 0), 2)

def draw_pose_landmarks(img, points):
    """繪製姿勢骨架，points 為 (x,y) 座標列表"""
    if not points:
        return
    # 畫點
    for (x, y) in points:
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
    # 畫連線
    for (start_idx, end_idx) in POSE_CONNECTIONS:
        if start_idx < len(points) and end_idx < len(points):
            cv2.line(img, points[start_idx], points[end_idx], (0, 255, 255), 2)

def draw_face_landmarks(img, points):
    """繪製臉部網格 (簡化為點)"""
    if not points:
        return
    for (x, y) in points:
        cv2.circle(img, (x, y), 1, (255, 255, 0), -1)

# ================== 主程式 ==================
def main():
    global frame_counter, current_text

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("🚀 即時手語辨識已啟動，按 'q' 離開")

    fps_time = time.time()
    fps_count = 0
    fps_display = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ✅ 每幀只呼叫一次 detect_for_video，保證時間戳嚴格遞增
        timestamp_ms = get_timestamp_ms()
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = holistic.detect_for_video(mp_image, timestamp_ms)

        # 抽取 225 維特徵
        feature = extract_features_from_result(result)
        frame_buffer.append(feature)

        # 繪製骨架 (使用 normalize_landmark_list 確保格式一致)
        # 手部
        left_hand_points = normalize_landmark_list(result.left_hand_landmarks)
        right_hand_points = normalize_landmark_list(result.right_hand_landmarks)
        hands_points = []
        if left_hand_points:
            hands_points.append(landmarks_to_xy(left_hand_points, frame.shape))
        if right_hand_points:
            hands_points.append(landmarks_to_xy(right_hand_points, frame.shape))
        if hands_points:
            draw_hand_landmarks(frame, hands_points)

        # 姿勢
        pose_points = normalize_landmark_list(result.pose_landmarks)
        if pose_points:
            draw_pose_landmarks(frame, landmarks_to_xy(pose_points, frame.shape))

        # 臉部
        face_points = normalize_landmark_list(result.face_landmarks)
        if face_points:
            draw_face_landmarks(frame, landmarks_to_xy(face_points, frame.shape))

        # 推論控制
        frame_counter += 1
        if frame_counter % STEP_SIZE == 0 and len(frame_buffer) == SEQUENCE_LENGTH:
            input_tensor = np.array(frame_buffer, dtype=np.float32)[np.newaxis, :, :]
            lengths = np.array([SEQUENCE_LENGTH], dtype=np.int64)

            log_probs = ort_session.run(None, {
                "input": input_tensor,
                "input_lengths": lengths
            })[0]

            gloss_list = ctc_greedy_decode(log_probs[0])
            current_text = ' '.join(gloss_list)

        # 計算 FPS
        fps_count += 1
        if time.time() - fps_time >= 1.0:
            fps_display = fps_count
            fps_count = 0
            fps_time = time.time()

        # 顯示資訊
        cv2.putText(frame, f"Gloss: {current_text}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps_display}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        frame = draw_chinese_text(frame, "即時手語辨識", (10, 110), size=24, color=(0,255,0))

        cv2.imshow('Live Sign Language Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()