# 手勢識別程序 - 啟動說明

## ✅ 問題已解決！

您的程序現在可以正常運行了！

## 🎯 問題原因

1. **Python 環境衝突**：系統有兩個 Python 環境
   - Python 3.10 (系統環境) ✅ 
   - Python 3.11 (虛擬環境) ❌ 缺少套件
   
2. **套件版本不相容**：
   - TensorFlow、MediaPipe、JAX、ml_dtypes 之間的版本衝突
   - 已修復並安裝相容版本

## 🚀 如何啟動程序

### 方法 1：使用啟動腳本（推薦）⭐

雙擊運行：
```
run.bat
```

### 方法 2：直接命令

在終端中運行：
```bash
C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe app.py
```

### 方法 3：在 VSCode 中設置

1. 按 `Ctrl + Shift + P`
2. 輸入 "Python: Select Interpreter"
3. 選擇 `Python 3.10.11 64-bit` (C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe)
4. 之後就可以直接使用 `python app.py`

## 📋 已安裝的相容套件版本

- **Python**: 3.10.11
- **TensorFlow**: 2.15.0
- **MediaPipe**: 0.10.14
- **OpenCV**: 4.11.0.86
- **NumPy**: 1.26.4
- **JAX**: 0.4.20
- **Protobuf**: 4.25.3
- **ml_dtypes**: 0.5.4

## 🎮 程序操作說明

### 快捷鍵
- **ESC** - 退出程序
- **k** - 進入關鍵點記錄模式
- **s** - 進入序列記錄模式
- **n** - 返回正常模式
- **o** - 進入定時檢測模式

### 功能特點
- ✅ 手部地標檢測和繪製
- ✅ 臉部地標檢測和繪製
- ✅ 姿勢骨架檢測和繪製
- ✅ 手勢分類（單次和序列）
- ✅ 即時 FPS 顯示
- ✅ 中文標籤支持

## ⚠️ 常見警告（可以忽略）

程序啟動時可能看到這些警告，但不影響運行：
- `oneDNN custom operations are on` - TensorFlow 性能優化提示
- `Feedback manager requires a model` - MediaPipe 模型兼容性提示
- `sparse_softmax_cross_entropy is deprecated` - TensorFlow 版本提示

這些都是正常的信息提示，不影響程序功能。

## ❓ 故障排除

### Q: 為什麼關閉 VSCode 後程序就無法運行？
A: VSCode 可能自動切換到虛擬環境。解決方法：
1. 使用 `run.bat` 啟動腳本
2. 或按照上面"方法 3"設置 VSCode 默認解釋器

### Q: 出現 "Module not found" 錯誤
A: 確保使用正確的 Python 環境：
```bash
C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe app.py
```

### Q: 攝像頭無法打開
A: 檢查：
1. 其他程序是否佔用攝像頭
2. 攝像頭權限設置
3. 嘗試修改 `app.py` 中的攝像頭設備號（默認為 0）

### Q: FPS 太低
A: 已優化設置：
- 解析度：640x480
- 輕量級手部模型
- TFLite 優化推理
- 多線程處理

## 💡 性能提示

如需更高 FPS，可以：
1. 降低解析度：
   ```bash
   python app.py --width 480 --height 360
   ```

2. 只檢測單手：
   修改 app.py 中 `max_num_hands=2` 改為 `max_num_hands=1`

3. 臨時禁用臉部/姿勢檢測：
   註釋掉 `app.py` 中相關代碼行

## 📝 最新更改

**2025-12-27 更新**:
- ✅ 修復了 Python 環境衝突問題
- ✅ 解決了套件版本不相容問題
- ✅ 恢復了 face_mesh 和 pose 檢測功能
- ✅ 優化了 TFLite 推理性能
- ✅ 創建了便捷啟動腳本

---

**程序狀態**: ✅ 正常運行  
**優化狀態**: ✅ 已優化  
**最後測試**: 2025-12-27 19:20

如有任何問題，請檢查終端輸出獲取詳細錯誤信息。

