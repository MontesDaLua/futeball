import matplotlib.pyplot as plt
from fpdf import FPDF
import pandas as pd

class ReportGenerator:
    def __init__(self, player_data, squad_map, match_info):
        self.data = player_data
        self.squad = squad_map
        self.info = match_info

    def create_speed_plot(self, player_id, output_path):
        speeds = self.data[str(player_id)]["speeds"]
        plt.figure(figsize=(10, 4))
        plt.plot(speeds, color='#007AFF')
        plt.title(f"Perfil de Intensidade - {self.squad.get(str(player_id), 'Unknown')}")
        plt.ylabel("Velocidade (km/h)")
        plt.xlabel("Amostras")
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path)
        plt.close()

    def generate_pdf(self, output_filename):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Relatório de Performance: {self.info['teams']}", ln=True, align='C')

        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Estádio: {self.info['stadium']} | ID: {self.info['match_id']}", ln=True)

        for p_id, metrics in self.data.items():
            name = self.squad.get(str(p_id), f"Jogador {p_id}")
            v_max = max(metrics["speeds"]) if metrics["speeds"] else 0
            v_med = sum(metrics["speeds"]) / len(metrics["speeds"]) if metrics["speeds"] else 0
            sprints = len([s for s in metrics["speeds"] if s > 25.2]) # Threshold sprint FIFA

            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"Atleta: {name}", ln=True)

            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, f"Velocidade Máxima: {v_max:.2 km/h}", ln=True)
            pdf.cell(0, 7, f"Velocidade Média: {v_med:.2 km/h}", ln=True)
            pdf.cell(0, 7, f"Sprints (>25.2 km/h): {sprints}", ln=True)

            plot_path = f"speed_{p_id}.png"
            self.create_speed_plot(p_id, plot_path)
            pdf.image(plot_path, x=10, w=180)

        pdf.output(output_filename)
