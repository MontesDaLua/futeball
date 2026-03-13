# 20260312-1617
  ```
    ## Contexto
    Gera um sistema de análise de performance de futebol profissional em Python, utilizando Programação Orientada a Objetos (OOP), desenhado para correr localmente num Mac M1 com aceleração Metal (MPS).

    ## 1. Estrutura de Configuração (YAML)
    O sistema deve ler um ficheiro `config_jogo.yaml` que contém:
    - `match_info`: ID do jogo, equipas e estádio.
    - `pitch`: Comprimento e largura em metros.
    - `analysis`: `sample_rate` (ex: 0.2 para 5fps), `min_confidence` e `model_size`.
    - `squad`: Dicionário {ID_Tracker: "Nome do Jogador"}.

    ## 2. Requisitos das Classes (OOP)
    - **Class `FieldAnalyst`**:
        - Realizar calibração automática via Homografia (OpenCV) detetando as linhas do campo.
        - Método `pixel_to_meters(x, y)` para converter coordenadas da imagem em metros.
    - **Class `PlayerTracker`**:
        - Inicializar o modelo YOLOv8 forçando o dispositivo `mps` (Apple Silicon).
        - Utilizar `model.track(persist=True)` para rastreio.
        - Calcular velocidade em km/h com filtro de mediana para remover ruído.
    - **Class `MatchAnalyzer`**:
        - Gerir o loop de vídeo processando frames conforme o `sample_rate`.
        - Implementar `save_session()` e `load_session()` em JSON para persistência de dados.
    - **Class `ReportGenerator`**:
        - Gerar gráficos de intensidade (Velocidade vs Tempo) com Matplotlib.
        - Criar um relatório PDF profissional usando a biblioteca `fpdf2`, incluindo tabelas de métricas (Vmax, Vmed, contagem de Sprints) e o gráfico gerado.

    ## 3. Requisitos Técnicos e Otimização
    - Utilizar `tqdm` para exibir uma barra de progresso no terminal.
    - O código deve ser "Headless" por defeito (sem `cv2.imshow`) para maximizar a velocidade no M1.
    - Implementar tratamento de erros para vídeos corrompidos ou falhas de calibração.

    ## 4. Ficheiro de Dependências
    Gera um ficheiro `requirements.txt` que inclua: ultralytics, opencv-python, pyyaml, matplotlib, numpy, fpdf2, tqdm e pandas.
    isola as classes num ficheiro separado 
  ```
# 20260313-13032026
  ```
    gera uma Makefile para python para:
    * criar o ambiente virtual
    * instalar os pacotes de pip
    * limpar o ambiente virtual

    não cries a opção help
    responde em ingles
  ```
