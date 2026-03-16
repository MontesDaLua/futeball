"""
main script for football video analyser
"""
import argparse
import os
import sys
from pathlib import Path
import yaml
import cv2
from modules.match_analyzer import MatchAnalyzer
from modules.report_generator import ReportGenerator

def validate_output_path(output_arg):
    """
    Validate output as a sub directory from current dir
    """
    # Converte para um objeto Path
    output_path = Path(output_arg)

    # Extrai o diretório (ex: de 'reports/final.pdf' extrai 'reports')
    output_dir = output_path.parent

    # Se o output for apenas 'relatorio.pdf', o parent será '.' (raiz)
    # Se houver uma subdiretoria, verificamos se ela existe
    if not output_dir.exists():
        print(f"❌ Erro: A diretoria '{output_dir}' não existe a partir da raiz.")
        print("💡 Dica: Cria a pasta primeiro ou verifica o caminho.")
        sys.exit(1)

    # Verifica se temos permissão de escrita
    if not os.access(output_dir, os.W_OK):
        print(f"❌ Erro: Não tens permissão para escrever na pasta '{output_dir}'.")
        sys.exit(1)

    # Verifica se a extensão é .pdf (boa prática já que o parser diz 'PDF final')
    if output_path.suffix.lower() != '.pdf':
        print("⚠️ Aviso: O ficheiro de output não tem extensão .pdf.")

def validate_yaml(config_path):
    """
    validate if its an yaml file
    """
    path = Path(config_path)

    # 1. Verifica se o ficheiro existe (já tinhas esta ideia)
    if not path.exists():
        print(f"❌ Erro: Ficheiro de configuração '{config_path}' não encontrado.")
        sys.exit(1)

    # 2. Tenta carregar o conteúdo
    try:
        with open(path, 'r', encoding="utf-8") as f:
            # safe_load evita a execução de código arbitrário dentro do YAML
            data = yaml.safe_load(f)

        # 3. Verifica se o YAML não está vazio
        if data is None:
            print(f"⚠️ Erro: O ficheiro '{config_path}' está vazio.")
            sys.exit(1)

        return data # Retorna os dados para usares no MatchAnalyzer

    except yaml.YAMLError as e:
        print(f"❌ Erro de sintaxe no YAML ({config_path}):")
        # O erro do PyYAML costuma indicar a linha e coluna exata
        print(f"Detalhes: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao ler o YAML: {e}")
        sys.exit(1)

def validate_video(video_path):
    """
    Validate valid video file
    """
    path = Path(video_path)

    # 1. Verificação básica de existência
    if not path.exists():
        print(f"❌ Erro: O ficheiro '{video_path}' não existe.")
        sys.exit(1)

    # 2. Tentar abrir o stream de vídeo
    # O OpenCV retornará isOpened() = False se o codec não for suportado ou o
    #     ficheiro estiver corrompido
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        print(f"❌ Erro: '{video_path}' não é um ficheiro de vídeo válido ou o codec não é suportado.")
        cap.release()
        sys.exit(1)

    # 3. Validar se tem conteúdo (Frames e Duração)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if frame_count <= 0 or width <= 0 or height <= 0:
        print(f"❌ Erro: O vídeo '{video_path}' parece estar vazio ou tem dimensões inválidas.")
        cap.release()
        sys.exit(1)

    # 4. Tentar ler o primeiro frame (Garante que o codec de vídeo funciona)
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"❌ Erro: Não foi possível descodificar o primeiro frame de '{video_path}'.")
        cap.release()
        sys.exit(1)

    print(f"✅ Vídeo validado: {width}x{height} | {fps:.2f} FPS | {frame_count} frames.")

    cap.release()
    return True

def parse_arguments():
    """
    return cli arguments
    """
    parser = argparse.ArgumentParser(description="Football Performance AI ")
    parser.add_argument("--video", type=str, required=True, help="Caminho para o ficheiro de vídeo")
    parser.add_argument("--config", type=str, required=True, help="Caminho para o YAML")
    parser.add_argument("--output", type=str, required=True, help="Nome do PDF final")
    args = parser.parse_args()

    # Validate conditions
    ## Paths
    if not os.path.exists(args.video):
        print(f"Erro: O vídeo '{args.video}' não foi encontrado.")
        sys.exit(0)

    if not os.path.exists(args.config):
        print(f"Erro: O ficheiro de configuração '{args.config}' não existe.")
        sys.exit(0)
    # Validação de saída
    validate_output_path(args.output)

    print(f"✅ Tudo pronto! O relatório será guardado em: {args.output}")
    return ( args.video, args.config, args.output)

def process(video, config, output):
    """
    actual p+rocessing
    """
    # 1. Análise
    analyzer = MatchAnalyzer(config_data)
    analyzer.process_video(video)
    analyzer.save_session("session_data.json")

    # 2. Relatório
    reporter = ReportGenerator(
        analyzer.tracker.player_data,
        analyzer.config['squad'],
        analyzer.config['match_info']
    )
    reporter.generate_pdf(output)

    print(f"Sucesso! Relatório gerado em: {output}")

def main():
    """
    main script
    """
    ( video, config, output) = parse_arguments()
    ## file type
    config_data = validate_yaml(config)
    validate_video(video)
    #process(video, config, output)


if __name__ == "__main__":
    main()
