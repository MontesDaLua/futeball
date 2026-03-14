"""
Class match analyser
"""
import json
import cv2
import yaml
from tqdm import tqdm
from modules.field_analyst import FieldAnalyst
from modules.player_tracker import PlayerTracker

class MatchAnalyzer:
    """
    Match Analyser
    """
    def __init__(self, config_path):
        """
        Constructor
        """
        with open(config_path, 'r', encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.analyst = FieldAnalyst(self.config['pitch']['length'],
                                    self.config['pitch']['width'])
        self.tracker = PlayerTracker(self.config['analysis']['model_size'],
                                     self.config['analysis']['min_confidence'])
        self.sample_rate = self.config['analysis']['sample_rate']

    def process_video(self, video_path):
        # pylint: disable=too-many-locals
        """
        Video Processor
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Erro ao abrir vídeo: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_step = int(fps * self.sample_rate) or 1

        # Simulação de calibração (num sistema real, isto seria detetado na frame 0)
        # Exemplo de pontos para um campo 1080p genérico
        self.analyst.calibrate([[200, 300], [1700, 300], [1850, 900], [50, 900]])

        for i in tqdm(range(0, total_frames, frame_step), desc="A analisar frames"):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break

            results = self.tracker.track_frame(frame)
            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                ids = results.boxes.id.cpu().numpy().astype(int)

                for box, p_id in zip(boxes, ids):
                    # Centro inferior do bounding box (pés do jogador)
                    cx, cy = (box[0] + box[2]) / 2, box[3]
                    pos_m = self.analyst.pixel_to_meters(cx, cy)
                    self.tracker.calculate_speed(p_id, pos_m, self.sample_rate)

        cap.release()
        for p_id in self.tracker.player_data:
            self.tracker.apply_filter(p_id)

    def save_session(self, output_path):
        """
        Save current Session
        """
        with open(output_path, 'w', encoding="utf-8") as f:
            json.dump(self.tracker.player_data, f)

    def load_session(self, input_path):
        """
        Load previous  Session
        """
        with open(input_path, 'r', encoding="utf-8") as f:
            self.tracker.player_data = json.load(f)
