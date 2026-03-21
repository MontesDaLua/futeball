"""
Módulo ReportGenerator: Responsável por processar os dados brutos de tracking,
calcular estatísticas de performance e gerar um relatório PDF com gráficos.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

class ReportGenerator:
    """
    Gera relatórios estatísticos baseados nos dados de movimento dos jogadores.
    """
    def __init__(self, player_data, squad_map, match_info=None):
        """
        Args:
            player_data (dict): Dados vindos do JSON (posições e velocidades).
            squad_map (dict): Mapeamento de ID para Nome Real (vindo do YAML).
            match_info (dict): Metadados do jogo (data, equipas, etc).
        """
        self.player_data = player_data
        self.squad_map = squad_map
        self.match_info = match_info or {}
        self.output_dir = "temp_plots"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_player_name(self, p_id):
        """Retorna o nome real ou 'ID X' se não identificado."""
        return self.squad_map.get(str(p_id), f"Jogador {p_id}")

    def calculate_metrics(self, p_id):
        """Calcula métricas resumo para um jogador específico."""
        data = self.player_data.get(str(p_id), {})
        speeds = data.get("speeds", [])
        positions = np.array(data.get("positions", []))

        if not speeds:
            return None

        # Cálculo de distância total (soma das distâncias entre posições consecutivas)
        dist_total = 0
        if len(positions) > 1:
            diffs = np.diff(positions, axis=0)
            dist_total = np.sum(np.sqrt(np.sum(diffs**2, axis=1)))

        metrics = {
            "avg_speed": np.mean(speeds),
            "max_speed": np.max(speeds),
            "distance": dist_total,
            "sprints": len([s for s in speeds if s > 25.2]) # Sprints > 25.2 km/h
        }
        return metrics

    def create_speed_plot(self, p_id, name):
        """Gera um gráfico de linha da velocidade ao longo do tempo."""
        speeds = self.player_data[str(p_id)]["speeds"]
        plt.figure(figsize=(8, 4))
        plt.plot(speeds, color='blue', linewidth=1, label='Velocidade (km/h)')
        plt.axhline(y=np.mean(speeds), color='red', linestyle='--', label='Média')
        plt.title(f"Perfil de Velocidade: {name}")
        plt.xlabel("Amostras de Tempo")
        plt.ylabel("Km/h")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plot_path = os.path.join(self.output_dir, f"speed_{p_id}.png")
        plt.savefig(plot_path)
        plt.close()
        return plot_path

    def create_heatmap(self, p_id, name):
        """Gera um mapa de calor (Heatmap) da posição do jogador no campo."""
        positions = np.array(self.player_data[str(p_id)]["positions"])
        if len(positions) == 0: return None

        plt.figure(figsize=(10, 6))
        # Simulando o campo (105x68)
        plt.hexbin(positions[:, 0], positions[:, 1], gridsize=20, cmap='YlOrRd', extent=[0, 105, 0, 68])
        plt.colorbar(label='Densidade de Presença')
        plt.title(f"Mapa de Calor: {name}")
        plt.xlim(0, 105)
        plt.ylim(0, 68)

        # Desenho simplificado das linhas de campo
        plt.plot([0, 105, 105, 0, 0], [0, 0, 68, 68, 0], color="black") # Linhas laterais
        plt.plot([52.5, 52.5], [0, 68], color="black") # Meio campo

        plot_path = os.path.join(self.output_dir, f"heat_{p_id}.png")
        plt.savefig(plot_path)
        plt.close()
        return plot_path

    def generate_pdf(self, output_filename):
        """Compila todas as métricas e gráficos num ficheiro PDF único."""
        with PdfPages(output_filename) as pdf:
            # Página de Rosto
            plt.figure(figsize=(8.5, 11))
            plt.text(0.5, 0.9, "RELATÓRIO DE DESEMPENHO TÁTICO", fontsize=20, ha='center', weight='bold')
            plt.text(0.5, 0.85, f"Data do Processamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ha='center')
            plt.text(0.5, 0.7, f"Jogo: {self.match_info.get('teams', 'N/A')}", fontsize=14, ha='center')
            plt.axis('off')
            pdf.savefig()
            plt.close()

            # Processar cada jogador identificado no JSON
            for p_id in self.player_data.keys():
                name = self._get_player_name(p_id)
                metrics = self.calculate_metrics(p_id)

                if not metrics: continue

                # Página do Jogador
                fig = plt.figure(figsize=(8.5, 11))
                plt.suptitle(f"Análise Individual: {name} (ID {p_id})", fontsize=16, weight='bold')

                # Texto de Métricas
                info_text = (
                    f"Distância Total: {metrics['distance']:.2f} metros\n"
                    f"Velocidade Média: {metrics['avg_speed']:.2f} km/h\n"
                    f"Velocidade Máxima: {metrics['max_speed']:.2f} km/h\n"
                    f"Número de Sprints: {metrics['sprints']}"
                )
                plt.figtext(0.15, 0.8, info_text, fontsize=12, bbox={'facecolor': 'orange', 'alpha': 0.1, 'pad': 10})

                # Adicionar Gráfico de Velocidade
                speed_img = self.create_speed_plot(p_id, name)
                ax_speed = fig.add_axes([0.1, 0.45, 0.8, 0.3])
                img_s = plt.imread(speed_img)
                ax_speed.imshow(img_s)
                ax_speed.axis('off')

                # Adicionar Heatmap
                heat_img = self.create_heatmap(p_id, name)
                if heat_img:
                    ax_heat = fig.add_axes([0.1, 0.05, 0.8, 0.35])
                    img_h = plt.imread(heat_img)
                    ax_heat.imshow(img_h)
                    ax_heat.axis('off')

                pdf.savefig()
                plt.close()

        # Limpeza de ficheiros temporários
        for f in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, f))
        os.rmdir(self.output_dir)

        print(f"✅ Relatório PDF gerado com sucesso: {output_filename}")
