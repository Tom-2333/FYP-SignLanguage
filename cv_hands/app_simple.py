"""
Simplified gesture detection server using legacy MediaPipe Hands API
No .task model files required!
"""
import cv2 as cv
import mediapipe as mp
import numpy as np
import math
import copy
import os
import platform
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from collections import deque
import uvicorn

from model import KeyPointClassifier, KeyPointSequenceClassifier

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# FastAPI app for API
app = FastAPI(title="Gesture Detection API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variables for gesture results
current_gesture_data = {
    "hand_sign_text": "",
    "finger_gesture_text": "",
    "sequence_gesture_text": "",
    "handedness": "",
    "fps": 0
}
latest_frame = None
frame_lock = threading.Lock()

# Initialize MediaPipe Solutions (legacy API - no model files needed)
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

TARGET_FPS = int(os.getenv("TARGET_FPS", "30"))
ENABLE_FACE_POSE = os.getenv("ENABLE_FACE_POSE", "1") == "1"
FACE_POSE_INTERVAL = int(os.getenv("FACE_POSE_INTERVAL", "1"))
HANDS_MODEL_COMPLEXITY = int(os.getenv("HANDS_MODEL_COMPLEXITY", "1"))
POSE_MODEL_COMPLEXITY = int(os.getenv("POSE_MODEL_COMPLEXITY", "1"))

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=HANDS_MODEL_COMPLEXITY,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.6
)

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.6
)

pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=POSE_MODEL_COMPLEXITY,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.6
)

# Load gesture classifiers with absolute paths
keypoint_classifier = KeyPointClassifier(
    model_path=os.path.join(SCRIPT_DIR, 'model/keypoint_classifier/keypoint_classifier.tflite')
)
keypoint_sequence_classifier = KeyPointSequenceClassifier(
    model_path=os.path.join(SCRIPT_DIR, 'model/keypoint_classifier/keypoint_sequence_classifier.tflite')
)

# Read labels with absolute paths
with open(os.path.join(SCRIPT_DIR, 'Word-Label/keypoint_classifier_label.csv'), encoding='utf-8-sig') as f:
    keypoint_classifier_labels = [row[0] for row in __import__('csv').reader(f)]

try:
    with open(os.path.join(SCRIPT_DIR, 'Word-Label/keypoint_sequence_classifier_label.csv'), encoding='utf-8-sig') as f:
        keypoint_sequence_classifier_labels = [row[0] for row in __import__('csv').reader(f)]
except FileNotFoundError:
    keypoint_sequence_classifier_labels = []

# Sequence history
sequence_length = 25
keypoint_sequence = deque(maxlen=sequence_length)
sequence_gesture_history = deque(maxlen=5)
SEQUENCE_CONF_THRESHOLD = 0.8
ZERO_FEATURE_VECTOR = [0.0] * 80


def open_camera():
    """Try to open a camera without blocking the browser's default device."""
    preferred = os.getenv("CAMERA_INDEX")
    candidates = []
    if preferred is not None:
        try:
            candidates.append(int(preferred))
        except ValueError:
            pass

    if not candidates:
        if platform.system().lower().startswith("win"):
            candidates = [0, 1, 2]
        else:
            candidates = [0]

    for index in candidates:
        cap = cv.VideoCapture(index)
        if cap.isOpened():
            return cap, index
        cap.release()

    return None, None


def calc_landmark_list(image, landmarks):
    """Convert MediaPipe landmarks to list of coordinates"""
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point.append([landmark_x, landmark_y])
    return landmark_point


