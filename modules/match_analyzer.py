"""
Módulo MatchAnalyzer: Responsável pelo processamento de vídeo.
Correção: Conversão explícita de Tensors para tipos nativos Python.
"""
import os
import json
import numpy as np
import cv2
import yaml
from tqdm import tqdm
from modules.field_analyst import FieldAnalyst
from modules.player_tracker import PlayerTracker

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class MatchAnalyzer:
    def __init__(self, proc_config_path, game_data_path):
        with open(proc_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f) or {}
        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f) or {}

        pitch = self.game_data.get('pitch', {})
        self.analyst = FieldAnalyst(pitch.get('length', 105), pitch.get('width', 68))

        analysis_cfg = self.proc_config.get('analysis', {})
        self.tracker = PlayerTracker(
            model_size=analysis_cfg.get('model_size', 'yolov8n'),
            min_confidence=analysis_cfg.get('min_confidence', 0.3),
            device=analysis_cfg.get('device', 'cpu')
        )

        self.sample_rate = analysis_cfg.get('sample_rate', 0.1)
        self.extracted_ids = set()
        self.ignore_ids = [str(i) for i in self.game_data.get('ignore_ids', [])]
        self.squad = self.game_data.get('squad', {})

        # Mapeamento de IDs (Same As)
        self.id_map = {}
        for master, aliases in self.game_data.get('same_as', {}).items():
            if isinstance(aliases, list):
                for a in aliases: self.id_map[str(a)] = str(master)
            else:
                self.id_map[str(aliases)] = str(master)

    def _get_dominant_color(self, image):
        if image is None or image.size == 0: return "desconhecido"
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, w, _ = hsv.shape
        roi = hsv[int(h*0.3):int(h*0.6), int(w*0.2):int(w*0.8)]
        hist = cv2.calcHist([roi], [0], None, [180], [0, 180])
        hue = np.argmax(hist)
        if hue < 10 or hue > 160: return "vermelho"
        if 85 <= hue < 130: return "azul"
        return "outra_cor"

    def process_video(self, video_path, save_annotated_path=None, gallery_dir=None):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        interval = max(1, int(fps * self.sample_rate))

        if gallery_dir: os.makedirs(gallery_dir, exist_ok=True)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            f_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if f_idx % interval == 0:
                results = self.tracker.track_frame(frame)

                # CORREÇÃO: Verificar se existem IDs e convertê-los de Tensor para CPU/Numpy
                if hasattr(results.boxes, 'id') and results.boxes.id is not None:
                    # Converter todos os dados do frame para listas Python nativas
                    boxes = results.boxes.xyxy.cpu().numpy().tolist()
                    ids = results.boxes.id.cpu().numpy().astype(int).tolist()
                    clss = results.boxes.cls.cpu().numpy().astype(int).tolist()

                    for box, raw_id, cls in zip(boxes, ids, clss):
                        # p_id convertido para string nativa
                        raw_id_str = str(raw_id)
                        p_id = self.id_map.get(raw_id_str, raw_id_str)

                        # Filtros
                        if p_id in self.ignore_ids or p_id in self.squad:
                            continue

                        # Salvar galeria
                        if gallery_dir and cls == 0 and p_id not in self.extracted_ids:
                            x1, y1, x2, y2 = map(int, box)
                            crop = frame[max(0, y1):min(frame.shape[0], y2),
                                         max(0, x1):min(frame.shape[1], x2)]
                            color = self._get_dominant_color(crop)
                            prefix = f"{color}_{p_id}"

                            cv2.imwrite(os.path.join(gallery_dir, f"{prefix}_crop.jpg"), crop)
                            f_copy = frame.copy()
                            cv2.rectangle(f_copy, (x1, y1), (x2, y2), (0, 255, 255), 2)
                            cv2.imwrite(os.path.join(gallery_dir, f"{prefix}_full.jpg"), f_copy)
                            self.extracted_ids.add(p_id)

                        # Métricas (pos_m será uma lista de floats nativos)
                        center_x = (box[0] + box[2]) / 2
                        center_y = (box[1] + box[3]) / 2
                        pos_m = self.analyst.pixel_to_meters(center_x, center_y)

                        # Garantir que pos_m é uma lista de floats simples
                        if isinstance(pos_m, np.ndarray): pos_m = pos_m.tolist()

                        self.tracker.calculate_speed(p_id, pos_m, self.sample_rate)

        cap.release()

    def save_session(self, output_path):
        """Guarda os dados garantindo que não há objetos complexos."""
        # O tracker.player_data já deve conter apenas listas e floats nativos agora
        clean_data = {str(k): v for k, v in self.tracker.player_data.items()}
        with open(output_path, 'w', encoding="utf-8") as f:
            json.dump(clean_data, f, cls=NumpyEncoder, indent=4)
