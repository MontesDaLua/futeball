# Requirements

# Install
```bash
  make install
```

## youtube downloader


https://github.com/yt-dlp/yt-dlp/wiki/Installation


```bash
 source venv/bin/activate
 sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
 sudo chmod a+rx /usr/local/bin/yt-dlp  # Make executable
 yt-dlp "https://www.youtube.com/watch?v=2fB6zH1_cBo"
 mv SU\ Sintrense\ x\ FC\ Alverca\ ｜\ DIRETO\ \[2fB6zH1_cBo\].mp4 data/samples/game1/video/SINT-ALV.mp4
 # start game in video 9'15''
```


# Run

## make samples
```bash
ffmpeg -i  data/samples/game1/video/20260215/SINT-ALV-full.mp4  \
       -ss 00:09:14 \
       -t 00:01:00 \
       -c copy  data/samples/game1/video/20260215/SINT-ALV-min1.mp4
ffmpeg -i  data/samples/game1/video/20260215/SINT-ALV-full.mp4  \
       -ss 00:09:14 \
       -t 00:05:00 \
       -c copy  data/samples/game1/video/20260215/SINT-ALV-min5.mp4
```

## Teste
```bash
date
source ./venv/bin/activate
export DT=20260215
python3 main.py \
  --video=data/samples/game1/video/${DT}/SINT-ALV-min1.mp4 \
  --config=data/samples/game1/config/${DT}/SINT-ALV.yml \
  --output=tmp/${DT}-SINT-ALV.pdf
date
```
