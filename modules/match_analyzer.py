"""
Módulo MatchAnalyzer: Responsável pelo processamento de vídeo,
extração de métricas táticas e organização da galeria por cores.
"""
import os
import json
import numpy as np
import cv2
import yaml
import time
from tqdm import tqdm
from modules.field_analyst import FieldAnalyst
from modules.player_tracker import PlayerTracker

class NumpyEncoder(json.JSONEncoder):
    """Permite converter tipos NumPy para formatos compatíveis com JSON."""
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class MatchAnalyzer:
    """
    Classe principal para análise de jogo. Gere o ciclo de vida do vídeo,
    desde o tracking até à exportação de dados e capturas de ecrã.
    """
    def __init__(self, proc_config_path, game_data_path):
        # 1. Carregamento Seguro dos YAMLs
        with open(proc_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f) or {}
        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f) or {}

        # 2. Configuração do Campo (FieldAnalyst)
        pitch = self.game_data.get('pitch', {})
        self.analyst = FieldAnalyst(pitch.get('length', 105), pitch.get('width', 68))

        # 3. Inicialização do Tracker (YOLO)
        analysis_cfg = self.proc_config.get('analysis', {})
        self.tracker = PlayerTracker(
            model_size=analysis_cfg.get('model_size', 'yolov8n'),
            min_confidence=analysis_cfg.get('min_confidence', 0.3),
            device=analysis_cfg.get('device', 'cpu')
        )

        # 4. Parâmetros de Processamento
        self.sample_rate = analysis_cfg.get('sample_rate', 0.1)
        self.extracted_ids = set()

        # Sincronização de IDs (same_as) e ignore_ids
        self.ignore_ids = [str(i) for i in self.game_data.get('ignore_ids', [])]
        self.squad = self.game_data.get('squad', {})
        self.id_translation = {}
        for master, aliases in self.game_data.get('same_as', {}).items():
            for alias in aliases:
                self.id_translation[str(alias)] = str(master)

    def _get_dominant_color(self, image):
        """Analisa o centro do crop (tronco) para classificar a cor da camisola."""
        if image is None or image.size == 0: return "desconhecido"
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, w, _ = hsv.shape
        # ROI: foca na área central para evitar o relvado ou calções
        roi = hsv[int(h*0.3):int(h*0.6), int(w*0.2):int(w*0.8)]
        hist = cv2.calcHist([roi], [0], None, [180], [0, 180])
        hue = np.argmax(hist)

        if hue < 10 or hue > 160: return "vermelho"
        if 10 <= hue < 25: return "laranja"
        if 25 <= hue < 35: return "amarelo"
        if 35 <= hue < 85: return "verde"
        if 85 <= hue < 130: return "azul"
        if 130 <= hue < 160: return "roxo"
        return "branco_cinza"

    def process_video(self, video_path, save_annotated_path=None, gallery_dir=None):
        """Loop principal que processa os frames do vídeo."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, int(fps * self.sample_rate))

        if gallery_dir: os.makedirs(gallery_dir, exist_ok=True)

        writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            size = (int(cap.get(3)), int(cap.get(4)))
            writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, size)

        start_time = time.time()
        for f_idx in tqdm(range(total_f), desc="Analisando Partida"):
            ret, frame = cap.read()
            if not ret: break

            if f_idx % interval == 0:
                results = self.tracker.track_frame(frame)
                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)
                    clss = results.boxes.cls.cpu().numpy().astype(int)

                    for box, raw_id, cls in zip(boxes, ids, clss):
                        p_id_str = self.id_translation.get(str(raw_id), str(raw_id))

                        # Ignorar se já estiver no YAML ou identificado
                        if p_id_str in self.ignore_ids or p_id_str in self.squad:
                            continue

                        # Guardar na galeria se for uma pessoa (cls 0)
                        if gallery_dir and cls == 0 and p_id_str not in self.extracted_ids:
                            x1, y1, x2, y2 = map(int, box)
                            crop = frame[max(0, y1):min(frame.shape[0], y2),
                                         max(0, x1):min(frame.shape[1], x2)]

                            color = self._get_dominant_color(crop)
                            prefix = f"{color}_{p_id_str}"

                            # Salvar Par de Imagens: Crop e Total
                            cv2.imwrite(os.path.join(gallery_dir, f"{prefix}_crop.jpg"), crop)
                            full_v = frame.copy()
                            cv2.rectangle(full_v, (x1, y1), (x2, y2), (0, 255, 255), 3)
                            cv2.imwrite(os.path.join(gallery_dir, f"{prefix}_full.jpg"), full_v)
                            self.extracted_ids.add(p_id_str)

                        # Cálculo de Métricas Reais
                        pos_m = self.analyst.pixel_to_meters((box[0]+box[2])/2, (box[1]+box[3])/2)
                        label = "ball" if cls == 32 else "player"
                        self.tracker.calculate_speed(f"{label}_{p_id_str}", pos_m, self.sample_rate)

            if writer: writer.write(frame)

        cap.release()
        if writer: writer.release()
        self._print_summary(start_time, total_f)

    def _print_summary(self, start_time, total_frames):
        duration = time.time() - start_time
        print(f"\n✅ Análise concluída em {duration:.2f}s")
        print(f"📊 Foram extraídos {len(self.extracted_ids)} novos IDs para revisão.")

    def save_session(self, output_path):
        """Exporta os dados acumulados para JSON."""
        clean_data = {str(k): v for k, v in self.tracker.player_data.items()}
        with open(output_path, 'w', encoding="utf-8") as f:
            json.dump(clean_data, f, cls=NumpyEncoder, indent=4)
