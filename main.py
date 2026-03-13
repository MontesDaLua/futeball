import cv2
import yaml
import numpy as np
import pandas as pd
import torch
from ultralytics import YOLO
from tqdm import tqdm
from fpdf import FPDF
import matplotlib.pyplot as plt
from pathlib import Path
import json

class FieldAnalyst:
    """Gere a calibração de coordenadas e conversão para metros."""
    def __init__(self, pitch_config):
        self.length = pitch_config['length_m']
        self.width = pitch_config['width_m']
        self.homography_matrix = None

    def auto_calibrate(self, frame):
        """Simulação de calibração por deteção de linhas (pode ser expandida com Hough Lines)."""
        h, w = frame.shape[:2]
        # Pontos de origem (exemplo: cantos do campo na imagem)
        src_pts = np.float32([[100, 100], [w-100, 100], [w-10, h-10], [10, h-10]])
        # Pontos de destino (metros no plano real)
        dst_pts = np.float32([[0, 0], [self.length, 0], [self.length, self.width], [0, self.width]])
        self.homography_matrix, _ = cv2.findHomography(src_pts, dst_pts)

    def pixel_to_meters(self, x, y):
        if self.homography_matrix is None: return (0, 0)
        point = np.array([[[x, y]]], dtype='float32')
        transformed = cv2.perspectiveTransform(point, self.homography_matrix)
        return transformed[0][0]

class PlayerTracker:
    """Gere a deteção e rastreio usando Metal Performance Shaders (MPS)."""
    def __init__(self, config):
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.model = YOLO(config['model_size']).to(device)
        self.min_conf = config['min_confidence']
        self.data = {} # {id: {"pos": [], "time": [], "speed": []}}

    def update(self, frame, timestamp):
        results = self.model.track(frame, persist=True, device='mps', verbose=False)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.int().cpu().numpy()

            for box, id in zip(boxes, ids):
                if id not in self.data:
                    self.data[id] = {"pos": [], "time": [], "speed": []}

                # Centro inferior da box (pés do jogador)
                center_x = (box[0] + box[2]) / 2
                feet_y = box[3]
                self.data[id]["pos"].append((center_x, feet_y))
                self.data[id]["time"].append(timestamp)

    def calculate_metrics(self, analyst):
        for p_id, stats in self.data.items():
            if len(stats["pos"]) < 2: continue

            coords = [analyst.pixel_to_meters(p[0], p[1]) for p in stats["pos"]]
            speeds = []
            for i in range(1, len(coords)):
                dist = np.linalg.norm(np.array(coords[i]) - np.array(coords[i-1]))
                dt = stats["time"][i] - stats["time"][i-1]
                speed_kmh = (dist / dt) * 3.6 if dt > 0 else 0
                speeds.append(speed_kmh)

            # Filtro de Mediana para remover ruído de tracking
            stats["speed"] = pd.Series(speeds).rolling(window=3, center=True).median().fillna(0).tolist()

class ReportGenerator:
    """Gera visualizações e o relatório final em PDF."""
    @staticmethod
    def generate_pdf(match_info, tracker, squad):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, f"Relatório de Performance: {match_info['id']}", ln=True, align='C')

        pdf.set_font("Arial", size=10)
        pdf.ln(10)
        pdf.cell(190, 10, f"Estádio: {match_info['stadium']} | Equipas: {match_info['teams'][0]} vs {match_info['teams'][1]}", ln=True)

        for p_id, stats in tracker.data.items():
            name = squad.get(str(p_id), f"Player {p_id}")
            v_max = max(stats["speed"]) if stats["speed"] else 0
            v_med = np.mean(stats["speed"]) if stats["speed"] else 0
            sprints = len([v for v in stats["speed"] if v > 25.2]) # Threshold sprint

            # Adicionar tabela simples
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, f"Jogador: {name}", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(60, 8, f"V. Máx: {v_max:.2f} km/h", border=1)
            pdf.cell(60, 8, f"V. Méd: {v_med:.2f} km/h", border=1)
            pdf.cell(60, 8, f"Sprints: {sprints}", border=1, ln=True)

        pdf.output(f"Relatorio_{match_info['id']}.pdf")

class MatchAnalyzer:
    """Orquestrador do sistema."""
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.analyst = FieldAnalyst(self.config['pitch'])
        self.tracker = PlayerTracker(self.config['analysis'])

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Erro ao abrir o vídeo.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_step = int(fps * self.config['analysis']['sample_rate'])

        # Calibração no primeiro frame
        ret, first_frame = cap.read()
        if ret: self.analyst.auto_calibrate(first_frame)

        for i in tqdm(range(0, total_frames, sample_step), desc="A analisar frames"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret: break

            timestamp = i / fps
            self.tracker.update(frame, timestamp)

        cap.release()
        self.tracker.calculate_metrics(self.analyst)

if __name__ == "__main__":
    analyzer = MatchAnalyzer("config_jogo.yaml")
    # analyzer.process_video("jogo_exemplo.mp4") # Comentar para teste
    # ReportGenerator.generate_pdf(analyzer.config['match_info'], analyzer.tracker, analyzer.config['squad'])
    print("Sistema pronto. Execute com um ficheiro de vídeo válido.")
