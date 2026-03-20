"""
Class PlayerTracker
"""
from ultralytics import YOLO
import numpy as np
from scipy.signal import medfilt

class PlayerTracker:
    """
    Player Tracker
    """
    def __init__(self, model_size, min_confidence, device='mps'):
        """
        Constructor
        """
        self.model = YOLO(f"{model_size}.pt")
        self.min_confidence = min_confidence
        self.device = device
        self.player_data = {} # {id: {"positions": [], "speeds": []}}

    def track_frame(self, frame):
        """
        Rastreio de frames filtrando por pessoas (0) e bola (32)
        """
        results = self.model.track(
            frame,
            persist=True,
            device=self.device,
            conf=self.min_confidence,
            classes=[0, 32],  # Adicionado filtro de classes
            verbose=False
        )
        return results[0]
        
    def track_frame_old(self, frame):
        """
        specific frame track
        """
        results = self.model.track(frame,
                                    persist=True,
                                    device=self.device,
                                    conf=self.min_confidence,
                                    verbose=False)
        return results[0]

    def calculate_speed(self, player_id, current_pos_m, dt):
            """
            Calculate player speed - Força ID como string para evitar erros de tipo
            """
            p_id = str(player_id) # Conversão imediata para string

            if p_id not in self.player_data:
                self.player_data[p_id] = {"positions": [], "speeds": []}

            data = self.player_data[p_id] # Usa p_id (string) e não player_id (int64)

            if data["positions"]:
                prev_pos = data["positions"][-1]
                dist = np.sqrt((current_pos_m[0] - prev_pos[0])**2 +
                                (current_pos_m[1] - prev_pos[1])**2)
                speed_mps = dist / dt
                speed_kmh = speed_mps * 3.6
                data["speeds"].append(speed_kmh)

            data["positions"].append(current_pos_m)

    def calculate_speed_old(self, player_id, current_pos_m, dt):
        """
        Calculate player speed - Força ID como string
        """
        p_id = str(player_id) # Conversão imediata

        if p_id not in self.player_data:
            self.player_data[p_id] = {"positions": [], "speeds": []}

        data = self.player_data[p_id]

        if player_id not in self.player_data:
            self.player_data[player_id] = {"positions": [], "speeds": []}

        data = self.player_data[player_id]
        if data["positions"]:
            prev_pos = data["positions"][-1]
            dist = np.sqrt((current_pos_m[0] - prev_pos[0])**2 +\
                            (current_pos_m[1] - prev_pos[1])**2)
            speed_mps = dist / dt
            speed_kmh = speed_mps * 3.6
            data["speeds"].append(speed_kmh)

        data["positions"].append(current_pos_m)

    def apply_filter(self, player_id):
        """
        To describe
        """
        if len(self.player_data[player_id]["speeds"]) > 5:
            self.player_data[player_id]["speeds"] = medfilt(
                                        self.player_data[player_id]["speeds"],
                                        kernel_size=5).tolist()
