import tensorflow as tf


def main() -> int:
    print(f"TF_VERSION={tf.__version__}")
    print(f"IS_BUILT_WITH_CUDA={tf.test.is_built_with_cuda()}")

    build_info = tf.sysconfig.get_build_info()
    print(f"CUDA_VERSION={build_info.get('cuda_version')}")
    print(f"CUDNN_VERSION={build_info.get('cudnn_version')}")

    physical_gpus = tf.config.list_physical_devices("GPU")
    logical_gpus = tf.config.list_logical_devices("GPU")
    print(f"PHYSICAL_GPUS={physical_gpus}")
    print(f"LOGICAL_GPUS={logical_gpus}")

    matmul_ok = False
    gpu_error = ""

    try:
        if physical_gpus:
            with tf.device("/GPU:0"):
                a = tf.random.normal([2048, 2048])
                b = tf.random.normal([2048, 2048])
                c = tf.matmul(a, b)
                _ = c.numpy()
            matmul_ok = True
    except Exception as error:
        gpu_error = str(error)

    print(f"GPU_COUNT={len(physical_gpus)}")
    print(f"GPU_MATMUL_OK={matmul_ok}")
    print(f"GPU_ERROR={gpu_error}")

    if physical_gpus and matmul_ok:
        print("RESULT=PASS")
        return 0

    print("RESULT=FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
