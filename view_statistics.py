"""
Módulo ViewStatistics: Analisador de métricas de tracking de futebol.
Exibe estatísticas ordenadas por volume de frames analisadas (Ordem Descendente).
"""

import json
import argparse
import os
import sys
import yaml
import numpy as np


def load_data(json_path, yaml_path):
    """
    Carrega os ficheiros JSON e YAML necessários.
    """
    if not os.path.exists(json_path) or not os.path.exists(yaml_path):
        print("❌ ERRO: Ficheiros JSON ou YAML não encontrados.")
        sys.exit(1)

    with open(json_path, 'r', encoding="utf-8") as file_handle:
        player_data = json.load(file_handle)

    with open(yaml_path, 'r', encoding="utf-8") as file_handle:
        game_data = yaml.safe_load(file_handle)
        squad_map = game_data.get('squad', {})

    return player_data, squad_map


def calculate_player_stats(data, sample_rate):
    """
    Calcula as métricas de um jogador, incluindo a contagem de frames.
    """
    positions = data.get('positions', [])
    speeds = data.get('speeds', [])

    if not positions:
        return None

    frames_count = len(positions)
    total_time = frames_count * sample_rate

    # Distância Total
    total_distance = 0.0
    if len(positions) > 1:
        pos_array = np.array(positions)
        diffs = np.diff(pos_array, axis=0)
        total_distance = float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))

    # Velocidade Máxima
    max_v = float(np.max(speeds)) if speeds else 0.0

    return {
        "frames": frames_count,
        "time": total_time,
        "dist": total_distance,
        "v_max": max_v
    }


def main():
    """
    Lê os dados e imprime a tabela ordenada por frames (Descendente).
    """
    parser = argparse.ArgumentParser(description="Estatísticas Ordenadas por Frames")
    parser.add_argument("--json", type=str, required=True, help="JSON de entrada")
    parser.add_argument("--game_data", type=str, required=True, help="YAML de entrada")
    parser.add_argument("--rate", type=float, required=True, help="Sample rate (ex: 0.5)")

    args = parser.parse_args()

    # 1. Carregar dados
    p_data, s_map = load_data(args.json, args.game_data)

    # 2. Processar e calcular métricas para todos os jogadores
    results_list = []
    for p_id, content in p_data.items():
        stats = calculate_player_stats(content, args.rate)
        if stats:
            # Associar nome e ID aos resultados para a tabela
            nome = s_map.get(str(p_id)) or s_map.get(int(p_id)) or f"ID {p_id}"
            stats['id'] = p_id
            stats['nome'] = nome
            results_list.append(stats)

    # 3. ORDENAÇÃO: Sort pelo número de frames em ordem descendente
    # reverse=True garante que o maior número de frames aparece primeiro
    results_list.sort(key=lambda x: x['frames'], reverse=True)

    # 4. Impressão da Tabela
    width = 90
    print("\n" + "=" * width)
    print(f"{'RANKING POR PARTICIPAÇÃO (FRAMES ANALISADAS)':^90}")
    print("=" * width)
    header = (f"{'ID':<6} | {'JOGADOR':<20} | {'FRAMES':<10} | "
              f"{'TEMPO(s)':<10} | {'DIST(m)':<12} | {'V.MÁX':<8}")
    print(header)
    print("-" * width)

    for item in results_list:
        row = (f"{item['id']:<6} | "
               f"{str(item['nome'])[:20]:<20} | "
               f"{item['frames']:<10} | "
               f"{item['time']:>10.1f} | "
               f"{item['dist']:>12.2f} | "
               f"{item['v_max']:>8.1f}")
        print(row)

    print("=" * width)
    print(f"Critério: Ordem Descendente por Frames | Total de Jogadores: {len(results_list)}")
    print("=" * width + "\n")


if __name__ == "__main__":
    main()
