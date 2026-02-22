#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
import os

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


class KeyPointSequenceClassifier(object):
    def __init__(
        self,
        model_path='model/keypoint_classifier/keypoint_sequence_classifier.tflite',
        num_threads=1,
        use_openvino=None,
        openvino_device=None,
    ):
        model_path = _resolve_model_path(model_path)

        if not os.path.exists(model_path):
            self.interpreter = None
            self.use_openvino = False
            print(f"Warning: Model file {model_path} not found. Sequence classification will be disabled.")
        else:
            if use_openvino is None:
                use_openvino = os.getenv("USE_OPENVINO", "0") == "1"
            self.use_openvino = bool(use_openvino and _OPENVINO_AVAILABLE)
            self.openvino_device = openvino_device or os.getenv("OPENVINO_DEVICE", "GPU")
            self.ov_compiled = None
            self.ov_input = None
            self.ov_outputs = None

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
                except Exception:
                    self.use_openvino = False

            if not self.use_openvino:
                self.interpreter = tf.lite.Interpreter(model_path=model_path,
                                                       num_threads=num_threads,
                                                       experimental_delegates=[])

                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()

    def __call__(
        self,
        keypoint_sequence,
    ):
        if self.interpreter is None:
            return 0, 0.0  # Default to class 0 with 0 confidence if no model
        input_details_tensor_index = self.input_details[0]['index']
        # Take the last 25 frames with 80 features
        sequence_to_use = keypoint_sequence[-25:]
        if self.use_openvino and self.ov_compiled is not None:
            inputs = np.array([sequence_to_use], dtype=np.float32)
            results_map = self.ov_compiled({self.ov_input: inputs})
            result = results_map[self.ov_outputs[0]]
            result_squeezed = np.squeeze(result)
            result_index = np.argmax(result_squeezed)
            confidence = result_squeezed[result_index]
            return result_index + 1, confidence

        self.interpreter.set_tensor(
            input_details_tensor_index,
            np.array([sequence_to_use], dtype=np.float32))
        self.interpreter.invoke()

        output_details_tensor_index = self.output_details[0]['index']

        result = self.interpreter.get_tensor(output_details_tensor_index)

        result_squeezed = np.squeeze(result)
        result_index = np.argmax(result_squeezed)
        confidence = result_squeezed[result_index]

        return result_index + 1, confidence