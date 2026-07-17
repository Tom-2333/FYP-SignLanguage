# 👐 香港手語即時辨識系統 (HKSL Live Recognition)

本專案使用 **深度學習 (CTC 模型)** 與 **MediaPipe Holistic** 即時辨識香港手語 (HKSL)。  
你只需要對著鏡頭做手語，畫面上就會即時顯示對應的英文 gloss（手語詞彙標籤）。

---
## 📁 專案檔案結構
FYP-SignLanguage/
├── live_recognition.py # 即時辨識主程式 (用鏡頭)
├── train.py # 訓練模型
├── model.py # 模型結構定義
├── dataset.py # 讀取特徵與資料集處理
├── export_model.py # 將訓練好的模型轉成 ONNX
├── extract_hksllex_rich_features.py # 從影片抽取特徵 (通常只需執行一次)
├── split_manifest.py # (可選) 分割訓練/驗證清單
├── holistic_landmarker.task # MediaPipe 全身模型 (需下載)
├── model/
│ ├── sign_language_mla.onnx # 匯出後的 ONNX 模型 (訓練後產生)
├── data/
│ ├── gloss_to_id.json # 手語 gloss 對應數字 ID
│ ├── manifest.csv # 完整特徵清單
│ ├── train.csv / val.csv # 訓練/驗證清單
│ └── features/ # 存放所有 .pt 特徵檔
├── checkpoints/
│ └── best.pt # 訓練過程中最佳模型權重
└── README.md # 本說明文件

---
## ⚙️ 環境需求

- **Windows 10 / 11** 或 **macOS** 或 **Linux**
- **Python 3.10 以上** (推薦 3.11 或 3.12，3.13 亦可)
- **攝影機** (內置或外接 Webcam)
- **NVIDIA 顯示卡 (可選，加速訓練)** 或 Intel 內顯 / AMD 顯卡 (用於推論加速)
- **硬碟空間**：約 2 GB (特徵檔 + 模型)

---
## 🚀 快速開始

### 1. 下載專案並建立虛擬環境

```powershell
git clone <你的專案網址>
cd FYP-SignLanguage
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# 或 source .venv/bin/activate  (macOS / Linux)
```
### 2. 安裝所需套件
```powershell
pip install opencv-python mediapipe numpy torch pillow onnxruntime-directml
如果要用 NVIDIA GPU 訓練，請額外安裝 CUDA 版 PyTorch：
```
```powershell
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```
### 3. 下載 MediaPipe Holistic 模型
```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task" -OutFile "holistic_landmarker.task"
```
這個檔案約 6 MB，已包含在 GitHub 上。

## 📸 即時手語辨識 (使用已訓練好的模型)
如果已經有 sign_language_mla.onnx (匯出的 ONNX 模型)，直接執行：

```powershell
python live_recognition.py
```
- 按下 q 離開程式。

- 畫面上會顯示：

    - 手部、身體、臉部骨架

    - 即時預測的 gloss (例如 hello thank you)

    - 每秒幀數 (FPS)

若無 ONNX 模型，請先依下方步驟完成訓練與匯出。

## 🏋️ 訓練自己的模型
### 步驟 1：從影片抽取 225 維特徵
```powershell
python extract_hksllex_rich_features.py `
    --json "C:\path\to\HKSL-LEX\data.json" `
    --video_dir "C:\path\to\HKSL-LEX\videos" `
    --out_dir data
```
這會產生 data/features/ (數千個 .pt 檔) 和 data/gloss_to_id.json、data/manifest.csv。
⚠️ 此步驟耗時較久 (數小時至數天)，建議執行一次後保留檔案。

### 步驟 2：分割訓練 / 驗證清單
```powershell
python split_manifest.py
```
會自動將 manifest.csv 隨機分成 train.csv (90%) 與 val.csv (10%)。

### 步驟 3：訓練 CTC 模型
```powershell
python train.py `
    --train-manifest data/train.csv `
    --val-manifest data/val.csv `
    --num-classes 2762 `
    --device cuda
```
若無 NVIDIA GPU，--device cuda 會自動降為 CPU。

訓練過程會顯示每個 epoch 的損失，並自動儲存最佳驗證模型到 checkpoints/best.pt。

建議訓練至少 50～100 epoch，直到 val_loss 低於 5.0 以下。

常用參數調整 (可依需要加入)：

```text
--batch-size 128
--lr 1e-4
--dropout 0.4
--weight-decay 0.05
--epochs 300
```
### 步驟 4：匯出 ONNX 模型 (部署用)
```powershell
python export_model.py `
    --checkpoint checkpoints/best.pt `
    --gloss_map data/gloss_to_id.json `
    --output sign_language_mla.onnx
```

產生的 sign_language_mla.onnx 即可供 live_recognition.py 使用。

## 🤔 常見問題
### ❓ 即時辨識時螢幕只有骨架，沒有顯示 gloss？
模型可能尚未充分訓練 (val_loss 仍太高)。
請繼續訓練，直到 val_loss 降到 5.0 以下。
也可在 live_recognition.py 中查看信心度。

### ❓ 我想使用 NVIDIA GPU 加速推論，需要改程式嗎？
不需要。live_recognition.py 已使用 DirectML，會自動選擇系統中最快的顯卡 (包含 NVIDIA)。

### ❓ 訓練時出現 pin_memory 警告？
代表你安裝的是 CPU 版 PyTorch。請依上方「安裝 CUDA 版 PyTorch」步驟更換。

### ❓ 如何確認訓練正在使用 GPU？
在終端機執行：

```powershell
python -c "import torch; print(torch.cuda.is_available())"
```
輸出 True 即表示 GPU 可用。

## 🧠 關於本專案的模型
輸入：60 幀的全身關鍵點 (225 維)

輸出：2762 個香港手語 gloss + 1 個空白標籤

架構：低秩多頭注意力 (MLA) + CTC 損失

加速：訓練用 PyTorch CUDA，推論用 ONNX Runtime + DirectML

## 📬 聯絡與貢獻
本專案為香港手語研究用途，歡迎提出 issues 或 pull requests。
如有任何問題，請聯絡開發團隊。

 手語是美麗的語言，讓科技幫助更多人溝通 🤟