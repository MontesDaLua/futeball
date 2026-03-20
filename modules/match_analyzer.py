"""
Class match analyser
"""
import os
import json
import numpy as np
import cv2
import yaml
import time
from datetime import datetime
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
        # Carregamento seguro dos ficheiros YAML
        with open(proc_config_path, 'r', encoding="utf-8") as f:
            self.proc_config = yaml.safe_load(f) or {}
        with open(game_data_path, 'r', encoding="utf-8") as f:
            self.game_data = yaml.safe_load(f) or {}

        # Inicialização do Campo e Tracker
        pitch = self.game_data.get('pitch', {})
        self.analyst = FieldAnalyst(pitch.get('length', 105), pitch.get('width', 68))

        analysis_cfg = self.proc_config.get('analysis', {})
        self.tracker = PlayerTracker(
            analysis_cfg.get('model_size', 'yolov8n'),
            analysis_cfg.get('min_confidence', 0.3),
            device=analysis_cfg.get('device', 'cpu')
        )

        self.sample_rate = analysis_cfg.get('sample_rate', 0.1)
        self.extracted_ids = set()
        self.target_classes = [0, 32] # Person e Ball

        # 1. Mapeamento de IDs (Unificação / same_as)
        self.id_translation = {}
        same_as = self.game_data.get('same_as', {})
        for master_id, aliases in same_as.items():
            for alias in aliases:
                self.id_translation[str(alias)] = str(master_id)

        # 2. Lista de Exclusão (ignore_ids)
        self.ignore_ids = [str(i) for i in self.game_data.get('ignore_ids', [])]

    def process_video(self, video_path, save_annotated_path=None, gallery_dir=None):
        """
        Processamento integral: Tracking, Unificação, Galeria com Boxes e Relatório.
        """
        import os
        import time
        from datetime import datetime
        import cv2
        from tqdm import tqdm

        # --- 1. INICIALIZAÇÃO E MÉTRICAS ---
        start_ts = datetime.now()
        start_perf = time.perf_counter()

        cap = cv2.VideoCapture(video_path)
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(fps_video * self.sample_rate))
        w, h = int(cap.get(3)), int(cap.get(4))

        video_writer = None
        if save_annotated_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(save_annotated_path, fourcc, fps_video, (w, h))

        if gallery_dir:
            os.makedirs(gallery_dir, exist_ok=True)

        squad = self.game_data.get('squad', {})
        identified_ids_in_yaml = [str(k) for k in squad.keys() if k != 'referee_id']
        ref_id = str(squad.get('referee_id', ''))

        frames_analyzed = 0
        found_during_analysis = set()

        # --- 2. LOOP DE FRAMES ---
        for frame_idx in tqdm(range(total_frames), desc="Processamento"):
            ret, frame = cap.read()
            if not ret: break

            if frame_idx % frame_interval == 0:
                frames_analyzed += 1
                results = self.tracker.track_frame(frame)

                if results.boxes.id is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    ids = results.boxes.id.cpu().numpy().astype(int)
                    clss = results.boxes.cls.cpu().numpy().astype(int)

                    for box, p_id, cls in zip(boxes, ids, clss):
                        # A. UNIFICAÇÃO E FILTROS
                        raw_id_str = str(p_id)
                        p_id_str = self.id_translation.get(raw_id_str, raw_id_str)

                        if p_id_str in self.ignore_ids:
                            continue

                        is_ball = (cls == 32)
                        is_ref = (p_id_str == ref_id)
                        is_identified = (p_id_str in identified_ids_in_yaml or is_ref)

                        if not is_ball:
                            found_during_analysis.add(p_id_str)

                        # B. DEFINIÇÃO VISUAL (Cores)
                        color = (0, 0, 255) if is_ball else ((255, 255, 0) if is_ref else (0, 255, 0))
                        label = "BOLA" if is_ball else (f"REF:{p_id_str}" if is_ref else f"ID:{p_id_str}")

                        # C. LÓGICA DA GALERIA (Com Anotações Específicas)
                        if (gallery_dir and cls == 0 and not is_ref and
                            not is_identified and p_id_str not in self.extracted_ids):

                            x1, y1, x2, y2 = map(int, box)

                            # Criamos uma cópia temporária para anotar APENAS este jogador
                            temp_gallery_frame = frame.copy()

                            # Desenhar a box e o ID na cópia da galeria
                            cv2.rectangle(temp_gallery_frame, (x1, y1), (x2, y2), (0, 255, 255), 3) # Amarelo para destaque
                            cv2.putText(temp_gallery_frame, f"IDENTIFICAR: {p_id_str}", (x1, y1-15),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                            # Gerar Crop a partir da imagem anotada
                            crop = temp_gallery_frame[max(0, y1-30):min(h, y2+30), max(0, x1-30):min(w, x2+30)]

                            if crop.size > 0:
                                cv2.imwrite(os.path.join(gallery_dir, f"unidentified_{p_id_str}_crop.jpg"), crop)
                                cv2.imwrite(os.path.join(gallery_dir, f"unidentified_{p_id_str}_full.jpg"), temp_gallery_frame)
                                self.extracted_ids.add(p_id_str)

                        # D. MÉTRICAS E VÍDEO FINAL
                        pos_m = self.analyst.pixel_to_meters((box[0]+box[2])/2, (box[1]+box[3])/2)
                        prefix = "ball" if is_ball else ("referee" if is_ref else "player")
                        self.tracker.calculate_speed(f"{prefix}_{p_id_str}", pos_m, self.sample_rate)

                        if video_writer:
                            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 2)
                            cv2.putText(frame, label, (int(box[0]), int(box[1])-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if video_writer:
                video_writer.write(frame)

        cap.release()
        if video_writer: video_writer.release()

        # --- 3. RELATÓRIO FINAL ---
        end_ts = datetime.now()
        duration = time.perf_counter() - start_perf
        aps = frames_analyzed / duration if duration > 0 else 0

        identificados = sorted([fid for fid in found_during_analysis if fid in identified_ids_in_yaml or fid == ref_id], key=lambda x: int(x) if x.isdigit() else 0)
        nao_identificados = sorted([fid for fid in found_during_analysis if fid not in identificados], key=lambda x: int(x) if x.isdigit() else 0)

        print(f"\n" + "="*55)
        print(f"📋 RELATÓRIO TÉCNICO")
        print(f"="*55)
        print(f"⏱️ PERFORMANCE: {duration:.2f}s ({aps:.2f} análises/seg)")
        print(f"📂 GALERIA: {gallery_dir if gallery_dir else 'Desativada'}")
        print(f"-"*55)
        print(f"✅ IDENTIFICADOS ({len(identificados)}):")
        for i in identificados:
            print(f"   - ID {i}: {squad.get(i, 'Árbitro')}")
        print(f"❓ NÃO IDENTIFICADOS ({len(nao_identificados)}): {', '.join(nao_identificados)}")
        print("="*55 + "\n")
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
