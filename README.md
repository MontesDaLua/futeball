# Requirements
python3
make
git
# Install
```bash
  make install
  export YOLO_DIR=yolo_dir
  # V8
  curl -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt -o ${YOLO_DIR}/yolov8n.pt
  curl -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.pt -o ${YOLO_DIR}/yolov8s.pt
  curl -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt -o ${YOLO_DIR}/yolov8m.pt
  curl -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8l.pt -o ${YOLO_DIR}/yolov8l.pt
  curl -L https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8x.pt -o ${YOLO_DIR}/yolov8x.pt

  # V10
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10n.pt -o ${YOLO_DIR}/yolov10n.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10s.pt -o ${YOLO_DIR}/yolov10s.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov10m.pt -o ${YOLO_DIR}/yolov10m.pt
  curl -L -O https://github.com/Log-0/yolov10-models/releases/download/v1.1/yolov10l.pt -o ${YOLO_DIR}/yolov10l.pt

  # V11
  # Nano, Small, Medium, Large, X
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt -o ${YOLO_DIR}/yolov11n.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt -o ${YOLO_DIR}/yolov11s.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt -o ${YOLO_DIR}/yolov11m.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt -o ${YOLO_DIR}/yolov11l.pt
  curl -L -O https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt -o ${YOLO_DIR}/yolov11x.pt
```

## youtube downloader


https://github.com/yt-dlp/yt-dlp/wiki/Installation


```bash
 source venv/bin/activate
 yt-dlp "https://www.youtube.com/watch?v=2fB6zH1_cBo" --output data/samples/game1/video/SINT-ALV-full.mp4
 # start game in video 9'15''
```


# Run

## make samples
```bash
ffmpeg -i data/samples/game1/video/SINT-ALV-full.mp4.webm \
       -ss 00:09:14 \
       -t 00:01:00 \
       -c copy  data/samples/game1/video/SINT-ALV-min1.mp4
ffmpeg -i data/samples/game1/video/SINT-ALV-full.mp4.webm \
       -ss 00:09:14 \
       -t 00:05:00 \
       -c copy  data/samples/game1/video/SINT-ALV-min5.mp4
```

## Teste com separacao scripts
### linux  - bash
```bash
source ./venv/bin/activate
export game_name=SINT-ALV



export video_path=data/samples/game1/video/${game_name}-min1.mp4
export config_path=data/samples/game1/game_analysis/${game_name}.yml


export proc_config_file=data/frame_analysis/simple.yml

export data_path=data/samples/game1/game_analysis/${game_name}-data.json
export data_config_file=data/samples/game1/game_analysis/${game_name}.yml
export gallery_dir=data/samples/game1/game_analysis/gallery

export video_save_dir=data/samples/game1/game_analysis/
export pdfname=${video_save_dir}/report-${game_name}.pdf

date
python run_video_processing.py \
  --video ${video_path} \
  --proc_config ${proc_config_file} \
  --game_data ${data_config_file} \
  --output ${data_path} \
  --save-video ${video_save_dir}/SAVE_VIDEO.mp4 \
  --gallery ${gallery_dir}
date

streamlit run id_manager_app.py -- \
    --game_data ${data_config_file} \
    --gallery ${gallery_dir}


date
python report_generator.py \
  --input ${data_path} \
  --config ${config_path}  \
  --output ${pdfname}
date
```

### powershell (re test )
```powershell
# 1. Ativar o ambiente virtual (Caminho padrão Windows)
# Se a tua venv foi criada no wsl
. .\venv\bin\activate.ps1

# 2. Definir Variáveis de Configuração
$env:game_name = "SINT-ALV"
$env:video_path = "data/samples/game1/video/20260215/$($env:game_name)-min1.mp4"
$env:config_path = "data/samples/game1/config/20260215/$($env:game_name).yml"
$env:data_path = "data/samples/game1/analisys/20260215/$($env:game_name)-data.json"
$env:proc_config_file = "data/frame_analysis/simple.yml"
$env:data_config_file = "data/samples/game1/config/20260215/SINT-ALV.yml"
$env:video_save_dir = "tmp"
$env:gallery_dir = "tmp/lixo"

# 3. Otimizações para Snapdragon / ARM64 Nativo
# DirectML e OpenBLAS performance
$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"

# 4. Execução com timestamps
Write-Host "--- Início da Análise: $(Get-Date -Format 'HH:mm:ss') ---" -ForegroundColor Cyan

python run_video_processing.py `
  --video $env:video_path `
  --proc_config $env:proc_config_file `
  --game_data $env:data_config_file `
  --output $env:data_path `
  --save-video "$env:video_save_dir/SAVE_VIDEO.mp4" `
  --gallery $env:gallery_dir

Write-Host "--- Fim da Análise: $(Get-Date -Format 'HH:mm:ss') ---" -ForegroundColor Green``powershell
```
