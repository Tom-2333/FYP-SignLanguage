import json
import os
import subprocess
import time
import argparse
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
 
tf = None


SEED = 42
np.random.seed(SEED)


def inject_windows_cuda_paths():
    """Inject CUDA/cuDNN DLL paths before importing TensorFlow."""
    project_root = Path(__file__).resolve().parents[1]

    candidates = [
        Path(r"C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.5/bin"),
        project_root / "third_party" / "cudnn-8.9.7-cuda11" / "bin",
        Path.cwd() / "third_party" / "cudnn-8.9.7-cuda11" / "bin",
        Path.cwd() / "cv_hands" / "third_party" / "cudnn-8.9.7-cuda11" / "bin",
    ]

    picked = []
    for p in candidates:
        if p.exists():
            picked.append(str(p))

    if picked:
        existing = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(picked + [existing])

    return picked


def init_tensorflow():
    """Import TensorFlow only after DLL search paths are prepared."""
    global tf
    if tf is not None:
        return tf

    inject_windows_cuda_paths()
    import tensorflow as _tf

    tf = _tf
    tf.random.set_seed(SEED)
    return tf


@dataclass
class TrialResult:
    mode: str
    batch_size: int
    epochs: int
    samples: int
    ok: bool
    error_type: str
    error_msg: str
    seconds: float
    gpu_memory_before_mb: float
    gpu_memory_after_mb: float


def get_nvidia_smi_memory_mb():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()
        first = out.splitlines()[0].strip()
        return float(first)
    except Exception:
        return -1.0


def setup_gpu_memory_growth():
    init_tensorflow()
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        try:
            tf.config.experimental.set_memory_growth(gpu, True)
        except Exception:
            pass
    return gpus


