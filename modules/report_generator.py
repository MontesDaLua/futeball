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

    def create_displacement_plot_old(self, p_id, name):
        """
        Gera o mapa de trajeto/deslocamento linear do jogador.
        Usa as coordenadas reais [x, y] em metros para desenhar as linhas de movimento.
        """
        data = self.player_data.get(str(p_id))
        if not data or not data['positions']:
            return None

        # Converter lista de posições para array numpy para facilitar a indexação
        pos = np.array(data['positions'])
        x = pos[:, 0]
        y = pos[:, 1]

        fig, ax = plt.subplots(figsize=(10, 7))

        # Desenho das marcações do campo (assumindo padrão 105x68m)
        # Borda externa
        ax.plot([0, 105, 105, 0, 0], [0, 0, 68, 68, 0], color="green", linewidth=2)
        # Linha de meio campo
        ax.plot([52.5, 52.5], [0, 68], color="green", linestyle='--', alpha=0.5)

        # Desenhar a linha de deslocamento (A trajetória propriamente dita)
        ax.plot(x, y, color='blue', label='Trajeto Percorrido', linewidth=1, alpha=0.8)

        # Marcar o ponto de Início (Verde) e o ponto de Fim (Vermelho)
        if len(x) > 0:
            # Ponto inicial
            ax.scatter(x[0], y[0], color='lime', s=100, label='Início', edgecolors='black', zorder=5)
            # Ponto final
            ax.scatter(x[-1], y[-1], color='red', s=100, label='Fim', edgecolors='black', zorder=5)

        # Configurações estéticas do gráfico
        ax.set_title(f"Mapa de Deslocamento Real (Metros) - {name}")
        ax.set_xlabel("Comprimento (m)")
        ax.set_ylabel("Largura (m)")
        ax.legend(loc='upper right')

        # Garante que 1 metro no eixo X é igual a 1 metro no eixo Y (evita distorção do campo)
        ax.set_aspect('equal')

        # Inverter o eixo Y para que a origem (0,0) coincida com o topo esquerdo da câmara
        ax.invert_yaxis()

        # Guardar o gráfico temporariamente
        path = os.path.join(self.output_dir, f"disp_{p_id}.png")
        plt.savefig(path)
        plt.close()
        return path


    def create_displacement_plot(self, p_id, name):
        """
        Gera o mapa de trajeto/deslocamento linear do jogador dentro de um campo.
        Usa as coordenadas reais [x, y] em metros.
        """
        data = self.player_data.get(str(p_id))
        if not data or not data['positions']:
            return None

        pos = np.array(data['positions'])
        x = pos[:, 0]
        y = pos[:, 1]

        # Dimensões padrão FIFA (ajustar se o seu campo for diferente)
        l_campo = 105.0
        w_campo = 68.0

        fig, ax = plt.subplots(figsize=(10, 7))

        # --- DESENHO DO CAMPO (COORDENADAS REAIS EM METROS) ---
        # 1. Relvado e Linhas de Fundo
        ax.plot([0, l_campo, l_campo, 0, 0], [0, 0, w_campo, w_campo, 0], color="black", linewidth=2)

        # 2. Linha de Meio Campo e Círculo Central
        ax.plot([l_campo/2, l_campo/2], [0, w_campo], color="black", linewidth=2)
        centro = plt.Circle((l_campo/2, w_campo/2), 9.15, color="black", fill=False, linewidth=2)
        ax.add_artist(centro)

        # 3. Áreas de Grande Penalidade (Esquerda e Direita)
        # Área Grande (16.5m)
        ax.plot([0, 16.5, 16.5, 0], [w_campo/2 - 20.15, w_campo/2 - 20.15, w_campo/2 + 20.15, w_campo/2 + 20.15], color="black", linewidth=2)
        ax.plot([l_campo, l_campo - 16.5, l_campo - 16.5, l_campo], [w_campo/2 - 20.15, w_campo/2 - 20.15, w_campo/2 + 20.15, w_campo/2 + 20.15], color="black", linewidth=2)

        # Pequena Área (5.5m)
        ax.plot([0, 5.5, 5.5, 0], [w_campo/2 - 9.16, w_campo/2 - 9.16, w_campo/2 + 9.16, w_campo/2 + 9.16], color="black", linewidth=2)
        ax.plot([l_campo, l_campo - 5.5, l_campo - 5.5, l_campo], [w_campo/2 - 9.16, w_campo/2 - 9.16, w_campo/2 + 9.16, w_campo/2 + 9.16], color="black", linewidth=2)

        # --- DESENHO DA TRAJETÓRIA DO JOGADOR ---
        ax.plot(x, y, color='blue', label='Trajeto', linewidth=1.5, alpha=0.8, zorder=4)

        # Marcar Início (Verde) e Fim (Vermelho)
        if len(x) > 0:
            ax.scatter(x[0], y[0], color='lime', s=80, label='Início', edgecolors='black', zorder=5)
            ax.scatter(x[-1], y[-1], color='red', s=80, label='Fim', edgecolors='black', zorder=5)

        # Configurações do Gráfico
        ax.set_title(f"Mapa de Deslocamento Tático - {name}")
        ax.set_xlim(-5, l_campo + 5)
        ax.set_ylim(-5, w_campo + 5)
        ax.set_aspect('equal')
        ax.invert_yaxis() # Mantém a orientação da câmara (0,0 no topo)
        ax.axis('off') # Remove os eixos numéricos para parecer um relatório tático

        path = os.path.join(self.output_dir, f"disp_{p_id}.png")
        plt.savefig(path, bbox_inches='tight', pad_inches=0.1)
        plt.close()
        return path



    def generate_pdf(self, output_pdf_path):
        """
        Compila todas as métricas e gráficos (Velocidade, Heatmap e Deslocamento)
        num relatório PDF final, com uma página por jogador.
        """
        with PdfPages(output_pdf_path) as pdf:
            # Iterar por cada jogador encontrado nos dados
            for p_id in self.player_data.keys():
                name = self._get_player_name(p_id)
                metrics = self.calculate_metrics(p_id)

                # Se não houver dados suficientes para calcular métricas, salta o jogador
                if not metrics:
                    continue

                # Criar uma figura do tamanho de uma folha A4 (polegadas)
                fig = plt.figure(figsize=(8.27, 11.69))
                plt.clf()

                # 1. Título do Relatório
                plt.suptitle(f"Relatório de Performance: {name} (ID: {p_id})",
                             fontsize=16, weight='bold', y=0.95)

                # 2. Bloco de Texto com Métricas Resumo
                info_text = (
                    f"Distância Total Percorrida: {metrics['distance']:.2f} metros\n"
                    f"Velocidade Média: {metrics['avg_speed']:.2f} km/h\n"
                    f"Velocidade Máxima: {metrics['max_speed']:.2f} km/h\n"
                    f"Número de Sprints (>20km/h): {metrics['sprints']}"
                )
                plt.figtext(0.15, 0.82, info_text, fontsize=11,
                            bbox={'facecolor': 'orange', 'alpha': 0.1, 'pad': 10})

                # 3. Adicionar Gráfico de Velocidade (Topo)
                speed_img_path = self.create_speed_plot(p_id, name)
                ax_speed = fig.add_axes([0.1, 0.58, 0.8, 0.22]) # [left, bottom, width, height]
                img_s = plt.imread(speed_img_path)
                ax_speed.imshow(img_s)
                ax_speed.axis('off')
                ax_speed.set_title("Evolução da Velocidade", fontsize=10, loc='left')

                # 4. Adicionar Heatmap (Meio)
                heat_img_path = self.create_heatmap(p_id, name)
                if heat_img_path:
                    ax_heat = fig.add_axes([0.1, 0.31, 0.8, 0.25])
                    img_h = plt.imread(heat_img_path)
                    ax_heat.imshow(img_h)
                    ax_heat.axis('off')
                    ax_heat.set_title("Mapa de Calor (Ocupação)", fontsize=10, loc='left')

                # 5. Adicionar Mapa de Deslocamento (Fundo)
                disp_img_path = self.create_displacement_plot(p_id, name)
                if disp_img_path:
                    ax_disp = fig.add_axes([0.1, 0.04, 0.8, 0.25])
                    img_d = plt.imread(disp_img_path)
                    ax_disp.imshow(img_d)
                    ax_disp.axis('off')
                    ax_disp.set_title("Trajetória Real de Deslocamento", fontsize=10, loc='left')

                # Guardar a página atual no PDF
                pdf.savefig(fig)
                plt.close(fig)

        print(f"📄 Relatório PDF consolidado gerado em: {output_pdf_path}")

    def generate_pdf_old(self, output_filename):
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
