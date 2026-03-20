"""
Script: run_video_processing.py
Objetivo: Processar vídeo de futebol e exportar coordenadas de tracking para JSON.
"""
import sys
import argparse
import os
from pathlib import Path
from modules.match_analyzer import MatchAnalyzer

def validate_inputs(video_path, proc_config, game_data):
    """ Validações básicas de existência de ficheiros """
    if not Path(video_path).exists():
        print(f"❌ Erro: Vídeo '{video_path}' não encontrado.")
        sys.exit(1)
    if not Path(proc_config).exists():
        print(f"❌ Erro: Configuração '{proc_config}' não encontrada.")
        sys.exit(1)
    if not Path(proc_config).exists():
        print(f"❌ Erro: Configuração '{game_data}' não encontrada.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Etapa 1: Processamento de Vídeo e Tracking")
    parser.add_argument("--video", type=str,
        required=True, help="Caminho do vídeo .mp4")
    # parser.add_argument("--config", type=str, required=True,
    #         help="Caminho do ficheiro .yaml")
    parser.add_argument("--output", type=str, required=True,
            help="Nome do ficheiro JSON de saída")
    parser.add_argument("--save-video", type=str, required=False,
        help="Nome do vídeo anotado (ex: output.mp4). Se omitido, não gera vídeo.")


    parser.add_argument("--proc_config", type=str, required=True,
        help="processor_config.yaml")
    parser.add_argument("--game_data", type=str, required=True,
        help="game_data.yaml")

    args = parser.parse_args()

    # 1. Validar Ficheiros
    validate_inputs(args.video, args.proc_config, args.game_data)

    print(f"🚀 A iniciar processamento: {args.video}")

    try:
        # 2. Inicializar o Analisador (usa FieldAnalyst e PlayerTracker internamente)
        #analyzer = MatchAnalyzer(args.config)
        analyzer = MatchAnalyzer(proc_config_path=args.proc_config,
                                 game_data_path=args.game_data)
        # 3. Executar a análise de frames
        #analyzer.process_video(args.video)
        analyzer.process_video(args.video,
            save_annotated_path=args.save_video)
        # 4. Guardar a sessão num ficheiro JSON
        # Este ficheiro será o input para o script de relatórios
        analyzer.save_session(args.output)

        print(f"\n✅ Processamento concluído com sucesso!")
        print(f"📂 Dados de tracking guardados em: {args.output}")

    except Exception as e:
        print(f"❌ Ocorreu um erro durante o processamento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
