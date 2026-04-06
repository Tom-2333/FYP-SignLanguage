#!/usr/bin/env python
# -*- coding: utf-8 -*-12
import argparse
import copy
import csv
import itertools
from collections import Counter, deque

import cv2 as cv
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
import math
import os
import sys
from google.protobuf import message_factory, symbol_database


def install_protobuf_compat_shims():
    if not hasattr(symbol_database.SymbolDatabase, 'GetPrototype'):
        def _symbol_db_get_prototype(self, descriptor):
            message_class = message_factory.GetMessageClass(descriptor)
            self.RegisterMessage(message_class)
            return message_class

        symbol_database.SymbolDatabase.GetPrototype = _symbol_db_get_prototype

    if not hasattr(message_factory.MessageFactory, 'GetPrototype'):
        def _message_factory_get_prototype(self, descriptor):
            return message_factory.GetMessageClass(descriptor)

        message_factory.MessageFactory.GetPrototype = _message_factory_get_prototype


install_protobuf_compat_shims()

import mediapipe as mp

from model import KeyPointClassifier, KeyPointSequenceClassifier
from utils import CvFpsCalc


def print_runtime_info():
    print("=" * 60)
    print(f"Python executable: {sys.executable}")
    try:
        import tensorflow as tf
        print(f"TensorFlow version: {tf.__version__}")
    except Exception as e:
        print(f"TensorFlow version: unavailable ({e})")
    print("=" * 60)


def draw_chinese_text(image, text, position, font_size=20, color=(255, 255, 255), bold=False):

    image_pil = Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", font_size)
                except:
                    try:
                        font = ImageFont.truetype("C:\\Windows\\Fonts\\simhei.ttf", font_size)
                    except:
                        font = ImageFont.load_default()

    if bold:
        draw.text(position, text, font=font, fill=color)
        draw.text((position[0] + 1, position[1]), text, font=font, fill=color)
    else:
        draw.text(position, text, font=font, fill=color)

    image_cv = cv.cvtColor(np.array(image_pil), cv.COLOR_RGB2BGR)
    return image_cv


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--width", help='cap width', type=int, default=960)
    parser.add_argument("--height", help='cap height', type=int, default=540)

    parser.add_argument('--use_static_image_mode', action='store_true')
    parser.add_argument("--min_detection_confidence",
                        help='min_detection_confidence',
                        type=float,
                        default=0.7)
    parser.add_argument("--min_tracking_confidence",
                        help='min_tracking_confidence',
                        type=float,
                        default=0.5)
    parser.add_argument("--sequence_confidence_threshold",
                        help='confidence threshold for sequence gesture display',
                        type=float,
                        default=0.35)

    args = parser.parse_args()

    return args


