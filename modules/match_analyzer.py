"""
Class match analyser
"""
import json
import numpy as np
import cv2
import yaml
from tqdm import tqdm
from modules.field_analyst import FieldAnalyst
from modules.player_tracker import PlayerTracker


class NumpyEncoder(json.JSONEncoder):
    """
    to allow safe save
    """
    def default(self, obj):
        """
        deal with np class
        """
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

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

    def process_video(self, video_path, save_annotated_path=None):
        """
        Processa o vídeo respeitando o sample_rate e opcionalmente grava o output.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Configuração do Gravador
        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, (width, height))

        frame_count = 0
        # O intervalo de frames a saltar baseado no sample_rate (segundos)
        frame_interval = max(1, int(fps * self.sample_rate))

        for _ in tqdm(range(total_frames), desc="A analisar (com Sample Rate)"):
            ret, frame = cap.read()
            if not ret:
                break

            # SÓ PROCESSA A IA se for o frame de amostragem
            if frame_count % frame_interval == 0:
                results = self.tracker.track_frame(frame)

                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)

                    for box, p_id in zip(boxes, ids):
                        x1, y1, x2, y2 = map(int, box)
                        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                        # Converte para metros e calcula velocidade
                        pos_m = self.analyst.pixel_to_meters(cx, cy)
                        # dt é o tempo real passado entre amostras
                        self.tracker.calculate_speed(p_id, pos_m, self.sample_rate)

                        # Desenha para o vídeo se a gravação estiver ativa
                        if video_writer:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f"ID: {p_id}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Grava todos os frames para manter o timing do vídeo original
            if video_writer:
                video_writer.write(frame)

            frame_count += 1

        cap.release()
        if video_writer:
            video_writer.release()

        # Aplica filtros nos dados recolhidos
        for p_id in self.tracker.player_data:
            self.tracker.apply_filter(p_id)
            
    def process_video_ia(self, video_path, save_annotated_path=None):
        """
        Processa o vídeo frame a frame e opcionalmente grava o resultado anotado.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Configura o gravador de vídeo apenas se um caminho for fornecido
        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, (width, height))

        for _ in tqdm(range(total_frames), desc="A processar e anotar"):
            ret, frame = cap.read()
            if not ret:
                break

            results = self.tracker.track_frame(frame)

            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy()
                ids = results.boxes.id.cpu().numpy().astype(int)

                for box, p_id in zip(boxes, ids):
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                    # Cálculo de métricas
                    pos_m = self.analyst.pixel_to_meters(cx, cy)
                    self.tracker.calculate_speed(p_id, pos_m, self.sample_rate)

                    # Desenha no frame se save_annotated_path foi definido
                    if video_writer:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"ID: {p_id}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Grava o frame (com ou sem anotações) no novo vídeo
            if video_writer:
                video_writer.write(frame)

        cap.release()
        if video_writer:
            video_writer.release()

        # Aplica filtros de suavização nos dados finais
        for p_id in self.tracker.player_data:
            self.tracker.apply_filter(p_id)

    def process_video_old (self, video_path):
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
                # Mantemos o astype(int) apenas para limpar o float do YOLO,
                # o calculate_speed tratará de passar para string.
                boxes = results.boxes.xyxy.cpu().numpy()
                #ids = results.boxes.id.cpu().numpy().astype(int)
                ids = results.boxes.id.cpu().numpy().astype(int)
                for box, p_id in zip(boxes, ids):
                    cx, cy = (box[0] + box[2]) / 2, box[3]
                    pos_m = self.analyst.pixel_to_meters(cx, cy)
                    self.tracker.calculate_speed(p_id, pos_m, self.sample_rate)

        cap.release()
        for p_id in self.tracker.player_data:
            self.tracker.apply_filter(p_id)

    def save_session(self, output_path):
            """
            Save current Session - Garante que as chaves são strings para o JSON
            """
            # Compreensão de dicionário para converter chaves NumPy int64 em strings nativas
            clean_data = {str(k): v for k, v in self.tracker.player_data.items()}

            with open(output_path, 'w', encoding="utf-8") as f:
                # O NumpyEncoder trata os VALORES (floats e listas do numpy),
                # as chaves agora são strings tratadas pelo clean_data
                json.dump(clean_data, f, cls=NumpyEncoder)

    def save_session_old(self, output_path):
        """
        Save current Session - Agora simplificado
        """
        with open(output_path, 'w', encoding="utf-8") as f:
            # O NumpyEncoder ainda é necessário para os VALORES (arrays numpy),
            # mas as chaves já são strings nativas.
            json.dump(self.tracker.player_data, f, cls=NumpyEncoder)

    def load_session(self, input_path):
        """
        Load previous  Session
        """
        with open(input_path, 'r', encoding="utf-8") as f:
            # Ao carregar, as chaves vêm como strings
            self.tracker.player_data = json.load(f)
