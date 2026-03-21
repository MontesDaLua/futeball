* 20260312
  * initial skelton
* 20260313
  * Added Makefile and .gitignore
  * Added changelog
* 20260314
  * add
    * TODO
    * README.md
    * pylint to makefile
    * unittest to each method in each class
    * data
      * video
        * full video (SINT-ALV)
  * changed
    * global prompt
    * Makefile prompt
* 20260314-1
  * added
    * pylintrc
  * changed
    * ammend pylint errors
      * main.py
      * match_analyzer.py
      * report_generator.py
      * tests
        * test_field_analyst.py
        * test_match_analyzer.py
        * test_player_tracker.py
* 20260314-2
  * test if arguments are valid (yaml and video )

* 20260316
  * generate samples for demo purpose
  * first run with success

* 20260316-1
  * generate speed reports image in a temporary folder and remove the images after the report run

* 20260317-1
  * split the game analysis in 2 scripts
    * video processing
    * report generator

* 20260318-1
  * opção de gerar um video em formato mp4 com frames analisadas

* 20260319-1
  * split the config in 2 DISTINCT FILES \
    * game data
    * video processor parameters

* 20260319-2
  * video analysis
    * include ball position
    * include referee position
    * imagem de todos os ids de jogadores encontrados numa directoria especifica
    * lista de ids a ignorar na configuração de jogo
* 20260319-3
  * video analysis
    * possibilidade de considerar 2 ou mais ids como o mesmo
    * Numero de frames Totais
    * Numero de frames analisdas
    * timestampo inicio da analise
    * timestampo fim da analise
    * duração da analise
    * numero de analises por segundo
    * fim lista
      * os jogadores identificados
      * os jogadores nao identificados
    * na galeria das imagens dos jogadores nao identificados, por cada um inclui tambem a totalida da frame em que foi detectado

* 20260319-4
  # video_app
    gera uma aplicação iteractiva em python que :
      - permita a partir do video gerado , para cada id nao identificado atribuir um nome.
      - deve ler os argumentos com argparse
      - acrescenta a opção de :
        - salvar yaml
        - remover um jogador da lista de jogadores conhecidos
        - sair da aplicação
        - Identificar o arbitro
        - adicionar esse jogador á lista de exclusoes
        - o ficheiro de yaml deve terum num numero sequencial apos o processamento
        - deve ser possivel adicionar um id a lista a ignorar
        - deve ser possivel adicionar um id a um jogador ja identificado
        - em vez de carregar todos os nao identificados deve carregar em grupos de 50
        - term interface para ir para o proximo ou o anterior grupo de 50
* 20260320-1
  - organiza o nomes do ficheiros da galeria pela cor da camisola dos jogadores
* 20260320-1
  - atribuir a um id um jogador ja identificado



  - app
    - ter uma lista inicial de jogadores no yaml e só poder atribuir um id não identificado a 1 jogador dessa lista
  - video analysis
    - ter um relatorio final com
      * Numero de frames Totais
      * Numero de frames analisdas
      * timestampo inicio da analise
      * timestampo fim da analise
      * duração da analise
      * numero de analises por segundo
      * fim lista
        * os jogadores identificados
        * os jogadores nao identificados