def main():
    print_runtime_info()
    # Argument parsing
    args = get_args()

    cap_device = args.device
    cap_width = args.width
    cap_height = args.height

    use_static_image_mode = args.use_static_image_mode
    min_detection_confidence = args.min_detection_confidence
    min_tracking_confidence = args.min_tracking_confidence
    sequence_confidence_threshold = args.sequence_confidence_threshold

    use_brect = True

    # Camera preparation
    cap = cv.VideoCapture(cap_device)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, cap_width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, cap_height)

    # Model load
    mp_hands = mp.solutions.hands
    mp_face_mesh = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose

    hands = mp_hands.Hands(
        static_image_mode=use_static_image_mode,
        max_num_hands=2, # detects the number of hands in the program
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=use_static_image_mode,
        max_num_faces=1,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    pose = mp_pose.Pose(
        static_image_mode=use_static_image_mode,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    keypoint_classifier = KeyPointClassifier()

    keypoint_sequence_classifier = KeyPointSequenceClassifier()
    if not keypoint_sequence_classifier.is_available:
        print("Sequence classifier is disabled because the model could not be loaded.")
        print(f"Load error: {keypoint_sequence_classifier.load_error}")
        print("Please retrain/export using the same TensorFlow version as this runtime.")

    # Read labels
    with open('Word-Label/keypoint_classifier_label.csv',
              encoding='utf-8-sig') as f:
        keypoint_classifier_labels = csv.reader(f)
        keypoint_classifier_labels = [
            row[0] for row in keypoint_classifier_labels
        ]
    try:
        with open('Word-Label/keypoint_sequence_classifier_label.csv',
                  encoding='utf-8-sig') as f:
            keypoint_sequence_classifier_labels = csv.reader(f)
            keypoint_sequence_classifier_labels = [
                row[0] for row in keypoint_sequence_classifier_labels
            ]
    except FileNotFoundError:
        keypoint_sequence_classifier_labels = ["Unknown"]

    # FPS Measurement
    cvFpsCalc = CvFpsCalc(buffer_len=10)

    # Coordinate history
    history_length = 16
    point_history = deque(maxlen=history_length)


    # Sequence gesture history
    sequence_gesture_history = deque(maxlen=history_length)

    # For timed gesture detection mode
    gestures_4 = []
    start_time_4 = 0

    # Keypoint sequence for LSTM
    sequence_length = 25
    keypoint_sequence = deque(maxlen=sequence_length)

    mode = 0
    previous_mode = 0
    sequence_started = False
    last_pre_processed = []

    current_sequence_gesture = ""

    # Number input accumulation
    number_input = ""
    number = -1
    input_state = 0  # 0: idle, 1: inputting number, 2: number confirmed
    continuous_logging = False
    space_pressed = False
    auto_mode = False

    while True:
        fps = cvFpsCalc.get()

        # Initialize sequence gesture variables
        sequence_gesture_id = 0
        sequence_gesture_confidence = 0.0

        # Process Key (ESC: end)
        key = cv.waitKey(10)
        if key == 27:  # ESC
            break
        if key != -1:  # Any key pressed
            print(f"Key pressed: {key} (char: {chr(key) if 32 <= key <= 126 else 'non-printable'})")

        # Handle space key for continuous logging while pressed
        if input_state == 2:
            if key == 32:  # Space
                if not space_pressed:
                    space_pressed = True
                    continuous_logging = True
                    print("Continuous logging started while space is pressed.")
            elif key != 32 and space_pressed and not auto_mode:
                space_pressed = False
                continuous_logging = False
                print("Continuous logging stopped.")

        # Handle key input based on state
        log_this_frame = False
        if key == ord('k'):
            mode = 1
            input_state = 1
            number_input = ""
            number = -1
            continuous_logging = False
            space_pressed = False
            auto_mode = False
            print("Mode changed to 1 (Logging Keypoints). Enter class number:")
            print("Available labels:")
            for i, label in enumerate(keypoint_classifier_labels, 1):
                print(f"{i}: {label}")
        elif key == ord('s'):
            mode = 3
            input_state = 1
            number_input = ""
            number = -1
            continuous_logging = False
            space_pressed = False
            auto_mode = False
            print("Mode changed to 3 (Logging Sequence). Enter class number:")
            print("Available labels:")
            for i, label in enumerate(keypoint_sequence_classifier_labels, 1):
                print(f"{i}: {label}")
        elif key == ord('n'):
            mode = 0
            input_state = 0
            number = -1
            continuous_logging = False
            space_pressed = False
            auto_mode = False
            print("Mode changed to 0 (Normal)")
        elif key == ord('o'):
            mode = 4
            input_state = 0
            number = -1
            continuous_logging = False
            space_pressed = False
            auto_mode = False
            print("Mode changed to 4 (Timed Gesture Detection)")
        elif input_state == 1:  # Inputting number
            if 48 <= key <= 57:  # 0-9
                number_input += chr(key)
                print(f"Number input: {number_input}")
            elif key == 13:  # Enter
                if number_input:
                    number = int(number_input)
                    input_state = 2
                    print(f"Number confirmed: {number}. Press Space to start continuous logging.")
            elif key == 8:  # Backspace
                number_input = number_input[:-1]
                print(f"Number input: {number_input}")
        elif input_state == 2:  # Number confirmed, ready to log
            if key == ord('c'):
                continuous_logging = True
                auto_mode = True
                print("Auto continuous logging started.")

        if mode != previous_mode:
            if mode == 4:
                keypoint_sequence.clear()
                sequence_started = False
        previous_mode = mode

        # Camera capture
        ret, image = cap.read()
        if not ret:
            break
        image = cv.flip(image, 1)  # Mirror display
        debug_image = copy.deepcopy(image)

        # Detection implementation
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        image.flags.writeable = False
        hands_results = hands.process(image)
        face_results = face_mesh.process(image)
        pose_results = pose.process(image)
        image.flags.writeable = True

        if hands_results.multi_hand_landmarks is not None:
            if mode == 4 and not sequence_started:
                sequence_started = True
            if mode == 4 and start_time_4 == 0:
                gestures_4 = []
                start_time_4 = time.time()

            # Get face and pose landmarks for reference
            face_landmarks = face_results.multi_face_landmarks[0] if face_results.multi_face_landmarks else None
            pose_landmarks = pose_results.pose_landmarks if pose_results else None

            for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks,
                                                  hands_results.multi_handedness):
                # Bounding box calculation
                brect = calc_bounding_rect(debug_image, hand_landmarks)
                # Landmark calculation
                landmark_list = calc_landmark_list(debug_image, hand_landmarks)

                # Conversion to relative coordinates / normalized coordinates
                pre_processed_landmark_list = pre_process_landmark(
                    landmark_list, face_landmarks, pose_landmarks, debug_image, use_legacy_mode=False)
                last_pre_processed = pre_processed_landmark_list
                # Hand sign classification
                classifier_result = keypoint_classifier(pre_processed_landmark_list)
                
                if isinstance(classifier_result, list):
                    # Multi-task model
                    hand_sign_id, hand_sign_confidence = classifier_result[0]  # Main gesture
                    region_id, region_confidence = classifier_result[1]  # Hand region
                    direction_id, direction_confidence = classifier_result[2]  # Pointing direction
                    grammar_id, grammar_confidence = classifier_result[3]  # Grammar category
                else:
                    # Single-task model (legacy)
                    hand_sign_id, hand_sign_confidence = classifier_result
                    region_id = direction_id = grammar_id = 0
                    region_confidence = direction_confidence = grammar_confidence = 0.0
                if hand_sign_id == 2:  # Point gesture
                    point_history.append(landmark_list[8])
                else:
                    point_history.append([0, 0])

                # Add to keypoint sequence
                if (mode == 4 and sequence_started) or (mode != 4 and True):  # Always append for non-4 modes when hand detected
                    keypoint_sequence.append(pre_processed_landmark_list)

                # Logging data when continuous logging is enabled
                if continuous_logging and input_state == 2 and number >= 0:
                    logging_csv(number, mode, pre_processed_landmark_list, keypoint_sequence, sequence_length)

                # Drawing part
                debug_image = draw_bounding_rect(use_brect, debug_image, brect)
                debug_image = draw_landmarks(debug_image, landmark_list)
                debug_image = draw_face_landmarks(debug_image, face_landmarks)
                debug_image = draw_pose_landmarks(debug_image, pose_landmarks)


                if hand_sign_confidence > 0.8:
                    hand_sign_label = f"{keypoint_classifier_labels[hand_sign_id - 1] if hand_sign_id - 1 < len(keypoint_classifier_labels) else str(hand_sign_id)} ({hand_sign_confidence*100:.0f}%)"
                else:
                    hand_sign_label = "不確定"

                # Add auxiliary information
                auxiliary_info = ""
                if region_confidence > 0.6:
                    region_labels = ["臉側", "胸前", "側邊", "前方延伸"]
                    auxiliary_info += f"區域:{region_labels[region_id] if region_id < len(region_labels) else str(region_id)} "
                
                if direction_confidence > 0.6:
                    direction_labels = ["北", "東北", "東", "東南", "南", "西南", "西", "西北"]
                    auxiliary_info += f"方向:{direction_labels[direction_id] if direction_id < len(direction_labels) else str(direction_id)}"

                if mode == 4 and start_time_4 > 0 and hand_sign_confidence > 0.8:
                    gestures_4.append(hand_sign_id)

                if keypoint_sequence_classifier.is_available and sequence_gesture_confidence > sequence_confidence_threshold:
                    sequence_gesture_label = f"{keypoint_sequence_classifier_labels[sequence_gesture_id - 1] if sequence_gesture_id - 1 < len(keypoint_sequence_classifier_labels) else str(sequence_gesture_id)} ({sequence_gesture_confidence*100:.0f}%)"
                else:
                    sequence_gesture_label = ""

                # Print detected results to terminal
                # print(f"Detected: Hand Sign: {hand_sign_label}, {auxiliary_info.strip()}, Sequence: {sequence_gesture_label}")

                debug_image = draw_info_text(
                    debug_image,
                    brect,
                    handedness,
                    hand_sign_label,
                    auxiliary_info,
                    sequence_gesture_label,
                )
        else:
            point_history.append([0, 0])
            if mode == 4 and sequence_started:
                keypoint_sequence.append(last_pre_processed)

        # Sequence gesture classification
        if keypoint_sequence_classifier.is_available and (len(keypoint_sequence) >= sequence_length or (mode == 4 and start_time_4 > 0 and time.time() - start_time_4 >= 1 and len(keypoint_sequence) >= 15)):
            seq = list(keypoint_sequence)
            if len(seq) < sequence_length:
                last = seq[-1]
                seq.extend([last] * (sequence_length - len(seq)))
            sequence_gesture_id, sequence_gesture_confidence = keypoint_sequence_classifier(seq)

        # Calculates the gesture IDs in the latest detection
        sequence_gesture_history.append(sequence_gesture_id)
        most_common_sg_id = Counter(
            sequence_gesture_history).most_common()

        if keypoint_sequence_classifier.is_available and sequence_gesture_confidence > sequence_confidence_threshold:
            sequence_gesture_label = f"{keypoint_sequence_classifier_labels[sequence_gesture_id - 1] if sequence_gesture_id - 1 < len(keypoint_sequence_classifier_labels) else str(sequence_gesture_id)} ({sequence_gesture_confidence*100:.0f}%)"
        else:
            sequence_gesture_label = "不確定" if keypoint_sequence_classifier.is_available else "模型未載入"

        current_sequence_gesture = sequence_gesture_label

        debug_image = draw_point_history(debug_image, point_history)

        # Always display sequence gesture if available
        if current_sequence_gesture != "":
            debug_image = draw_chinese_text(debug_image, "Sequence Gesture:" + current_sequence_gesture, (10, 70), font_size=35, color=(0, 0, 0), bold=True)
            debug_image = draw_chinese_text(debug_image, "Sequence Gesture:" + current_sequence_gesture, (10, 70), font_size=35, color=(255, 255, 0), bold=True)

        debug_image = draw_info(debug_image, fps, mode, number)

        if mode == 4 and start_time_4 > 0 and time.time() - start_time_4 >= 2.5:
            if gestures_4:
                most_common = Counter(gestures_4).most_common(1)[0][0]
                label = keypoint_classifier_labels[most_common - 1] if most_common - 1 < len(keypoint_classifier_labels) else str(most_common)
                sequence_part = f" + {current_sequence_gesture}" if current_sequence_gesture else ""
                print(f"Detected gesture after 2.5 seconds: {label}{sequence_part}")
            mode = 0
            start_time_4 = 0
            gestures_4 = []

        # Screen reflection
        cv.imshow('Hand Gesture Recognition', debug_image)

    cap.release()
    cv.destroyAllWindows()


def select_mode(key, mode, number_input):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number_input += chr(key)
        print(f"Number input: {number_input}")
    elif key == 13 or key == 32:  # Enter or Space to confirm number
        if number_input:
            number = int(number_input)
            print(f"Number confirmed: {number}")
            number_input = ""
        else:
            number = -1
    elif key == 8:  # Backspace to delete last digit
        number_input = number_input[:-1]
        print(f"Number input: {number_input}")
    if key == 110:  # n
        mode = 0
        number_input = ""  # Clear input on mode change
    if key == 107:  # k
        mode = 1
        number_input = ""  # Clear input on mode change
    if key == 115:  # s
        mode = 3
        print(f"Mode changed to {mode} (Logging Sequence)")
        number_input = ""  # Clear input on mode change
    if key == 111:  # o
        mode = 4
        print(f"Mode changed to {mode} (Timed Gesture Detection)")
        number_input = ""  # Clear input on mode change
    return number, mode, number_input


def calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_array = np.empty((0, 2), int)

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point = [np.array((landmark_x, landmark_y))]

        landmark_array = np.append(landmark_array, landmark_point, axis=0)

    x, y, w, h = cv.boundingRect(landmark_array)

    return [x, y, x + w, y + h]


def calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    # Keypoint
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        # landmark_z = landmark.z

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point


def extract_face_features(face_landmarks, image):
    """Extract face features: head pose, eye gaze, mouth openness"""
    try:
        if face_landmarks is None or image is None:
            return [0.0] * 8  # Default values

        image_width, image_height = image.shape[1], image.shape[0]
        features = []

        # Head pose estimation using facial landmarks
        # Nose tip (1), left eye (33), right eye (263), left ear (234), right ear (454)
        nose = face_landmarks.landmark[1]
        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        left_ear = face_landmarks.landmark[234]
        right_ear = face_landmarks.landmark[454]

        # Simple head pose estimation
        eye_center_x = (left_eye.x + right_eye.x) / 2
        eye_center_y = (left_eye.y + right_eye.y) / 2

        # Yaw: horizontal rotation (difference between ear positions)
        yaw = right_ear.x - left_ear.x
        # Pitch: vertical rotation (nose position relative to eyes)
        pitch = nose.y - eye_center_y
        # Roll: tilt (eye level difference)
        roll = right_eye.y - left_eye.y

        features.extend([yaw, pitch, roll])

        # Eye gaze (eye openness and direction)
        # Left eye landmarks: 160 (top), 144 (bottom), 133 (left), 33 (right)
        left_eye_top = face_landmarks.landmark[160].y
        left_eye_bottom = face_landmarks.landmark[144].y
        left_eye_left = face_landmarks.landmark[133].x
        left_eye_right = face_landmarks.landmark[33].x
        left_eye_openness = left_eye_top - left_eye_bottom
        left_eye_width = left_eye_right - left_eye_left

        # Right eye landmarks: 385 (top), 380 (bottom), 263 (left), 362 (right)
        right_eye_top = face_landmarks.landmark[385].y
        right_eye_bottom = face_landmarks.landmark[380].y
        right_eye_left = face_landmarks.landmark[263].x
        right_eye_right = face_landmarks.landmark[362].x
        right_eye_openness = right_eye_top - right_eye_bottom
        right_eye_width = right_eye_right - right_eye_left

        features.extend([left_eye_openness, right_eye_openness])

        # Mouth openness
        # Upper lip (13), lower lip (14)
        upper_lip = face_landmarks.landmark[13].y
        lower_lip = face_landmarks.landmark[14].y
        mouth_openness = lower_lip - upper_lip

        features.append(mouth_openness)

        # Eye gaze direction (simplified)
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
            return [0.0] * 8  # Default values

        image_width, image_height = image.shape[1], image.shape[0]
        features = []

        # Key pose landmarks
        left_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        left_hip = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP]
        right_hip = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_HIP]
        nose = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE]

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
            return [0.0] * 22  # Default values

        image_width, image_height = image.shape[1], image.shape[0]
        features = []

        # Key hand landmarks (wrist, index finger tip, middle finger tip)
        wrist = hand_landmarks[0]  # [x, y]
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]

        # Convert to normalized coordinates
        wrist_x = wrist[0] / image_width
        wrist_y = wrist[1] / image_height
        index_x = index_tip[0] / image_width
        index_y = index_tip[1] / image_height
        middle_x = middle_tip[0] / image_width
        middle_y = middle_tip[1] / image_height

        # If pose features available, compute relative to shoulders and torso
        if len(pose_features) >= 8:
            shoulder_center_x, shoulder_center_y = pose_features[0], pose_features[1]

            # Hand relative to shoulder center
            hand_to_shoulder_x = wrist_x - shoulder_center_x
            hand_to_shoulder_y = wrist_y - shoulder_center_y
            index_to_shoulder_x = index_x - shoulder_center_x
            index_to_shoulder_y = index_y - shoulder_center_y

            features.extend([hand_to_shoulder_x, hand_to_shoulder_y, index_to_shoulder_x, index_to_shoulder_y])

            # Hand position relative to torso center
            torso_center_x = shoulder_center_x  # Approximation
            torso_center_y = (shoulder_center_y + pose_features[6]) / 2  # Between shoulders and hips
            hand_rel_torso_x = wrist_x - torso_center_x
            hand_rel_torso_y = wrist_y - torso_center_y

            features.extend([hand_rel_torso_x, hand_rel_torso_y])
        else:
            features.extend([0.0] * 6)

        # If face features available, compute relative to head
        if len(face_features) >= 10:
            # Approximate head center from nose position (assuming normalized)
            # This is a simplification - in practice you'd use the face landmarks
            head_center_x = 0.5  # Approximate center
            head_center_y = 0.3  # Approximate center

            hand_to_head_x = wrist_x - head_center_x
            hand_to_head_y = wrist_y - head_center_y
            index_to_head_x = index_x - head_center_x
            index_to_head_y = index_y - head_center_y

            features.extend([hand_to_head_x, hand_to_head_y, index_to_head_x, index_to_head_y])
        else:
            features.extend([0.0] * 4)

        # Hand extension ratio (distance from wrist to fingertips)
        index_extension = math.sqrt((index_x - wrist_x)**2 + (index_y - wrist_y)**2)
        middle_extension = math.sqrt((middle_x - wrist_x)**2 + (middle_y - wrist_y)**2)

        features.extend([index_extension, middle_extension])

        # Elbow and wrist offsets (simplified - would need elbow landmarks)
        # For now, use placeholder
        features.extend([0.0, 0.0])  # elbow_offset_x, elbow_offset_y

        # Pad to 22 features
        features.extend([0.0] * (22 - len(features)))

        return features
    except (AttributeError, IndexError, TypeError, ZeroDivisionError):
        return [0.0] * 22


