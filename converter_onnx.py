import os
from ultralytics import YOLO

# 1. Define aqui a tua lista de modelos (.pt)
modelos_para_converter = [
    "yolov8n.pt",
    "yolo11n.pt",
    "yolo26n.pt",
    "yolo26s.pt"
]

def exportar_modelos_para_onnx(lista_modelos, imgsz=640):
    for modelo_pt in lista_modelos:
        # Define o nome do ficheiro de saída (troca .pt por .onnx)
        modelo_onnx = modelo_pt.replace(".pt", ".onnx")

        print(f"\n--- Verificando: {modelo_pt} ---")

        # Verifica se o ficheiro já existe no disco
        if os.path.exists(modelo_onnx):
            print(f"⏩ Pulando: '{modelo_onnx}' já existe.")
            continue

        try:
            print(f"🚀 Exportando '{modelo_pt}' para ONNX...")
            # Carrega o modelo
            model = YOLO(modelo_pt)

            # Exporta com otimizações para DirectML (simplify=True)
            # O half=True é opcional, mas ajuda muito em ARM se a GPU suportar FP16
            model.export(format="onnx", imgsz=imgsz, simplify=True)

            print(f"✅ Sucesso: '{modelo_onnx}' criado.")
        except Exception as e:
            print(f"❌ Erro ao exportar {modelo_pt}: {e}")

if __name__ == "__main__":
    exportar_modelos_para_onnx(modelos_para_converter)
