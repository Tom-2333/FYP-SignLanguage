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


class KeyPointSequenceClassifier(object):
    def __init__(
        self,
        model_path='model/keypoint_classifier/keypoint_sequence_classifier.tflite',
        num_threads=2,  # Increased threads for better performance
    ):
        self.use_keras = False
        self.interpreter = None
        self.keras_model = None
        
        # Prioritize TFLite for better performance (faster than Keras)
        if os.path.exists(model_path):
            try:
                # Use TFLite Interpreter - much faster than Keras
                try:
                    self.interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=num_threads)
                except AttributeError:
                    self.interpreter = tflite.Interpreter(model_path=model_path, num_threads=num_threads)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                print(f"Loaded TFLite model from {model_path}")
            except Exception as e:
                print(f"Warning: Failed to load TFLite model: {e}")
                self.interpreter = None
        else:
            print(f"Warning: Model file {model_path} not found. Sequence classification will be disabled.")

    def __call__(
        self,
        keypoint_sequence,
    ):
        if self.interpreter is None:
            return 0, 0.0  # Default to class 0 with 0 confidence if no model
            
        # Take the last 25 frames with features
        sequence_to_use = keypoint_sequence[-25:]
        input_data = np.array([sequence_to_use], dtype=np.float32)
        
        # Use TFLite model (faster than Keras)
        input_details_tensor_index = self.input_details[0]['index']
        self.interpreter.set_tensor(input_details_tensor_index, input_data)
        self.interpreter.invoke()
        output_details_tensor_index = self.output_details[0]['index']
        result = self.interpreter.get_tensor(output_details_tensor_index)
        result_squeezed = np.squeeze(result)
        
        result_index = np.argmax(result_squeezed)
        confidence = result_squeezed[result_index]

        return result_index + 1, confidence