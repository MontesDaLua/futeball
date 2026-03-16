
* template report in multiple languages
* include in game configuration
  * visitor
  * home team
  * players that bellow to home or visitors team
* split the game analysis in 2 scripts
  * video processing
  * report generator
* report generator should have:
    * optional video generator based on the frames that where analised
    * players that where not identified
    * para cada jogador
      * quais as primeiras 100 frames que identificaram os valores atribuidos
* report generator should have
  * optional watter mark
  * summary from the video analysis
    * file name
    * duration
    * numer of original frames
    * frames analised
  * list of unidentified players
    * optional list of images
  * images should be based
    * on time (starting in the video analysis beginning ) , not in samples