def extract_face_features(face_landmarks, image):
    """Extract face features: head pose, eye gaze, mouth openness"""
    try:
        if face_landmarks is None or image is None:
            return [0.0] * 10

        features = []

        # Head pose estimation using facial landmarks
        nose = face_landmarks.landmark[1]
        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        left_ear = face_landmarks.landmark[234]
        right_ear = face_landmarks.landmark[454]

        eye_center_x = (left_eye.x + right_eye.x) / 2
        eye_center_y = (left_eye.y + right_eye.y) / 2

        # Yaw, Pitch, Roll
        yaw = right_ear.x - left_ear.x
        pitch = nose.y - eye_center_y
        roll = right_eye.y - left_eye.y
        features.extend([yaw, pitch, roll])

        # Eye openness
        left_eye_top = face_landmarks.landmark[160].y
        left_eye_bottom = face_landmarks.landmark[144].y
        right_eye_top = face_landmarks.landmark[385].y
        right_eye_bottom = face_landmarks.landmark[380].y
        left_eye_openness = left_eye_top - left_eye_bottom
        right_eye_openness = right_eye_top - right_eye_bottom
        features.extend([left_eye_openness, right_eye_openness])

        # Mouth openness
        upper_lip = face_landmarks.landmark[13].y
        lower_lip = face_landmarks.landmark[14].y
        mouth_openness = lower_lip - upper_lip
        features.append(mouth_openness)

        # Eye gaze direction
        left_eye_left = face_landmarks.landmark[133].x
        left_eye_right = face_landmarks.landmark[33].x
        right_eye_left = face_landmarks.landmark[263].x
        right_eye_right = face_landmarks.landmark[362].x
        left_gaze_x = (left_eye_left + left_eye_right) / 2 - nose.x
        right_gaze_x = (right_eye_left + right_eye_right) / 2 - nose.x
        features.extend([left_gaze_x, right_gaze_x])

        return features
    except (AttributeError, IndexError, TypeError):
        return [0.0] * 10


def extract_pose_features(pose_landmarks, image):
    """Extract pose features: shoulder positions, torso orientation"""
    try:
        if pose_landmarks is None or image is None:
            return [0.0] * 8

        features = []

        # Key pose landmarks
        left_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
        nose = pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]

        # Shoulder displacement and orientation
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        shoulder_width = right_shoulder.x - left_shoulder.x
        shoulder_height_diff = right_shoulder.y - left_shoulder.y
        features.extend([shoulder_center_x, shoulder_center_y, shoulder_width, shoulder_height_diff])

        # Torso rotation and lean
        hip_center_x = (left_hip.x + right_hip.x) / 2
        hip_center_y = (left_hip.y + right_hip.y) / 2
        torso_lean_x = shoulder_center_x - hip_center_x
        torso_lean_y = shoulder_center_y - hip_center_y
        features.extend([torso_lean_x, torso_lean_y])

        # Head position relative to shoulders
        head_to_shoulder_x = nose.x - shoulder_center_x
        head_to_shoulder_y = nose.y - shoulder_center_y
        features.extend([head_to_shoulder_x, head_to_shoulder_y])

        return features
    except (AttributeError, IndexError, TypeError):
        return [0.0] * 8


