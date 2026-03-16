* template report in multiple languages

* generate speed reports image in a temporary folder and remove the images after the report run
* include in game configuration
  * visitor
  * home team
  * players that bellow to home or visitors team
* split the game analysis in 2 scripts
  * video processing
  * report generator
* report generator should have:
    * optional video generator based on the frames that where analised
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