def build_tiny_model(seq_len=25, feat_dim=80, classes=156):
    init_tensorflow()
    inp = tf.keras.Input(shape=(seq_len, feat_dim))
    x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(64, return_sequences=True))(inp)
    x = tf.keras.layers.Bidirectional(tf.keras.layers.GRU(32))(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    out = tf.keras.layers.Dense(classes, activation="softmax")(x)
    model = tf.keras.Model(inp, out)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def make_fake_data(samples=8192, seq_len=25, feat_dim=80, classes=156):
    x = np.random.normal(size=(samples, seq_len, feat_dim)).astype(np.float32)
    y = np.random.randint(0, classes, size=(samples,), dtype=np.int32)
    return x, y


def make_dataset(x, y, batch_size):
    init_tensorflow()
    ds = tf.data.Dataset.from_tensor_slices((x, y))
    ds = ds.shuffle(min(4096, len(x)), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def run_trial(mode, batch_size, x, y):
    init_tensorflow()
    tf.keras.backend.clear_session()
    mem_before = get_nvidia_smi_memory_mb()
    model = build_tiny_model(classes=int(np.max(y) + 1))
    start = time.time()

    try:
        if mode == "numpy":
            model.fit(x, y, batch_size=batch_size, epochs=1, verbose=0)
        elif mode == "dataset":
            ds = make_dataset(x, y, batch_size)
            model.fit(ds, epochs=1, verbose=0)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        return TrialResult(
            mode=mode,
            batch_size=batch_size,
            epochs=1,
            samples=int(len(x)),
            ok=True,
            error_type="",
            error_msg="",
            seconds=time.time() - start,
            gpu_memory_before_mb=mem_before,
            gpu_memory_after_mb=get_nvidia_smi_memory_mb(),
        )
    except Exception as e:
        return TrialResult(
            mode=mode,
            batch_size=batch_size,
            epochs=1,
            samples=int(len(x)),
            ok=False,
            error_type=type(e).__name__,
            error_msg=str(e),
            seconds=time.time() - start,
            gpu_memory_before_mb=mem_before,
            gpu_memory_after_mb=get_nvidia_smi_memory_mb(),
        )


def classify(results):
    errors = [r for r in results if not r.ok]
    if not errors:
        return "No failure reproduced in this run."

    has_oom = any("ResourceExhausted" in r.error_type or "OOM" in r.error_msg for r in errors)
    has_internal = any("InternalError" in r.error_type or "Dst tensor is not initialized" in r.error_msg for r in errors)

    # Same-batch contrast: numpy fails but dataset passes indicates transfer instability.
    by_batch = {}
    for r in results:
        by_batch.setdefault(r.batch_size, {})[r.mode] = r

    transfer_pattern = False
    for b, modes in by_batch.items():
        n = modes.get("numpy")
        d = modes.get("dataset")
        if n and d and (not n.ok) and d.ok:
            transfer_pattern = True
            break

    if has_oom and not has_internal:
        return "Likely VRAM pressure (OOM/ResourceExhausted dominant)."
    if has_internal and transfer_pattern:
        return "Likely GPU init/host->device transfer instability (numpy fails, dataset passes at same batch)."
    if has_internal:
        return "Likely GPU initialization/copy instability (InternalError dominant)."
    return "Mixed failure modes; check driver/CUDA/cuDNN/TF compatibility and rerun."


def run_trial_with_epochs(mode, batch_size, epochs, x, y):
    tf.keras.backend.clear_session()
    mem_before = get_nvidia_smi_memory_mb()
    model = build_tiny_model(classes=int(np.max(y) + 1))
    start = time.time()

    try:
        if mode == "numpy":
            model.fit(x, y, batch_size=batch_size, epochs=epochs, verbose=0)
        elif mode == "dataset":
            ds = make_dataset(x, y, batch_size)
            model.fit(ds, epochs=epochs, verbose=0)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        return TrialResult(
            mode=mode,
            batch_size=batch_size,
            epochs=epochs,
            samples=int(len(x)),
            ok=True,
            error_type="",
            error_msg="",
            seconds=time.time() - start,
            gpu_memory_before_mb=mem_before,
            gpu_memory_after_mb=get_nvidia_smi_memory_mb(),
        )
    except Exception as e:
        return TrialResult(
            mode=mode,
            batch_size=batch_size,
            epochs=epochs,
            samples=int(len(x)),
            ok=False,
            error_type=type(e).__name__,
            error_msg=str(e),
            seconds=time.time() - start,
            gpu_memory_before_mb=mem_before,
            gpu_memory_after_mb=get_nvidia_smi_memory_mb(),
        )


def parse_batch_list(text):
    values = []
    for p in text.split(","):
        p = p.strip()
        if not p:
            continue
        values.append(int(p))
    if not values:
        raise ValueError("Batch list is empty. Example: 8,16,32,64")
    return values


def parse_args():
    parser = argparse.ArgumentParser(description="Diagnose GPU stability: VRAM pressure vs init/copy instability")
    parser.add_argument("--mode", choices=["quick", "default", "stress"], default="default")
    parser.add_argument("--input-mode", choices=["both", "numpy", "dataset"], default="both")
    parser.add_argument("--samples", type=int, default=None, help="Override sample count")
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs per trial")
    parser.add_argument("--batches", type=str, default=None, help="Comma separated batches, e.g. 8,16,32,64")
    parser.add_argument("--ramp-from", type=int, default=None, help="Start batch size for ramp-up test")
    parser.add_argument("--ramp-step", type=int, default=16, help="Batch increment for ramp-up test")
    parser.add_argument("--ramp-max", type=int, default=512, help="Maximum batch size for ramp-up test")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop immediately on first failed trial")
    parser.add_argument("--save", type=str, default=None, help="Output json path")
    return parser.parse_args()


def resolve_plan(args):
    if args.mode == "quick":
        samples = 4096
        epochs = 1
        batches = [8, 16, 32]
    elif args.mode == "stress":
        samples = 65536
        epochs = 3
        batches = [16, 32, 64, 96, 128]
    else:
        samples = 8192
        epochs = 1
        batches = [8, 16, 32, 64, 96, 128]

    if args.samples is not None:
        samples = int(args.samples)
    if args.epochs is not None:
        epochs = int(args.epochs)
    if args.batches is not None:
        batches = parse_batch_list(args.batches)
    if args.ramp_from is not None:
        if args.ramp_step <= 0:
            raise ValueError("--ramp-step must be > 0")
        if args.ramp_max < args.ramp_from:
            raise ValueError("--ramp-max must be >= --ramp-from")
        batches = list(range(args.ramp_from, args.ramp_max + 1, args.ramp_step))
        if not batches:
            raise ValueError("Ramp generated empty batch list")

    return samples, epochs, batches


def main():
    init_tensorflow()
    dll_paths = inject_windows_cuda_paths()
    args = parse_args()
    samples, epochs, batch_sizes = resolve_plan(args)

    print("=== GPU Stability Diagnose ===")
    print("TensorFlow:", tf.__version__)
    print("Keras:", getattr(tf.keras, "__version__", "unknown"))
    print("Python CUDA visible devices:", os.environ.get("CUDA_VISIBLE_DEVICES", "(not set)"))
    print("Injected DLL paths:", dll_paths)
    print(
        f"Plan mode={args.mode}, input_mode={args.input_mode}, "
        f"samples={samples}, epochs={epochs}, batches={batch_sizes}, "
        f"stop_on_error={args.stop_on_error}"
    )

    gpus = setup_gpu_memory_growth()
    print("GPUs:", gpus)
    if not gpus:
        print("No GPU detected. Cannot diagnose VRAM vs GPU transfer instability.")
        return

    x, y = make_fake_data(samples=samples)
    if args.input_mode == "numpy":
        modes = ["numpy"]
    elif args.input_mode == "dataset":
        modes = ["dataset"]
    else:
        modes = ["numpy", "dataset"]

    results = []
    stop_triggered = False
    for b in batch_sizes:
        for m in modes:
            print(f"Running trial: mode={m}, batch={b}")
            r = run_trial_with_epochs(m, b, epochs, x, y)
            results.append(r)
            status = "OK" if r.ok else f"FAIL({r.error_type})"
            print(
                f"  -> {status}, {r.seconds:.2f}s, "
                f"epochs={r.epochs}, samples={r.samples}, "
                f"mem {r.gpu_memory_before_mb:.0f}->{r.gpu_memory_after_mb:.0f} MB"
            )
            if args.stop_on_error and (not r.ok):
                print("Stop-on-error triggered; ending ramp test early.")
                stop_triggered = True
                break
        if stop_triggered:
            break

    summary = {
        "results": [asdict(r) for r in results],
        "diagnosis": classify(results),
    }

    print("\n=== Diagnosis ===")
    print(summary["diagnosis"])

    out_path = args.save or "gpu_stability_diagnosis_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved detailed report: {out_path}")


if __name__ == "__main__":
    main()