def compute_relative_positions(hand_landmarks, face_features, pose_features, image):
    """Compute relative positions of hand to face and body parts"""
    try:
        if hand_landmarks is None or image is None:
            return [0.0] * 22

        image_width, image_height = image.shape[1], image.shape[0]
        features = []

        # Key hand landmarks
        wrist = hand_landmarks[0]
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]

        # Normalize coordinates
        wrist_x = wrist[0] / image_width
        wrist_y = wrist[1] / image_height
        index_x = index_tip[0] / image_width
        index_y = index_tip[1] / image_height
        middle_x = middle_tip[0] / image_width
        middle_y = middle_tip[1] / image_height

        # Hand relative to shoulders
        if len(pose_features) >= 8:
            shoulder_center_x, shoulder_center_y = pose_features[0], pose_features[1]
            hand_to_shoulder_x = wrist_x - shoulder_center_x
            hand_to_shoulder_y = wrist_y - shoulder_center_y
            index_to_shoulder_x = index_x - shoulder_center_x
            index_to_shoulder_y = index_y - shoulder_center_y
            features.extend([hand_to_shoulder_x, hand_to_shoulder_y, index_to_shoulder_x, index_to_shoulder_y])

            torso_center_x = shoulder_center_x
            torso_center_y = (shoulder_center_y + pose_features[6]) / 2
            hand_rel_torso_x = wrist_x - torso_center_x
            hand_rel_torso_y = wrist_y - torso_center_y
            features.extend([hand_rel_torso_x, hand_rel_torso_y])
        else:
            features.extend([0.0] * 6)

        # Hand relative to head
        if len(face_features) >= 10:
            head_center_x = 0.5
            head_center_y = 0.3
            hand_to_head_x = wrist_x - head_center_x
            hand_to_head_y = wrist_y - head_center_y
            index_to_head_x = index_x - head_center_x
            index_to_head_y = index_y - head_center_y
            features.extend([hand_to_head_x, hand_to_head_y, index_to_head_x, index_to_head_y])
        else:
            features.extend([0.0] * 4)

        # Hand extension
        index_extension = math.sqrt((index_x - wrist_x)**2 + (index_y - wrist_y)**2)
        middle_extension = math.sqrt((middle_x - wrist_x)**2 + (middle_y - wrist_y)**2)
        features.extend([index_extension, middle_extension])

        # Elbow placeholders
        features.extend([0.0, 0.0])

        # Pad to 22 features
        while len(features) < 22:
            features.append(0.0)

        return features
    except (AttributeError, IndexError, TypeError, ZeroDivisionError):
        return [0.0] * 22


def pre_process_landmark(landmark_list, face_landmarks=None, pose_landmarks=None, image=None, use_legacy_mode=False):
    """Match training pipeline: recenter to face/shoulder when available and normalize full 80-dim vector"""
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Extract face/pose features first (pixel space)
    face_features = extract_face_features(face_landmarks, image)
    pose_features = extract_pose_features(pose_landmarks, image)

    # Compute relative positions in pixel space
    relative_features = compute_relative_positions(temp_landmark_list, face_features, pose_features, image)

    # Choose reference point
    base_x, base_y = 0, 0
    if use_legacy_mode:
        base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]
    else:
        if face_landmarks and image is not None:
            image_width, image_height = image.shape[1], image.shape[0]
            nose_x = int(face_landmarks.landmark[1].x * image_width)
            nose_y = int(face_landmarks.landmark[1].y * image_height)
            base_x, base_y = nose_x, nose_y
        elif pose_landmarks and image is not None:
            image_width, image_height = image.shape[1], image.shape[0]
            left_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            shoulder_x = int(((left_shoulder.x + right_shoulder.x) / 2) * image_width)
            shoulder_y = int(((left_shoulder.y + right_shoulder.y) / 2) * image_height)
            base_x, base_y = shoulder_x, shoulder_y
        else:
            base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]

    # Convert to relative coordinates
    for i in range(len(temp_landmark_list)):
        temp_landmark_list[i][0] -= base_x
        temp_landmark_list[i][1] -= base_y

    # Save 2D landmarks for relative position computation (already relative to base)
    hand_landmarks_2d = temp_landmark_list.copy()

    # Flatten and normalize hand landmarks
    temp_landmark_list = [coord for point in temp_landmark_list for coord in point]
    max_value = max(list(map(abs, temp_landmark_list))) if temp_landmark_list else 1
    temp_landmark_list = [n / max_value if max_value != 0 else n for n in temp_landmark_list]

    if use_legacy_mode:
        return temp_landmark_list  # Only 42 dims

    # Recompute relative features using relative coords for consistency
    relative_features = compute_relative_positions(hand_landmarks_2d, face_features, pose_features, image)

    # Concatenate: hand(42) + face(10) + pose(8) + relative(20)
    relative_features = relative_features[:20]
    all_features = temp_landmark_list + face_features + pose_features + relative_features

    # Normalize the full vector to match training
    max_value_all = max(list(map(abs, all_features))) if all_features else 1
    all_features = [n / max_value_all if max_value_all != 0 else n for n in all_features]

    # Ensure exactly 80 features
    if len(all_features) < 80:
        all_features.extend([0.0] * (80 - len(all_features)))
    elif len(all_features) > 80:
        all_features = all_features[:80]

    return all_features


