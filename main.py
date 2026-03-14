"""
main script for football video analyser
"""
import argparse
from modules.match_analyzer import MatchAnalyzer
from modules.report_generator import ReportGenerator

def main():
    """
    main script
    """
    parser = argparse.ArgumentParser(description="Football Performance AI ")
    parser.add_argument("--video", type=str, required=True, help="Caminho para o ficheiro de vídeo")
    parser.add_argument("--config", type=str, required=True, help="Caminho para o YAML")
    parser.add_argument("--output", type=str, required=True, help="Nome do PDF final")
    args = parser.parse_args()

    # 1. Análise
    analyzer = MatchAnalyzer(args.config)
    analyzer.process_video(args.video)
    analyzer.save_session("session_data.json")

    # 2. Relatório
    reporter = ReportGenerator(
        analyzer.tracker.player_data,
        analyzer.config['squad'],
        analyzer.config['match_info']
    )
    reporter.generate_pdf(args.output)

    print(f"Sucesso! Relatório gerado em: {args.output}")


if __name__ == "__main__":
    main()
