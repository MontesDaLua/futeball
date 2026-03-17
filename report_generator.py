"""
Script: run_report_generator.py
Objetivo: Ler dados de tracking (JSON) e gerar relatório estatístico em PDF.
"""
import sys
import json
import yaml
import argparse
from pathlib import Path
from modules.report_generator import ReportGenerator

def load_config(config_path):
    """ Carrega o ficheiro de configuração YAML """
    try:
        with open(config_path, 'r', encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Erro ao ler configuração: {e}")
        sys.exit(1)

def load_session_data(json_path):
    """ Carrega os dados de tracking exportados pelo processador de vídeo """
    try:
        with open(json_path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler dados da sessão (JSON): {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Etapa 2: Geração de Relatórios Estatísticos")
    parser.add_argument("--input", type=str, required=True, help="Caminho do ficheiro JSON (session_data.json)")
    parser.add_argument("--config", type=str, required=True, help="Caminho do ficheiro .yaml")
    parser.add_argument("--output", type=str, default="relatorio_performance.pdf", help="Nome do PDF de saída")

    args = parser.parse_args()

    # 1. Carregar recursos necessários
    print(f"📂 A carregar dados de: {args.input}")
    config = load_config(args.config)
    player_data = load_session_data(args.input)

    # 2. Inicializar o Gerador de Relatórios
    # Passamos os dados de tracking, o mapeamento de nomes (squad) e info do jogo
    reporter = ReportGenerator(
        player_data=player_data,
        squad_map=config.get('squad', {}),
        match_info=config.get('match_info', {})
    )

    print(f"📊 A gerar gráficos e métricas para {len(player_data)} jogadores...")

    # 3. Criar o PDF final
    # Internamente, a classe cria plots temporários e limpa-os no fim
    try:
        reporter.generate_pdf(args.output)
        print(f"\n✅ Relatório gerado com sucesso: {args.output}")
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
