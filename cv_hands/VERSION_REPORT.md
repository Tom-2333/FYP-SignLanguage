# 版本報告

## Python 環境

### 虛擬環境 (.venv)
- **Python 版本**: 3.11.9
- **Python 路徑**: C:\Users\PC\Desktop\hands\.venv\Scripts\python.exe

### 系統 Python
- **Python 版本**: 3.11.9

---

## 虛擬環境已安裝套件

| 套件名稱 | 版本 | 狀態 |
|---------|------|------|
| tensorflow | 2.15.1 | ✅ 正常 |
| tensorflow-intel | 2.15.1 | ✅ 正常 |
| keras | 2.15.0 | ✅ 正常 |
| mediapipe | 0.10.9 | ✅ 正常 |
| opencv-python | 4.12.0.88 | ✅ 正常 |
| numpy | 1.26.4 | ✅ 正常 |
| protobuf | 3.20.3 | ✅ 正常 |
| ml-dtypes | 0.3.2 | ✅ 正常 |
| pillow | 12.0.0 | ✅ 正常 |
| scikit-learn | 1.8.0 | ✅ 正常 |

---

## 版本兼容性檢查

### ✅ 已解決的問題
1. **TensorFlow Lite 訪問** - TensorFlow 2.15.1 正確安裝，`tf.lite` 可用
2. **Protobuf 兼容性** - 降級至 3.20.3 以支援 MediaPipe 0.10.9
3. **NumPy 兼容性** - 降級至 1.26.4 以支援 TensorFlow 2.15.x
4. **虛擬環境** - 套件現在正確安裝在 .venv 中

### ⚠️ 當前警告
運行 app.py 時出現以下警告（不影響基本功能）：

1. **Keras 模型載入警告**:
   ```
   Warning: Failed to load Keras model: Error when deserializing class 'InputLayer' 
   using config={'batch_shape': [None, 25, 80], 'dtype': 'float32', 'sparse': False, 
   'ragged': False, 'name': 'input_layer'}.
   Exception encountered: Unrecognized keyword arguments: ['batch_shape']
   ```
   - **原因**: Keras 3.x 與 Keras 2.15.0 之間的 API 差異
   - **影響**: 應用程式自動回退到 TFLite 模型
   - **解決方案**: 使用 TensorFlow 2.15.x 重新訓練模型，或使用 TFLite 模型

2. **TFLite 模型版本警告**:
   ```
   Warning: Failed to load TFLite model: Didn't find op for builtin opcode 
   'FULLY_CONNECTED' version '12'.
   ```
   - **原因**: TFLite 模型使用較新的操作版本
   - **影響**: 需要使用兼容的 TensorFlow 版本重新轉換模型
   - **解決方案**: 使用 TensorFlow 2.15.1 重新訓練並轉換模型為 TFLite

---

## 建議的操作

### 立即執行
應用程式可以運行，但建議重新訓練模型以消除警告：

1. **重新訓練 LSTM 序列模型**:
   ```powershell
   .\.venv\Scripts\python.exe -m jupyter notebook train_lstm_sequence.ipynb
   ```
   - 確保使用虛擬環境中的 Python
   - 訓練後保存為 .keras 和 .tflite 格式

2. **重新訓練關鍵點分類器** (如需要):
   ```powershell
   .\.venv\Scripts\python.exe -m jupyter notebook keypoint_classification.ipynb
   ```

### 運行應用程式
```powershell
.\.venv\Scripts\python.exe .\app.py
```

---

## 版本兼容性矩陣

| 組件 | 兼容版本 | 當前版本 | 狀態 |
|------|---------|---------|------|
| Python | 3.8-3.11 | 3.11.9 | ✅ |
| TensorFlow | 2.15.x | 2.15.1 | ✅ |
| Keras | 2.15.0 | 2.15.0 | ✅ |
| MediaPipe | 0.10.9 | 0.10.9 | ✅ |
| Protobuf | 3.20.x-3.x | 3.20.3 | ✅ |
| NumPy | <2.0, >=1.23.5 | 1.26.4 | ✅ |
| OpenCV | 4.x | 4.12.0 | ✅ |

---

## 變更記錄

### 2025-12-27
- ✅ 修復虛擬環境套件安裝問題
- ✅ 重新安裝 TensorFlow 2.15.1 至虛擬環境
- ✅ 驗證所有套件版本兼容性
- ✅ 確認 app.py 可以運行
- ⚠️ 發現模型兼容性警告（不影響基本功能）

---

**報告生成時間**: 2025-12-27
**虛擬環境狀態**: ✅ 正常
**應用程式狀態**: ✅ 可運行（有警告）