def pre_process_landmark(landmark_list, face_landmarks=None, pose_landmarks=None, image=None, use_legacy_mode=False):
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Extract face and pose features
    face_features = extract_face_features(face_landmarks, image)
    pose_features = extract_pose_features(pose_landmarks, image)

    # Compute relative positions
    relative_features = compute_relative_positions(temp_landmark_list, face_features, pose_features, image)

    # Convert hand landmarks to relative coordinates
    base_x, base_y = 0, 0

    if use_legacy_mode:
        # Legacy mode: use wrist as reference (original behavior)
        base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]
    else:
        # Enhanced mode: use face/body as reference for better accuracy
        # Use face nose as reference if available (landmark 1 in face mesh)
        if face_landmarks and image is not None:
            image_width, image_height = image.shape[1], image.shape[0]
            nose_x = int(face_landmarks.landmark[1].x * image_width)
            nose_y = int(face_landmarks.landmark[1].y * image_height)
            base_x, base_y = nose_x, nose_y
        # Use pose shoulder center as reference if face not available
        elif pose_landmarks and image is not None:
            image_width, image_height = image.shape[1], image.shape[0]
            left_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
            shoulder_x = int(((left_shoulder.x + right_shoulder.x) / 2) * image_width)
            shoulder_y = int(((left_shoulder.y + right_shoulder.y) / 2) * image_height)
            base_x, base_y = shoulder_x, shoulder_y
        else:
            # Fallback to wrist (original behavior)
            base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]

    for index, landmark_point in enumerate(temp_landmark_list):
        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Save 2D landmarks for relative position computation
    hand_landmarks_2d = temp_landmark_list.copy()

    # Convert to a one-dimensional list
    temp_landmark_list = list(
        itertools.chain.from_iterable(temp_landmark_list))

    # Normalization
    max_value = max(list(map(abs, temp_landmark_list)))

    def normalize_(n):
        return n / max_value if max_value != 0 else n

    temp_landmark_list = list(map(normalize_, temp_landmark_list))

    if use_legacy_mode:
        return temp_landmark_list  # Return only hand features (42)
    else:
        # Enhanced mode: concatenate all features
        # Extract face and pose features
        face_features = extract_face_features(face_landmarks, image)
        pose_features = extract_pose_features(pose_landmarks, image)

        # Compute relative positions
        relative_features = compute_relative_positions(hand_landmarks_2d, face_features, pose_features, image)

        # Concatenate all features: hand landmarks + face features + pose features + relative features
        all_features = temp_landmark_list + face_features + pose_features + relative_features

        # Normalization for all features
        max_value_all = max(list(map(abs, all_features)))

        def normalize_all(n):
            return n / max_value_all if max_value_all != 0 else n

        all_features = list(map(normalize_all, all_features))

        return all_features


