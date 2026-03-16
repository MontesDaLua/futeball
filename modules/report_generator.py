"""
Class ReportGenerator
"""
import os
import shutil
import matplotlib.pyplot as plt
from fpdf import FPDF

class ReportGenerator:
    """
    Report Generator com gestão de ficheiros temporários
    """
    def __init__(self, player_data, squad_map, match_info):
        """
        Constructor
        """
        self.data = player_data
        self.squad = squad_map
        self.info = match_info
        # Define o nome da pasta temporária
        self.temp_dir = "temp_plots"

    def create_speed_plot(self, player_id, output_path):
        """
        Gera o gráfico de velocidade para um atleta específico.
        """
        p_id_str = str(player_id)

        # Verifica se o ID existe e se tem dados de velocidade
        if p_id_str not in self.data or not self.data[p_id_str].get("speeds"):
            return False

        speeds = self.data[p_id_str]["speeds"]

        plt.figure(figsize=(10, 4))
        plt.plot(speeds, color='#007AFF', linewidth=2)

        player_name = self.squad.get(p_id_str, f"Jogador {p_id_str}")
        plt.title(f"Perfil de Intensidade - {player_name}")
        plt.ylabel("Velocidade (km/h)")
        plt.xlabel("Amostras (Frames)")
        plt.grid(True, alpha=0.3, linestyle='--')

        # Garante que a pasta existe antes de salvar
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        plt.savefig(output_path, bbox_inches='tight')
        plt.close() # Liberta memória do Matplotlib
        return True

    def generate_pdf(self, output_filename):
        """
        Gera o PDF final e limpa a diretoria temporária.
        """
        # 1. Criar pasta temporária se não existir
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        pdf = FPDF()
        pdf.add_page()

        # Cabeçalho
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Relatório de Performance: {self.info['teams']}", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Estádio: {self.info['stadium']} | ID: {self.info['match_id']}", ln=True)

        try:
            for p_id, metrics in self.data.items():
                p_id_str = str(p_id)
                name = self.squad.get(p_id_str, f"Jogador {p_id_str}")
                speeds = metrics.get("speeds", [])

                v_max = max(speeds) if speeds else 0
                v_med = sum(speeds) / len(speeds) if speeds else 0
                sprints = len([s for s in speeds if s > 25.2])

                # Layout do Atleta
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"Atleta: {name}", ln=True)

                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 7, f"Velocidade Máxima: {v_max:.2f} km/h", ln=True)
                pdf.cell(0, 7, f"Velocidade Média: {v_med:.2f} km/h", ln=True)
                pdf.cell(0, 7, f"Sprints (>25.2 km/h): {sprints}", ln=True)

                # Gerar imagem na pasta temporária
                img_name = f"speed_plot_{p_id_str}.png"
                img_path = os.path.join(self.temp_dir, img_name)

                if self.create_speed_plot(p_id_str, img_path):
                    # Insere imagem no PDF
                    pdf.image(img_path, x=15, w=170)
                else:
                    pdf.set_font("Arial", 'I', 8)
                    pdf.cell(0, 5, "Gráfico indisponível (dados insuficientes)", ln=True)

            # Salvar o PDF
            pdf.output(output_filename)
            print(f"✅ Relatório guardado com sucesso: {output_filename}")

        finally:
            # 2. Limpeza total da pasta temporária após o processamento
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Pasta temporária '{self.temp_dir}' removida.")
