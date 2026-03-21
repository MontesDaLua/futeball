# Requirements
python3
make
git
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

## Teste com separacao scripts
### linux  - bash
```bash
source ./venv/bin/activate
export game_name=SINT-ALV
export video_path=data/samples/game1/video/20260215/${game_name}-min1.mp4
export config_path=data/samples/game1/config/20260215/${game_name}.yml
export data_path=data/samples/game1/analisys/20260215/${game_name}-data.json
export proc_config_file=data/frame_analysis/simple.yml
export data_config_file=data/samples/game1/config/20260215/SINT-ALV.yml
export video_save_dir=tmp
export gallery_dir=tmp/lixo

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




python report_generator.py \
  --input ${data_path} \
  --config ${config_path}  \
  --output tmp/${game_name}-Relatorio.pdf
date
```

### powershell
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