def logging_csv(number, mode, landmark_list, keypoint_sequence, sequence_length):
    # Ensure the 'Words-Dataset' directory exists
    words_dir = 'Words-Dataset'
    if not os.path.exists(words_dir):
        os.makedirs(words_dir)
    
    if mode == 0:
        pass
    if mode == 1 and (number >= 0):
        # Create a separate CSV file for each class in 'Words-Dataset' folder
        csv_path = os.path.join(words_dir, f'{number:03d}.csv')
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *landmark_list])
    if mode == 3 and (number >= 0) and len(keypoint_sequence) >= sequence_length:
        # Create a separate CSV file for each sequence class in 'Words-Dataset' folder
        csv_path = os.path.join(words_dir, f'{number:03d}_sequence.csv')
        flattened_sequence = list(itertools.chain.from_iterable(keypoint_sequence))
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *flattened_sequence])
    return


def draw_landmarks(image, landmark_point):
    if len(landmark_point) > 0:
        # Thumb
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (255, 255, 255), 2)

        # Index finger
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (255, 255, 255), 2)

        # Middle finger
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (255, 255, 255), 2)

        # Ring finger
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (255, 255, 255), 2)

        # Little finger
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (255, 255, 255), 2)

        # Palm
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (255, 255, 255), 2)

    # Key Points
    for index, landmark in enumerate(landmark_point):
        if index == 0:  # 手首1
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 1:  # 手首2
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 2:  # 親指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 3:  # 親指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 4:  # 親指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 5:  # 人差指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 6:  # 人差指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 7:  # 人差指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 8:  # 人差指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 9:  # 中指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 10:  # 中指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 11:  # 中指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 12:  # 中指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 13:  # 薬指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 14:  # 薬指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 15:  # 薬指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 16:  # 薬指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 17:  # 小指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 18:  # 小指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 19:  # 小指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 20:  # 小指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

    return image


