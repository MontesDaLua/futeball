"""
Módulo PlayerTracker
Correção: Garantir que player_data armazena apenas tipos básicos.
"""
from ultralytics import YOLO
import numpy as np

class PlayerTracker:
    def __init__(self, model_size, min_confidence, device='cpu'):
        self.model = YOLO(f"{model_size}.pt")
        self.min_confidence = min_confidence
        self.device = device
        self.player_data = {} # {id: {"positions": [], "speeds": []}}

    def track_frame(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            device=self.device,
            conf=self.min_confidence,
            classes=[0, 32],
            verbose=False
        )
        return results[0]

    def calculate_speed(self, player_id, current_pos_m, dt):
        p_id = str(player_id)
        if p_id not in self.player_data:
            self.player_data[p_id] = {"positions": [], "speeds": []}

        data = self.player_data[p_id]

        # Garantir que current_pos_m é uma lista [x, y] de floats nativos
        if hasattr(current_pos_m, "tolist"):
            current_pos_m = current_pos_m.tolist()

        if data["positions"]:
            prev_pos = data["positions"][-1]
            dist = np.sqrt((current_pos_m[0] - prev_pos[0])**2 +
                           (current_pos_m[1] - prev_pos[1])**2)
            speed_kmh = (dist / dt) * 3.6
            data["speeds"].append(float(speed_kmh)) # Float nativo

        data["positions"].append(current_pos_m)
