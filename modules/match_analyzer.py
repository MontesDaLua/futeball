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
    def __init___old(self, proc_config_path, game_data_path):
        with open(proc_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f)
        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f)

        self.analyst = FieldAnalyst(self.game_data['pitch']['length'],
                                    self.game_data['pitch']['width'])

        self.tracker = PlayerTracker(self.proc_config['analysis']['model_size'],
                                     self.proc_config['analysis']['min_confidence'],
                                     device=self.proc_config['analysis']['device'])

        self.sample_rate = self.proc_config['analysis']['sample_rate']
        self.classes = self.proc_config.get('target_classes', {'person': 0, 'ball': 32})

    def process_video_old(self, video_path, save_annotated_path=None):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = int(cap.get(3)), int(cap.get(4))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Intervalo baseado no sample_rate
        frame_interval = max(1, int(fps * self.sample_rate))

        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, (w, h))

        for frame_count in tqdm(range(total_frames), desc="A analisar Jogo"):
            ret, frame = cap.read()
            if not ret: break

            # Processa lógica apenas no frame de amostragem
            if frame_count % frame_interval == 0:
                # Passamos as classes pretendidas para o tracker
                results = self.tracker.model.track(
                    frame, persist=True, conf=self.tracker.min_confidence,
                    classes=list(self.classes.values()), verbose=False, device=self.tracker.device
                )[0]

                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)
                    clss = results.boxes.cls.cpu().numpy().astype(int)

                    for box, p_id, cls in zip(boxes, ids, clss):
                        x1, y1, x2, y2 = map(int, box)
                        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                        # Distinguir visualmente Bola vs Pessoas
                        color = (0, 0, 255) if cls == self.classes['ball'] else (0, 255, 0)
                        label = "BOLA" if cls == self.classes['ball'] else f"ID:{p_id}"

                        # Guardar dados (usamos o ID para tudo, a classe ajuda na legenda)
                        pos_m = self.analyst.pixel_to_meters(cx, cy)
                        self.tracker.calculate_speed(f"{label}_{p_id}", pos_m, self.sample_rate)

                        if video_writer:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if video_writer:
                video_writer.write(frame)

        cap.release()
        if video_writer: video_writer.release()


    def __init__(self, proc_config_path, game_data_path):
        """
        Construtor atualizado para dois ficheiros de configuração
        """
        with open(proc_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f)

        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f)

        # AGORA USAMOS 'game_data' para o campo (pitch)
        self.analyst = FieldAnalyst(
            self.game_data['pitch']['length'],
            self.game_data['pitch']['width']
        )

        # AGORA USAMOS 'proc_config' para a IA
        self.tracker = PlayerTracker(
            self.proc_config['analysis']['model_size'],
            self.proc_config['analysis']['min_confidence'],
            device=self.proc_config['analysis']['device']
        )

        self.sample_rate = self.proc_config['analysis']['sample_rate']
        # Classes: 0 para pessoas, 32 para bola
        self.target_classes = self.proc_config.get('target_classes', {'person': 0, 'ball': 32})

    def process_video(self, video_path, save_annotated_path=None):
        """
        Processa o vídeo usando as configurações separadas
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Intervalo de amostragem
        frame_interval = max(1, int(fps * self.sample_rate))

        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, (width, height))

        for frame_idx in tqdm(range(total_frames), desc="Análise"):
            ret, frame = cap.read()
            if not ret: break

            if frame_idx % frame_interval == 0:
                # Filtrar classes (jogadores, árbitro e bola)
                results = self.tracker.model.track(
                    frame,
                    persist=True,
                    conf=self.tracker.min_confidence,
                    classes=list(self.target_classes.values()),
                    device=self.tracker.device,
                    verbose=False
                )[0]

                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)
                    clss = results.boxes.cls.cpu().numpy().astype(int)

                    for box, p_id, cls in zip(boxes, ids, clss):
                        x1, y1, x2, y2 = map(int, box)
                        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                        # Identificação visual
                        is_ball = (cls == self.target_classes['ball'])
                        color = (0, 0, 255) if is_ball else (0, 255, 0)
                        label = "BOLA" if is_ball else f"ID:{p_id}"

                        # Guardar métricas (usamos prefixo para a bola não misturar com jogadores)
                        obj_key = f"ball_{p_id}" if is_ball else str(p_id)
                        pos_m = self.analyst.pixel_to_meters(cx, cy)
                        self.tracker.calculate_speed(obj_key, pos_m, self.sample_rate)

                        if video_writer:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(frame, label, (x1, y1-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if video_writer:
                video_writer.write(frame)

        cap.release()
        if video_writer: video_writer.release()






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

    def load_session(self, input_path):
        """
        Load previous  Session
        """
        with open(input_path, 'r', encoding="utf-8") as f:
            # Ao carregar, as chaves vêm como strings
            self.tracker.player_data = json.load(f)

class MatchAnalyzer_ia1:
    """
    Match Analyser
    """
    def __init__(self, processor_config_path, game_data_path):
        # Carregar definições técnicas
        with open(processor_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f)

        # Carregar dados do jogo
        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f)

        print(f"game_data:{game_data}")
        # Inicializar componentes com os novos caminhos
        self.analyst = FieldAnalyst(
            self.game_data['pitch']['length'],
            self.game_data['pitch']['width']
        )

        self.tracker = PlayerTracker(
            self.proc_config['analysis']['model_size'],
            self.proc_config['analysis']['min_confidence'],
            device=self.proc_config['analysis']['device']
        )

        self.sample_rate = self.proc_config['analysis']['sample_rate']
        self.target_classes = self.proc_config.get('target_classes', {'person': 0, 'ball': 32})

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

    def load_session(self, input_path):
        """
        Load previous  Session
        """
        with open(input_path, 'r', encoding="utf-8") as f:
            # Ao carregar, as chaves vêm como strings
            self.tracker.player_data = json.load(f)

class MatchAnalyzer_old:
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

    def load_session(self, input_path):
        """
        Load previous  Session
        """
        with open(input_path, 'r', encoding="utf-8") as f:
            # Ao carregar, as chaves vêm como strings
            self.tracker.player_data = json.load(f)
