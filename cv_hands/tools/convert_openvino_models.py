"""
Convert TFLite models to OpenVINO IR (XML+BIN).
Requires: openvino-dev (for Model Optimizer).
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CV_HANDS_DIR = SCRIPT_DIR.parent
MODEL_DIR = CV_HANDS_DIR / "model" / "keypoint_classifier"

MODEL_SPECS = [
    {
        "name": "keypoint_classifier",
        "tflite": MODEL_DIR / "keypoint_classifier.tflite",
        "keras": MODEL_DIR / "keypoint_classifier.keras",
        "saved_model": MODEL_DIR / "keypoint_classifier_savedmodel",
    },
    {
        "name": "keypoint_sequence_classifier",
        "tflite": MODEL_DIR / "keypoint_sequence_classifier.tflite",
        "keras": MODEL_DIR / "keypoint_sequence_classifier.keras",
        "saved_model": MODEL_DIR / "keypoint_sequence_classifier_savedmodel",
    },
]


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("openvino_convert")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    log_path = MODEL_DIR / "openvino_convert.log"
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Logging to %s", log_path)
    return logger


def run_mo(input_model: Path, output_dir: Path, model_name: str, logger: logging.Logger):
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
    logger.info("Running: %s", " ".join(cmd))
    subprocess.check_call(cmd)


def convert_from_keras(keras_path: Path, output_dir: Path, model_name: str, logger: logging.Logger):
    import tensorflow as tf

    saved_model_dir = output_dir / f"{model_name}_saved_model"
    if saved_model_dir.exists():
        # Clean old export to avoid stale files
        for root, dirs, files in os.walk(saved_model_dir, topdown=False):
            for name in files:
                os.remove(Path(root) / name)
            for name in dirs:
                os.rmdir(Path(root) / name)
        logger.info("Cleaned old SavedModel dir: %s", saved_model_dir)
    model = tf.keras.models.load_model(keras_path, compile=False)
    model.save(saved_model_dir)
    logger.info("Exported Keras -> SavedModel: %s", saved_model_dir)
    run_mo(saved_model_dir, output_dir, model_name, logger)


def main():
    logger = setup_logger()
    output_dir = MODEL_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for spec in MODEL_SPECS:
        model_name = spec["name"]
        tflite_path = spec["tflite"]
        keras_path = spec["keras"]

        if tflite_path.exists():
            try:
                run_mo(tflite_path, output_dir, model_name, logger)
                logger.info("Converted: %s -> %s.xml/.bin", tflite_path.name, model_name)
                continue
            except subprocess.CalledProcessError as exc:
                logger.error("TFLite conversion failed for %s: %s", tflite_path.name, exc)
        else:
            logger.warning("Skip: %s not found", tflite_path)

        saved_model_dir = spec.get("saved_model")
        if saved_model_dir and saved_model_dir.exists():
            try:
                run_mo(saved_model_dir, output_dir, model_name, logger)
                logger.info("Converted: %s -> %s.xml/.bin", saved_model_dir.name, model_name)
                continue
            except subprocess.CalledProcessError as exc:
                logger.error("SavedModel conversion failed for %s: %s", saved_model_dir.name, exc)

        if keras_path.exists():
            try:
                convert_from_keras(keras_path, output_dir, model_name, logger)
                logger.info("Converted: %s -> %s.xml/.bin", keras_path.name, model_name)
                continue
            except Exception as exc:
                logger.exception("Keras conversion failed for %s: %s", keras_path.name, exc)
        else:
            logger.warning("Skip: %s not found", keras_path)


if __name__ == "__main__":
    main()