def draw_face_landmarks(image, face_landmarks):
    if face_landmarks:
        image_width, image_height = image.shape[1], image.shape[0]
        # Draw all face landmarks
        for idx, landmark in enumerate(face_landmarks.landmark):
            x = int(landmark.x * image_width)
            y = int(landmark.y * image_height)
            # Draw key landmarks with different colors
            if idx in [1, 33, 263, 234, 454]:  # Nose, eyes, ears
                cv.circle(image, (x, y), 3, (0, 255, 0), -1)  # Green for key points
            else:
                cv.circle(image, (x, y), 1, (255, 255, 0), -1)  # Yellow for other points
    return image


def draw_pose_landmarks(image, pose_landmarks):
    if pose_landmarks:
        image_width, image_height = image.shape[1], image.shape[0]
        
        # Define pose connections (simplified skeleton)
        pose_connections = [
            # Torso
            (mp.solutions.pose.PoseLandmark.LEFT_SHOULDER, mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER),
            (mp.solutions.pose.PoseLandmark.LEFT_SHOULDER, mp.solutions.pose.PoseLandmark.LEFT_HIP),
            (mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER, mp.solutions.pose.PoseLandmark.RIGHT_HIP),
            (mp.solutions.pose.PoseLandmark.LEFT_HIP, mp.solutions.pose.PoseLandmark.RIGHT_HIP),
            # Left arm
            (mp.solutions.pose.PoseLandmark.LEFT_SHOULDER, mp.solutions.pose.PoseLandmark.LEFT_ELBOW),
            (mp.solutions.pose.PoseLandmark.LEFT_ELBOW, mp.solutions.pose.PoseLandmark.LEFT_WRIST),
            # Right arm
            (mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER, mp.solutions.pose.PoseLandmark.RIGHT_ELBOW),
            (mp.solutions.pose.PoseLandmark.RIGHT_ELBOW, mp.solutions.pose.PoseLandmark.RIGHT_WRIST),
            # Left leg
            (mp.solutions.pose.PoseLandmark.LEFT_HIP, mp.solutions.pose.PoseLandmark.LEFT_KNEE),
            (mp.solutions.pose.PoseLandmark.LEFT_KNEE, mp.solutions.pose.PoseLandmark.LEFT_ANKLE),
            # Right leg
            (mp.solutions.pose.PoseLandmark.RIGHT_HIP, mp.solutions.pose.PoseLandmark.RIGHT_KNEE),
            (mp.solutions.pose.PoseLandmark.RIGHT_KNEE, mp.solutions.pose.PoseLandmark.RIGHT_ANKLE),
            # Head
            (mp.solutions.pose.PoseLandmark.LEFT_SHOULDER, mp.solutions.pose.PoseLandmark.NOSE),
            (mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER, mp.solutions.pose.PoseLandmark.NOSE),
        ]
        
        # Draw connections
        for connection in pose_connections:
            start_idx, end_idx = connection
            start_landmark = pose_landmarks.landmark[start_idx]
            end_landmark = pose_landmarks.landmark[end_idx]
            
            start_x = int(start_landmark.x * image_width)
            start_y = int(start_landmark.y * image_height)
            end_x = int(end_landmark.x * image_width)
            end_y = int(end_landmark.y * image_height)
            
            cv.line(image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)  # Blue lines
        
        # Draw all landmarks
        for idx, landmark in enumerate(pose_landmarks.landmark):
            x = int(landmark.x * image_width)
            y = int(landmark.y * image_height)
            
            # Different colors for different body parts
            if idx in [mp.solutions.pose.PoseLandmark.NOSE, mp.solutions.pose.PoseLandmark.LEFT_EYE, mp.solutions.pose.PoseLandmark.RIGHT_EYE]:
                color = (0, 255, 255)  # Cyan for head
            elif idx in [mp.solutions.pose.PoseLandmark.LEFT_SHOULDER, mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
                        mp.solutions.pose.PoseLandmark.LEFT_ELBOW, mp.solutions.pose.PoseLandmark.RIGHT_ELBOW,
                        mp.solutions.pose.PoseLandmark.LEFT_WRIST, mp.solutions.pose.PoseLandmark.RIGHT_WRIST]:
                color = (0, 0, 255)  # Red for arms
            elif idx in [mp.solutions.pose.PoseLandmark.LEFT_HIP, mp.solutions.pose.PoseLandmark.RIGHT_HIP,
                        mp.solutions.pose.PoseLandmark.LEFT_KNEE, mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
                        mp.solutions.pose.PoseLandmark.LEFT_ANKLE, mp.solutions.pose.PoseLandmark.RIGHT_ANKLE]:
                color = (255, 0, 255)  # Magenta for legs
            else:
                color = (255, 255, 0)  # Yellow for others
            
            cv.circle(image, (x, y), 4, color, -1)
            cv.circle(image, (x, y), 4, (255, 255, 255), 1)  # White border
    return image


