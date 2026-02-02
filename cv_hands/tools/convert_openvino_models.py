"""
Convert TFLite models to OpenVINO IR (XML+BIN).
Requires: openvino-dev (for Model Optimizer).
"""
import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CV_HANDS_DIR = SCRIPT_DIR.parent
MODEL_DIR = CV_HANDS_DIR / "model" / "keypoint_classifier"

MODEL_SPECS = [
    {
        "name": "keypoint_classifier",
        "tflite": MODEL_DIR / "keypoint_classifier.tflite",
        "keras": MODEL_DIR / "keypoint_classifier.keras",
    },
    {
        "name": "keypoint_sequence_classifier",
        "tflite": MODEL_DIR / "keypoint_sequence_classifier.tflite",
        "keras": MODEL_DIR / "keypoint_sequence_classifier.keras",
    },
]


def run_mo(input_model: Path, output_dir: Path, model_name: str):
    cmd = [
        sys.executable,
        "-m",
        "openvino.tools.mo",
        "--input_model",
        str(input_model),
        "--output_dir",
        str(output_dir),
        "--model_name",
        model_name,
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def convert_from_keras(keras_path: Path, output_dir: Path, model_name: str):
    import tensorflow as tf

    saved_model_dir = output_dir / f"{model_name}_saved_model"
    if saved_model_dir.exists():
        # Clean old export to avoid stale files
        for root, dirs, files in os.walk(saved_model_dir, topdown=False):
            for name in files:
                os.remove(Path(root) / name)
            for name in dirs:
                os.rmdir(Path(root) / name)
    model = tf.keras.models.load_model(keras_path, compile=False)
    model.save(saved_model_dir)
    run_mo(saved_model_dir, output_dir, model_name)


def main():
    output_dir = MODEL_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for spec in MODEL_SPECS:
        model_name = spec["name"]
        tflite_path = spec["tflite"]
        keras_path = spec["keras"]

        if tflite_path.exists():
            try:
                run_mo(tflite_path, output_dir, model_name)
                print(f"Converted: {tflite_path.name} -> {model_name}.xml/.bin")
                continue
            except subprocess.CalledProcessError as exc:
                print(f"TFLite conversion failed for {tflite_path.name}: {exc}")
        else:
            print(f"Skip: {tflite_path} not found")

        if keras_path.exists():
            try:
                convert_from_keras(keras_path, output_dir, model_name)
                print(f"Converted: {keras_path.name} -> {model_name}.xml/.bin")
                continue
            except Exception as exc:
                print(f"Keras conversion failed for {keras_path.name}: {exc}")
        else:
            print(f"Skip: {keras_path} not found")


if __name__ == "__main__":
    main()
