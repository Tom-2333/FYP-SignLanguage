#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
import os
import platform

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CV_HANDS_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))


def _resolve_model_path(model_path):
    if os.path.isabs(model_path):
        return model_path
    candidate = os.path.join(_CV_HANDS_DIR, model_path)
    return candidate if os.path.exists(candidate) else model_path

try:
    from openvino.runtime import Core
    _OPENVINO_AVAILABLE = True
except Exception:
    _OPENVINO_AVAILABLE = False


def _resolve_openvino_model_path(model_path):
    model_path = _resolve_model_path(model_path)
    if model_path.lower().endswith(".xml"):
        return model_path
    base, _ = os.path.splitext(model_path)
    xml_path = base + ".xml"
    return xml_path if os.path.exists(xml_path) else model_path


def _should_use_openvino(model_path, explicit_use_openvino):
    if explicit_use_openvino is not None:
        return bool(explicit_use_openvino)

    backend = os.getenv("INFERENCE_BACKEND", "auto").strip().lower()
    if backend in ("openvino", "ov"):
        return True
    if backend in ("tflite", "tf", "tensorflow"):
        return False

    legacy_flag = os.getenv("USE_OPENVINO")
    if legacy_flag is not None:
        return legacy_flag == "1"

    # Auto mode: prefer OpenVINO on Windows when IR model exists.
    is_windows = platform.system().lower().startswith("win")
    ov_model_path = _resolve_openvino_model_path(model_path)
    return bool(is_windows and ov_model_path.lower().endswith(".xml") and os.path.exists(ov_model_path))


class KeyPointClassifier(object):
    def __init__(
        self,
        model_path='model/keypoint_classifier/keypoint_classifier.tflite',
        num_threads=1,
        use_openvino=None,
        openvino_device=None,
    ):
        self.interpreter = None
        self.use_openvino = bool(_should_use_openvino(model_path, use_openvino) and _OPENVINO_AVAILABLE)
        self.openvino_device = openvino_device or os.getenv("OPENVINO_DEVICE", "GPU")
        self.ov_compiled = None
        self.ov_input = None
        self.ov_outputs = None
        self.backend = "tflite"

        model_path = _resolve_model_path(model_path)

        if self.use_openvino:
            try:
                core = Core()
                ov_model = core.read_model(_resolve_openvino_model_path(model_path))
                try:
                    self.ov_compiled = core.compile_model(ov_model, self.openvino_device)
                except Exception:
                    self.openvino_device = "CPU"
                    self.ov_compiled = core.compile_model(ov_model, self.openvino_device)
                self.ov_input = self.ov_compiled.inputs[0]
                self.ov_outputs = list(self.ov_compiled.outputs)
                self.backend = f"openvino:{self.openvino_device}"
            except Exception:
                self.use_openvino = False

        if not self.use_openvino:
            self.interpreter = tf.lite.Interpreter(model_path=model_path,
                                                   num_threads=num_threads,
                                                   experimental_delegates=[])

            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.backend = "tflite"

    def __call__(
        self,
        landmark_list,
    ):
        if self.use_openvino and self.ov_compiled is not None:
            inputs = np.array([landmark_list], dtype=np.float32)
            results_map = self.ov_compiled({self.ov_input: inputs})
            outputs = [results_map[o] for o in self.ov_outputs]

            if len(outputs) > 1:
                results = []
                for result in outputs:
                    result_squeezed = np.squeeze(result)
                    result_index = np.argmax(result_squeezed)
                    confidence = result_squeezed[result_index]
                    results.append((result_index + 1, confidence))
                return results

            result = outputs[0]
            result_squeezed = np.squeeze(result)
            if result_squeezed.ndim == 0:
                result_index = int(result_squeezed)
                confidence = 1.0
            else:
                result_index = np.argmax(result_squeezed)
                confidence = result_squeezed[result_index]
            return result_index + 1, confidence

        input_details_tensor_index = self.input_details[0]['index']
        self.interpreter.set_tensor(
            input_details_tensor_index,
            np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()

        # Handle multiple outputs for multi-task model
        if len(self.output_details) > 1:
            results = []
            for output_detail in self.output_details:
                output_tensor_index = output_detail['index']
                result = self.interpreter.get_tensor(output_tensor_index)
                result_squeezed = np.squeeze(result)
                result_index = np.argmax(result_squeezed)
                confidence = result_squeezed[result_index]
                results.append((result_index + 1, confidence))
            return results  # Return list of (index, confidence) tuples
        else:
            # Single output (legacy behavior)
            output_details_tensor_index = self.output_details[0]['index']
            result = self.interpreter.get_tensor(output_details_tensor_index)
            result_squeezed = np.squeeze(result)
            if result_squeezed.ndim == 0:
                # Scalar output, assume it's the class index
                result_index = int(result_squeezed)
                confidence = 1.0
            else:
                result_index = np.argmax(result_squeezed)
                confidence = result_squeezed[result_index]
            return result_index + 1, confidence
