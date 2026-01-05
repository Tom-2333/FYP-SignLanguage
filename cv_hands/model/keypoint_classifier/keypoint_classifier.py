#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os

# TensorFlow Lite import
try:
    import tensorflow as tf
    # For TF 2.16+
    try:
        from tensorflow import lite as tflite
    except:
        import tensorflow.lite as tflite
except ImportError:
    # Fallback to tflite_runtime if available
    import tflite_runtime.interpreter as tflite


class KeyPointClassifier(object):
    def __init__(
        self,
        model_path='model/keypoint_classifier/keypoint_classifier.tflite',
        num_threads=2,  # Increased threads for better performance
    ):
        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Use TFLite Interpreter - works with TF 2.x
        try:
            self.interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=num_threads)
        except AttributeError:
            self.interpreter = tflite.Interpreter(model_path=model_path, num_threads=num_threads)

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(
        self,
        landmark_list,
    ):
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
