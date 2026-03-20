"""
Class match analyser
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

    def __init__(self, proc_config_path, game_data_path):
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

        # --- LINHAS A ADICIONAR ---
        self.target_classes = [0, 32]  # 0: Pessoa (Jogadores/Árbitros), 32: Bola
        self.extracted_ids = set()      # Conjunto para evitar duplicados na galeria

        # Carregar lista de IDs a ignorar (converte para string para consistência)
        raw_ignore = self.game_data.get('ignore_ids', [])
        self.ignore_ids = [str(i) for i in raw_ignore]

    def process_video(self, video_path, save_annotated_path=None, gallery_dir=None):
        """
        Processamento de vídeo com galeria exclusiva para jogadores NÃO identificados.
        """
        import os
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = int(cap.get(3)), int(cap.get(4))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(fps * self.sample_rate))

        # 1. Setup do VideoWriter
        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps, (w, h))

        # 2. Setup da Galeria e Mapeamento do Squad
        if gallery_dir:
            os.makedirs(gallery_dir, exist_ok=True)

        # Obtemos a lista de IDs que já têm nome atribuído no YAML
        squad = self.game_data.get('squad', {})
        identified_ids = [str(k) for k in squad.keys()]
        ref_id = str(squad.get('referee_id', ''))

        for frame_idx in tqdm(range(total_frames), desc="A analisar"):
            ret, frame = cap.read()
            if not ret: break

            if frame_idx % frame_interval == 0:
                results = self.tracker.track_frame(frame)

                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)
                    clss = results.boxes.cls.cpu().numpy().astype(int)

                    for box, p_id, cls in zip(boxes, ids, clss):
                        p_id_str = str(p_id)

                        # --- FILTRO 1: Ignorar IDs explicitamente excluídos ---
                        if p_id_str in self.ignore_ids:
                            continue

                        # Identificação de tipos
                        is_ball = (cls == 32)
                        is_ref = (p_id_str == ref_id)
                        # Verificar se o ID já existe no dicionário 'squad' do YAML
                        is_identified = (p_id_str in identified_ids)

                        # Definição de labels para o tracking
                        if is_ball:
                            prefix, color, label = "ball", (0, 0, 255), "BOLA"
                        elif is_ref:
                            prefix, color, label = "referee", (255, 255, 0), f"REF:{p_id}"
                        else:
                            prefix, color, label = "player", (0, 255, 0), f"ID:{p_id}"

                        # --- LÓGICA DA GALERIA REFINADA ---
                        # Só guarda se:
                        # - gallery_dir existe
                        # - É um jogador (cls 0 e não é árbitro)
                        # - NÃO está na lista de identificados (squad)
                        # - Ainda não extraímos este ID nesta sessão
                        if (gallery_dir and cls == 0 and not is_ref and
                            not is_identified and p_id_str not in self.extracted_ids):

                            x1, y1, x2, y2 = map(int, box)
                            crop = frame[max(0, y1-15):min(h, y2+15), max(0, x1-15):min(w, x2+15)]
                            if crop.size > 0:
                                cv2.imwrite(os.path.join(gallery_dir, f"unidentified_{p_id}.jpg"), crop)
                                self.extracted_ids.add(p_id_str)

                        # --- MÉTRICAS E DESENHO ---
                        x1, y1, x2, y2 = map(int, box)
                        pos_m = self.analyst.pixel_to_meters((x1+x2)/2, (y1+y2)/2)
                        self.tracker.calculate_speed(f"{prefix}_{p_id}", pos_m, self.sample_rate)

                        if video_writer:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

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
