import onnxruntime as ort
import numpy as np
import time

def benchmark_cpu_wsl(model_path, iterations=50):
    # Forçar apenas o CPU (padrão no WSL sem configuração de GPU)
    providers = ['CPUExecutionProvider']

    try:
        session = ort.InferenceSession(model_path, providers=providers)
    except Exception as e:
        return f"Erro: {e}"

    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape
    if isinstance(input_shape[2], str): input_shape = [1, 3, 640, 640]

    dummy_input = np.random.randn(*input_shape).astype(np.float32)

    # Aquecimento (Warm-up)
    for _ in range(5):
        session.run(None, {input_name: dummy_input})

    # Medição
    times = []
    for _ in range(iterations):
        t0 = time.time()
        session.run(None, {input_name: dummy_input})
        times.append(time.time() - t0)

    avg_ms = np.mean(times) * 1000
    fps = 1000 / avg_ms

    return {"ms": round(avg_ms, 2), "fps": round(fps, 1)}

modelos = ["yolov8n.onnx", "yolo11n.onnx", "yolo26n.onnx", "yolo26s.onnx"]

print(f"--- BENCHMARK WSL (CPU ONLY - aarch64) ---")
print(f"{'Modelo':<15} | {'Latência (ms)':<15} | {'FPS'}")
print("-" * 45)

for m in modelos:
    import os
    if os.path.exists(m):
        res = benchmark_cpu_wsl(m)
        print(f"{m:<15} | {res['ms']:<15} | {res['fps']}")
    else:
        print(f"{m:<15} | Não encontrado.")