def draw_bounding_rect(use_brect, image, brect):
    if use_brect:
        # Outer rectangle
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                     (0, 0, 0), 1)

    return image


def draw_info_text(image, brect, handedness, hand_sign_text,
                   finger_gesture_text, sequence_gesture_text):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22),
                 (0, 0, 0), -1)

    info_text = handedness.classification[0].label[0:]
    if hand_sign_text != "":
        info_text = info_text + ':' + hand_sign_text

    image = draw_chinese_text(image, info_text, (brect[0] + 5, brect[1] - 20), font_size=25, color=(255, 255, 255))

    if finger_gesture_text != "":
        image = draw_chinese_text(image, finger_gesture_text, (10, 40), font_size=20, color=(0, 0, 0))
        image = draw_chinese_text(image, finger_gesture_text, (10, 40), font_size=20, color=(255, 255, 255))

    if sequence_gesture_text != "":
        image = draw_chinese_text(image, "Sequence Gesture:" + sequence_gesture_text, (10, 70), font_size=35, color=(0, 0, 0), bold=True)
        image = draw_chinese_text(image, "Sequence Gesture:" + sequence_gesture_text, (10, 70), font_size=35, color=(255, 255, 0), bold=True)

    return image


def draw_point_history(image, point_history):
    for index, point in enumerate(point_history):
        if point[0] != 0 and point[1] != 0:
            cv.circle(image, (point[0], point[1]), 1 + int(index / 2),
                      (152, 251, 152), 2)

    return image


def draw_info(image, fps, mode, number):

    fps_text = f"FPS:{fps}"
    image = draw_chinese_text(image, fps_text, (10, 10), font_size=20, color=(0, 0, 0))
    image = draw_chinese_text(image, fps_text, (10, 10), font_size=20, color=(255, 255, 255))

    mode_string = ['記錄關鍵點', '', '記錄序列', '定時偵測']
    if 1 <= mode <= 4:
        mode_text = f"模式:{mode_string[mode - 1]}"
        image = draw_chinese_text(image, mode_text, (10, 50), font_size=16, color=(255, 255, 255))
        if mode == 4:
            detect_text = "正在偵測中(2s)"
            image = draw_chinese_text(image, detect_text, (10, 70), font_size=16, color=(255, 255, 255))
        elif number >= 0:
            num_text = f"編號:{number}"
            image = draw_chinese_text(image, num_text, (10, 70), font_size=16, color=(255, 255, 255))
    return image


if __name__ == '__main__':
    main()
