# FYP Sign Language：換電腦快速接手說明

最後更新：2026-02-23

## 1) 目前已確認可用的訓練環境
- OS：Windows
- Python：3.10.11
- TensorFlow：2.10.1（Windows 原生 GPU 可用版本）
- CUDA：11.5
- cuDNN：8.9.7（cuda11）
- 訓練 venv：cv_hands/.venv-train310

## 2) 你的主要檔案
- GPU 設定/實作說明：GPU-Training-Implementation-Report.md
- cuDNN 安裝腳本：install-cudnn-to-cuda115.bat
- 訓練 shell：start-train-cuda115.bat
- 一鍵啟動訓練 notebook：run-train-notebook-cuda115.bat
- GPU 驗證程式：cv_hands/tools/verify_tf_gpu.py
- 訓練 notebook：cv_hands/train_lstm_sequence.ipynb

## 3) 新電腦最快流程（建議照順序）
1. 安裝 NVIDIA 驅動、CUDA 11.5、Python 3.10.x
2. 下載並解壓 cuDNN（你目前用的是 cudnn-windows-x86_64-8.9.7.29_cuda11-archive）
3. 在專案根目錄執行：
   - install-cudnn-to-cuda115.bat "你的cuDNN解壓資料夾完整路徑"
4. 重建訓練 venv（PowerShell 於專案根目錄）：
   - py -3.10 -m venv cv_hands/.venv-train310
   - cv_hands/.venv-train310/Scripts/python.exe -m pip install --upgrade pip
   - cv_hands/.venv-train310/Scripts/python.exe -m pip install -r cv_hands/requirements-train-win-py310.txt
5. 驗證 GPU：
   - cv_hands/.venv-train310/Scripts/python.exe cv_hands/tools/verify_tf_gpu.py
   - 預期看到 RESULT=PASS、GPU_COUNT=1
6. 啟動 notebook：
   - run-train-notebook-cuda115.bat

## 4) Notebook 目前關鍵設定（train_lstm_sequence.ipynb）
- 第 7 格：已加入資料清理（移除 NaN/Inf 與非法標籤）
- 第 11 格：
  - ModelCheckpoint 設為 save_best_only=True（只保留最佳模型）
  - 監看指標 monitor='val_accuracy'，mode='max'
  - EarlyStopping 目前是 patience=20，可自行調整
- 第 20 格：訓練曲線繪圖（若缺 matplotlib 會自動安裝）

## 5) 為什麼會看到 val_loss=nan
- 常見原因：驗證資料曾有 NaN/Inf 或數值異常
- 目前 notebook 已加前處理保護
- 即使 val_loss=nan，仍可先用 val_accuracy 作為 best model 依據

## 6) 提早停止訓練會不會壞掉
- 不會刪掉資料集
- 已存下來的最佳 .keras 模型會保留
- 若中斷在 model.fit 期間，history 可能不存在（屬正常）
- 中斷後若要繼續後續流程，先載入最佳模型最安全：
  - model = tf.keras.models.load_model(model_save_path)

## 7) 常調參數位置（都在第 11 格）
- 早停耐心值：patience=20
- 最大 epoch：epochs=2000
- batch size：batch_size=32
- best model 監看指標：monitor='val_accuracy'

## 8) 目前已驗證結果（本機）
- TensorFlow 可偵測 GPU（NVIDIA RTX A4000）
- verify_tf_gpu.py 通過（PASS）
- 訓練可在 GPU 執行

## 9) 換機後若出錯，優先檢查
1. Python 是否真的是 3.10
2. CUDA 路徑是否為 C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.5
3. cudnn64_8.dll 是否存在於 CUDA\bin
4. Notebook kernel 是否選到訓練環境（FYP train venv）
5. 先跑一次 cv_hands/tools/verify_tf_gpu.py

## 10) Windows 與手機部署格式怎麼選（OpenVINO vs TFLite）
- 建議結論：
   - Windows（特別是 Intel CPU/iGPU）：優先 OpenVINO
   - 手機（Android/iOS）：優先 TFLite

### OpenVINO（較適合 Windows）
- 優點：
   - 在 Intel 硬體上常有更佳推論效能（延遲/吞吐）
   - 桌面部署工具鏈成熟，適合即時視訊推論
- 缺點：
   - 行動端整合不如 TFLite 普及
   - 轉換與部署流程較複雜

### TFLite（較適合手機）
- 優點：
   - Android/iOS 生態完整，整合容易
   - 模型檔小、啟動快，適合 App 端離線推論
- 缺點：
   - 桌面端最佳化彈性通常不如 OpenVINO
   - 某些模型需要 SELECT_TF_OPS/Flex，可能增加包體與相依

## 11) 建議採用「雙輸出」交付（同一份訓練模型）
- 訓練後輸出三種產物：
   1. `model/keypoint_classifier/keypoint_sequence_classifier.keras`（best model）
   2. `model/keypoint_classifier/keypoint_sequence_classifier_savedmodel`（給 OpenVINO 轉換）
   3. `model/keypoint_classifier/keypoint_sequence_classifier.tflite`（手機端）
- 實務建議：
   - Windows 版 App 使用 OpenVINO 路線
   - 手機 App 使用 TFLite 路線
   - Notebook 訓練結束後，依序執行「SavedModel 匯出」與「TFLite 轉換」兩格
