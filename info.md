
---
### Start
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1

# 安裝必要套件（複製整行）
pip install opencv-python mediapipe numpy torch pillow onnxruntime-directml

# 執行即時手語辨識
python live_recognition.py

### 1️⃣ `extract_hksllex_rich_features.py`  
**功能：從原始影片中抽取 MediaPipe Holistic 225 維特徵，並生成資料清單。**  
- 讀取 `data.json`（HKSL-LEX 影片描述）  
- 從 `video_dir` 載入每個影片（`.mp4` / `.webp`）  
- 用 MediaPipe 0.10.x Tasks API 偵測手、姿勢、臉部關鍵點  
- 將每一幀的特徵向量存成 `data/features/<video_id>.pt`  
- 建立 `data/gloss_to_id.json`（不重複 gloss 對應的整數 ID）  
- 輸出 `data/manifest.csv`（每部影片的路徑、目標 ID、幀數、中英文 gloss）

**執行指令：**
```powershell
python extract_hksllex_rich_features.py `
    --json "C:\path\to\data.json" `
    --video_dir "C:\path\to\videos" `
    --out_dir data
```

**產出：**
- `data/features/`：數千個 `.pt` 檔案（每個影片一個）
- `data/gloss_to_id.json`：gloss 對 ID 的對照表
- `data/manifest.csv`：完整的資料清單

---

### 2️⃣ （可選）切分清單腳本（可手動或寫一個 `split_manifest.py`）  
**功能：將 `manifest.csv` 隨機拆成訓練集與驗證集。**  
這一步可以用一段簡單的 Python 程式完成，你也可以手動分割。

**範例腳本內容（自行建立 `split_manifest.py`）：**
```python
import csv, random
with open("data/manifest.csv") as f:
    header = next(f)
    rows = list(csv.reader(f))
random.seed(42); random.shuffle(rows)
split = int(0.9 * len(rows))
for name, data in [("train", rows[:split]), ("val", rows[split:])]:
    with open(f"data/{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path","target","input_lengths","english_gloss","chinese_gloss","cantonese_gloss"])
        w.writerows(data)
    print(f"{name}.csv: {len(data)} samples")
```

**產出：** `data/train.csv`、`data/val.csv`

---

### 3️⃣ `dataset.py`  
**功能：定義資料集類別與 DataLoader，負責從清單中載入 `.pt` 特徵並處理 padding / time warp。**  
- `load_manifest()`：讀取 `.csv` 清單  
- `SignLanguageDataset`：將每個 `.pt` 檔案讀入，調整長度至固定 `seq_len`（預設 60），並依機率做時間扭曲（time warp）  
- `collate_ctc()`：將一個 batch 的資料包裝成 CTC 需要的格式  
- `make_dataloader()`：快速建立 DataLoader

這個檔案**不直接執行**，而是被 `train.py` 引用。

---

### 4️⃣ `model.py`  
**功能：定義 CTC 手語辨識模型（低秩多頭注意力 + CTC 輸出）。**  
- `InputProjection`：將 225 維投影到 128 維的隱藏空間  
- `LowRankMultiheadAttention`：低秩 KV 壓縮的自注意力  
- `MLADecoderLayer`：包含自注意力與前饋網路的解碼層  
- `SignLanguageModel`：完整模型，最後輸出 `log_softmax`，類別數為 `num_classes + 1`（空白 0）

這個檔案**不直接執行**，被 `train.py` 與 `export_model.py` 引用。

---

### 5️⃣ `train.py`  
**功能：訓練模型。**  
- 載入 `train.csv` / `val.csv` 產生 DataLoader  
- 建立 `SignLanguageModel`、CTC 損失、AdamW 優化器  
- 每個 epoch 印出損失，儲存驗證損失最低的模型到 `checkpoints/best.pt`

**執行指令：**
```powershell
python train.py `
    --train-manifest data/train.csv `
    --val-manifest data/val.csv `
    --num-classes 2762 `
    --batch-size 16 `
    --epochs 50 `
    --save-path checkpoints/best.pt
```

**產出：** `checkpoints/best.pt`（訓練好的權重）

---

### 6️⃣ `export_model.py`  
**功能：將訓練好的模型匯出成 ONNX 格式，供行動裝置部署。**  
- 載入 `checkpoints/best.pt` 和 `gloss_to_id.json` 取得類別數  
- 重新建立模型並載入權重  
- 以固定時間長度 60 的 dummy 輸入匯出 ONNX

**執行指令：**
```powershell
python export_model.py `
    --checkpoint checkpoints/best.pt `
    --gloss_map data/gloss_to_id.json `
    --output sign_language_mla.onnx
```

**產出：** `sign_language_mla.onnx`

---

### 📊 整體執行流程

```
1. 特徵提取
   ↓
2. 分割清單 (train.csv / val.csv)
   ↓
3. 訓練模型 (train.py)
   ↓
4. (選用) 匯出 ONNX (export_model.py)
```