"""
Class ReportGenerator
"""
import matplotlib.pyplot as plt
from fpdf import FPDF

class ReportGenerator:
    """
    Report Generator
    """
    def __init__(self, player_data, squad_map, match_info):
        """
        Constructor
        """
        self.data = player_data
        self.squad = squad_map
        self.info = match_info

    def create_speed_plot_old(self, player_id, output_path):
        """
        Plot speed - player_id já deve vir como string do loop principal
        """
        if player_id not in self.data:
            return False
        speeds = self.data[player_id]["speeds"]
        plt.figure(figsize=(10, 4))
        plt.plot(speeds, color='#007AFF')
        plt.title(f"Perfil de Intensidade - {self.squad.get(str(player_id), 'Unknown')}")
        plt.ylabel("Velocidade (km/h)")
        plt.xlabel("Amostras")
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path)
        plt.close()

    def generate_pdf_old(self, output_filename):
        """
        Generate pdf file
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Relatório de Performance: {self.info['teams']}", ln=True, align='C')

        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Estádio: {self.info['stadium']} | ID: {self.info['match_id']}", ln=True)

        for p_id, metrics in self.data.items():
            name = self.squad.get(p_id, f"Jogador {p_id}")
            v_max = max(metrics["speeds"]) if metrics["speeds"] else 0
            v_med = sum(metrics["speeds"]) / len(metrics["speeds"]) if metrics["speeds"] else 0
            sprints = len([s for s in metrics["speeds"] if s > 25.2]) # Threshold sprint FIFA

            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"Atleta: {name}", ln=True)

            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, f"Velocidade Máxima: {v_max:.2f}km/h", ln=True)
            pdf.cell(0, 7, f"Velocidade Média: {v_med:.2f}km/h", ln=True)
            pdf.cell(0, 7, f"Sprints (>25.2 km/h): {sprints}", ln=True)

            plot_path = f"speed_{p_id}.png"
            self.create_speed_plot(p_id, plot_path)
            pdf.image(plot_path, x=10, w=180)

        pdf.output(output_filename)

    def create_speed_plot(self, player_id, output_path):
        """
        Gera um gráfico da evolução da velocidade de um atleta.
        """
        # Garante que o ID é tratado como string para corresponder às chaves do dicionário
        p_id_str = str(player_id)

        # 1. Verificação de segurança: O ID existe nos dados?
        if p_id_str not in self.data:
            print(f"⚠️ Aviso: Sem dados para o ID {p_id_str} no dicionário.")
            return False

        # 2. Verificação de conteúdo: Existem velocidades registadas?
        speeds = self.data[p_id_str].get("speeds", [])
        if not speeds:
            print(f"⚠️ Aviso: Lista de velocidades vazia para o jogador {p_id_str}.")
            return False

        # 3. Configuração do gráfico
        plt.figure(figsize=(10, 4))
        plt.plot(speeds, color='#007AFF', linewidth=2, label='Velocidade')

        # Tenta obter o nome do jogador do squad_map, caso contrário usa "Unknown"
        player_name = self.squad.get(p_id_str, "Unknown")
        plt.title(f"Perfil de Intensidade - {player_name}")

        plt.ylabel("Velocidade (km/h)")
        plt.xlabel("Amostras (Frames analisadas)")
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend()

        # 4. Gravação e fecho do buffer para libertar memória
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return True

    def generate_pdf(self, output_filename):
        """
        Gera o ficheiro PDF final com métricas e gráficos de performance.
        """
        pdf = FPDF()
        pdf.add_page()

        # Cabeçalho do Relatório
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Relatório de Performance: {self.info['teams']}", ln=True, align='C')

        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Estádio: {self.info['stadium']} | ID: {self.info['match_id']}", ln=True)
        pdf.ln(5)

        # Iteração sobre cada jogador no dicionário de dados
        for p_id, metrics in self.data.items():
            # p_id já é tratado como string para garantir compatibilidade
            name = self.squad.get(str(p_id), f"Jogador {p_id}")
            speeds = metrics.get("speeds", [])

            # Cálculos de Performance
            v_max = max(speeds) if speeds else 0
            v_med = sum(speeds) / len(speeds) if speeds else 0
            sprints = len([s for s in speeds if s > 25.2]) # Limiar de sprint FIFA

            # Secção do Atleta
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, f"Atleta: {name}", ln=True, fill=True)

            # Métricas em Texto
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, f"Velocidade Máxima: {v_max:.2f} km/h", ln=True)
            pdf.cell(0, 7, f"Velocidade Média: {v_med:.2f} km/h", ln=True)
            pdf.cell(0, 7, f"Sprints (>25.2 km/h): {sprints}", ln=True)

            # Inserção do Gráfico com Verificação de Segurança
            plot_path = f"speed_{p_id}.png"

            # create_speed_plot retorna True se gravou a imagem, False se não havia dados
            if self.create_speed_plot(p_id, plot_path):
                pdf.ln(2)
                # Insere a imagem apenas se o ficheiro existir
                pdf.image(plot_path, x=15, w=170)
                pdf.ln(5)
            else:
                # Caso não existam dados para o gráfico, insere um aviso no PDF
                pdf.set_font("Arial", 'I', 9)
                pdf.set_text_color(150, 0, 0)
                pdf.cell(0, 10, " > Gráfico de intensidade não disponível (dados insuficientes).", ln=True)
                pdf.set_text_color(0, 0, 0) # Reseta a cor para o próximo jogador

        # Gravação do Ficheiro
        pdf.output(output_filename)