def gesture_detection_loop():
    """Main gesture detection loop running in separate thread"""
    global current_gesture_data
    global latest_frame
    
    cap, cam_index = open_camera()
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    if TARGET_FPS > 0:
        cap.set(cv.CAP_PROP_FPS, TARGET_FPS)
    
    if not cap or not cap.isOpened():
        print("❌ ERROR: Cannot open camera! Check if camera is available.")
        return
    print(f"📷 Using camera index: {cam_index}")
    
    fps_time = time.time()
    fps_counter = 0
    current_fps = 0
    detection_count = 0
    last_detection_time = time.time()
    frame_index = 0
    last_face_landmarks = None
    last_pose_landmarks = None
    last_pre_processed_landmark = None
    
    print("🎥 Camera started - Gesture detection active!")
    print("👋 Show your hand to the camera to test detection...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("❌ ERROR: Failed to read frame from camera")
            break
        
        # Calculate FPS
        fps_counter += 1
        if time.time() - fps_time >= 1.0:
            current_fps = fps_counter
            fps_counter = 0
            fps_time = time.time()
            
            # Log detection status every second
            if detection_count > 0:
                print(f"✅ Hands detected: {detection_count} times in last second")
                detection_count = 0
            elif time.time() - last_detection_time > 5:
                print("⚠️  No hands detected for 5+ seconds. Show your hand to the camera!")
        
        # Flip frame horizontally for selfie view
        frame = cv.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        
        # Process with all MediaPipe models
        hands_results = hands.process(frame_rgb)
        if ENABLE_FACE_POSE and (frame_index % max(FACE_POSE_INTERVAL, 1) == 0):
            face_results = face_mesh.process(frame_rgb)
            pose_results = pose.process(frame_rgb)
            last_face_landmarks = face_results.multi_face_landmarks[0] if face_results.multi_face_landmarks else None
            last_pose_landmarks = pose_results.pose_landmarks if pose_results.pose_landmarks else None
        
        hand_sign_text = ""
        sequence_gesture_text = ""
        handedness_text = ""
        
        # Extract face and pose landmarks
        face_landmarks = last_face_landmarks if ENABLE_FACE_POSE else None
        pose_landmarks = last_pose_landmarks if ENABLE_FACE_POSE else None
        
        if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
            detection_count += 1
            last_detection_time = time.time()
            for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks, hands_results.multi_handedness):
                # Get hand label (Left/Right)
                handedness_text = handedness.classification[0].label
                
                # Convert landmarks to list
                landmark_list = calc_landmark_list(frame, hand_landmarks)
                
                # Preprocess for classification with multi-modal features
                pre_processed_landmark = pre_process_landmark(
                    landmark_list, 
                    face_landmarks=face_landmarks,
                    pose_landmarks=pose_landmarks,
                    image=frame
                )
                
                # Hand sign classification
                hand_sign_result = keypoint_classifier(pre_processed_landmark)
                # Handle both integer and tuple returns
                hand_sign_id = hand_sign_result[0] if isinstance(hand_sign_result, tuple) else hand_sign_result
                
                if hand_sign_id < len(keypoint_classifier_labels):
                    hand_sign_text = keypoint_classifier_labels[hand_sign_id]
                
                # Sequence gesture classification (enqueue current frame)
                keypoint_sequence.append(pre_processed_landmark)
                last_pre_processed_landmark = pre_processed_landmark
                
                # Draw hand landmarks on frame for debugging
                mp_drawing.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
        else:
            # No hand detected: pad sequence with last known frame (or zeros)
            if last_pre_processed_landmark is not None:
                keypoint_sequence.append(last_pre_processed_landmark)
            else:
                keypoint_sequence.append(list(ZERO_FEATURE_VECTOR))

        # Sequence classification (run every frame once enough frames are collected)
        if len(keypoint_sequence) >= sequence_length:
            seq = list(keypoint_sequence)
            if len(seq) < sequence_length:
                seq.extend([seq[-1]] * (sequence_length - len(seq)))

            sequence_gesture_result = keypoint_sequence_classifier(seq)
            if isinstance(sequence_gesture_result, tuple):
                sequence_gesture_id, sequence_confidence = sequence_gesture_result
            else:
                sequence_gesture_id, sequence_confidence = sequence_gesture_result, 0.0

            # Model uses 1-based ids; labels are 0-based
            label_index = None
            if sequence_gesture_id - 1 >= 0 and sequence_gesture_id - 1 < len(keypoint_sequence_classifier_labels):
                label_index = sequence_gesture_id - 1

            if label_index is not None and sequence_confidence >= SEQUENCE_CONF_THRESHOLD:
                sequence_gesture_history.append(label_index)
                # Majority vote over last few frames
                most_common = max(set(sequence_gesture_history), key=sequence_gesture_history.count)
                sequence_gesture_text = keypoint_sequence_classifier_labels[most_common]
        
        # Draw face and pose landmarks (optional - for debugging)
        # if face_landmarks:
        #     mp_drawing.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)
        # if pose_landmarks:
        #     mp_drawing.draw_landmarks(frame, pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # Display current detection info on frame
        if hand_sign_text or sequence_gesture_text:
            display_text = f"Hand: {hand_sign_text}"
            if sequence_gesture_text:
                display_text += f" | Sequence: {sequence_gesture_text}"
            cv.putText(frame, display_text, (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show FPS
        cv.putText(frame, f"FPS: {current_fps}", (10, frame.shape[0] - 10),
                  cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display the frame (OPTIONAL - disabled due to threading issues on macOS)
        # To enable window display, run this script directly instead of through Flask
        # Uncomment the lines below:
        # cv.imshow('Gesture Detection - Python Camera', frame)
        # if cv.waitKey(1) & 0xFF == ord('q'):
        #     print("👋 Closing gesture detection...")
        #     break
        
        # Update global gesture data
        current_gesture_data.update({
            "hand_sign_text": hand_sign_text,
            "finger_gesture_text": handedness_text,
            "sequence_gesture_text": sequence_gesture_text,
            "handedness": handedness_text,
            "fps": current_fps
        })
        # Store latest frame for browser streaming
        success, jpeg = cv.imencode('.jpg', frame)
        if success:
            with frame_lock:
                latest_frame = jpeg.tobytes()
        frame_index += 1
        
        # Small delay to prevent excessive CPU usage
        # time.sleep(0.01)  # Removed to maximize detection speed
    
    cap.release()
    cv.destroyAllWindows()
    print("Camera closed")


@app.get('/gesture')
async def get_gesture():
    """API endpoint to get current gesture data"""
    return JSONResponse(content=current_gesture_data)


def mjpeg_stream():
    """Yield MJPEG frames for browser preview."""
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.05)
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)


@app.get('/stream')
async def stream():
    """MJPEG stream for the browser camera preview."""
    return StreamingResponse(mjpeg_stream(), media_type='multipart/x-mixed-replace; boundary=frame')


@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "online", "gesture_detection": "active"})


if __name__ == '__main__':
    # Start gesture detection in separate thread
    detection_thread = threading.Thread(target=gesture_detection_loop, daemon=True)
    detection_thread.start()
    
    print("=" * 60)
    print("🚀 Gesture Detection Server Starting...")
    print("=" * 60)
    print("📡 FastAPI Server: http://localhost:5001")
    print("🔍 Gesture endpoint: http://localhost:5001/gesture")
    print("💚 Health check: http://localhost:5001/health")
    print("📺 Stream endpoint: http://localhost:5001/stream")
    print("📖 API Docs: http://localhost:5001/docs")
    print("=" * 60)
    
    # Start FastAPI server with uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001, log_level="info")
