#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf
import os


class KeyPointSequenceClassifier(object):
    def __init__(
        self,
        model_path='model/keypoint_classifier/keypoint_sequence_classifier.tflite',
        num_threads=1,
    ):
        if not os.path.exists(model_path):
            self.backend = 'disabled-missing-model'
            self.interpreter = None
            print(f"Warning: Model file {model_path} not found. Sequence classification will be disabled.")
        else:
            self.backend = 'tflite-tensorflow'
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