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
