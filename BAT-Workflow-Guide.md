# FYP Sign Language 一鍵啟動說明

最後更新：2026-03-31

這份專案給一般使用者的啟動方式只需要一個批次檔：
- run-fyp-tools.bat

此批次檔會直接啟動：
1. Python 後端：cv_hands/app_simple.py
2. React 前端：my-app

不需要使用者自行部署或啟動 AI 訓練環境。

---

## 0. 需要安裝的軟體

- Python 3.10（建議 3.10.x）
- Node.js 18 以上（建議 LTS）

> 只要系統有安裝上述兩項，其餘 Python/Node 套件會由 run-fyp-tools.bat 自動安裝。

---

## Python 套件（自動安裝）

來源檔案：cv_hands/requirements.txt

- opencv-python==4.8.0.76
- mediapipe==0.10.14
- numpy==1.24.3
- pillow==10.0.0
- tensorflow==2.13.0
- openvino==2023.3.0
- fastapi==0.100.0
- uvicorn==0.23.0
- websockets>=12,<15
- jax
- jaxlib

安裝位置：專案根目錄下的 .venv-app310（由批次檔自動建立）

## React / Node.js 套件（自動安裝）

來源檔案：my-app/package.json

- react, react-dom, react-scripts
- react-router-dom, react-icons
- http-proxy-middleware
- @mediapipe/camera_utils, @mediapipe/drawing_utils, @mediapipe/hands
- 其他測試與工具相依套件

另外若專案根目錄 node_modules 不存在，批次檔也會自動安裝根目錄 package.json 的依賴。

---

## 1. 使用方式

在專案根目錄直接雙擊：
- run-fyp-tools.bat

啟動後會自動：
1. 檢查 Python 3.10 與 Node.js 是否可用
2. 建立 Python 虛擬環境 .venv-app310（第一次執行）
3. 安裝 cv_hands/requirements.txt（第一次執行）
4. 安裝 Node.js 依賴（第一次執行）
5. 開新視窗啟動 app_simple.py
6. 開新視窗啟動 React (npm start)

---

## 2. 啟動成功後網址

- 後端：http://localhost:5001
- 前端：http://localhost:3000
- FastAPI 文件：http://localhost:5001/docs

---

## 3. 常見問題

### 問題：Python not found in PATH
原因：系統找不到 Python。
處理：安裝 Python 3.10+，並加入 PATH 或安裝 py launcher。

### 問題：Python 3.10 not found
原因：系統只有其他 Python 版本。
處理：請安裝 Python 3.10（TensorFlow 2.13 建議版本）。

### 問題：Node.js not found in PATH
原因：系統找不到 Node.js。
處理：安裝 Node.js 18+，並加入 PATH。

### 問題：React 沒有啟動
原因：首次安裝依賴失敗或 npm 套件不完整。
處理：
1. 到 my-app 資料夾執行 npm install
2. 再次執行 run-fyp-tools.bat

---

## 4. 備註

- 訓練用途的 .bat（CUDA/cuDNN/Notebook）保留給開發者，不是一般使用者流程。
- 一般展示與操作，只要執行 run-fyp-tools.bat 即可。

# FYP Sign Language 批次檔整合操作手冊

最後更新：2026-03-31

本文件把目前專案中常用的批次檔（.bat）整合為單一操作指南，並搭配統一入口腳本：
- run-fyp-tools.bat

---

## 1. 檔案總覽

### install-cudnn-to-cuda115.bat
用途：把你下載並解壓好的 cuDNN 複製到 CUDA 11.5 安裝路徑。  
適用時機：新電腦第一次配置、或 CUDA 目錄缺少 cudnn64_8.dll。  

必要條件：
- CUDA 11.5 已安裝於：C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.5
- 你已下載並解壓 cuDNN for CUDA 11

執行範例：
- install-cudnn-to-cuda115.bat "C:\Users\你的帳號\Downloads\cudnn-windows-x86_64-8.x.x.x_cuda11-archive"

---

### start-train-cuda115.bat
用途：啟動訓練專用命令視窗，注入 CUDA/cuDNN 環境變數，並先做 TensorFlow GPU 驗證。  
適用時機：你想手動進入訓練環境，再自行跑 python 或 jupyter 指令。

必要條件：
- 訓練 venv 存在：cv_hands\.venv-train310
- CUDA 11.5 與 cuDNN 可用

---

### run-train-notebook-cuda115.bat
用途：一鍵驗證 GPU 後直接啟動 Jupyter Notebook。  
適用時機：你要直接進入 notebook 訓練流程。

必要條件：
- 訓練 venv 存在：cv_hands\.venv-train310
- CUDA 11.5 與 cuDNN 可用

---

### run-app-py310.bat
用途：使用固定 Python 3.10 執行 cv_hands\app.py。  
適用時機：你要用桌面相機推論版本 app.py。

必要條件：
- Python 3.10 路徑存在（目前腳本內建絕對路徑）

備註：
- 如果換電腦，請同步修改 run-app-py310.bat 裡的 PY310 路徑。

---

### setup-and-run.bat
用途：清理並重裝依賴後，一次啟動 FastAPI 與 React 開發伺服器。  
適用時機：開發環境異常、套件衝突、或要重建一個乾淨啟動流程。

會做的事：
- 卸載部分 Python 套件
- 刪除 root 與 my-app 的 node_modules / lock
- 重裝依賴
- 啟動：
  - FastAPI（預設 5001）
  - React（預設 3000）

---

## 2. 建議日常流程

### A. 一般開發（前後端）
1. 執行 setup-and-run.bat
2. 確認服務：
   - React: http://localhost:3000
   - FastAPI: http://localhost:5001/docs

### B. Notebook 訓練（GPU）
1. 先確認 CUDA 11.5 + cuDNN 已就緒
2. 執行 run-train-notebook-cuda115.bat
3. 在 Notebook 選到訓練環境 kernel

### C. 新機第一次設定
1. 執行 install-cudnn-to-cuda115.bat（帶入 cuDNN 解壓路徑）
2. 建立/重建 cv_hands\.venv-train310
3. 執行 run-train-notebook-cuda115.bat 驗證

---

## 3. 常見錯誤與排查

### 錯誤：Training venv not found
原因：缺少 cv_hands\.venv-train310。  
處理：
1. py -3.10 -m venv cv_hands/.venv-train310
2. 安裝訓練依賴：
   - cv_hands/.venv-train310/Scripts/python.exe -m pip install -r cv_hands/requirements-train-win-py310.txt

### 錯誤：CUDA runtime not found
原因：CUDA 11.5 未安裝或路徑不符。  
處理：確認 cudart64_110.dll 位於 CUDA 11.5 bin 目錄。

### 錯誤：cudnn64_8.dll not found
原因：cuDNN 尚未放到 CUDA 或專案本地 third_party。  
處理：先跑 install-cudnn-to-cuda115.bat。

### 錯誤：localhost:3000 無法連線
原因：React 開發伺服器沒啟動。  
處理：到 my-app 執行 npm start，或直接跑 setup-and-run.bat。

---

## 4. 統一入口腳本

請使用：run-fyp-tools.bat

功能：
- 提供文字選單
- 統一呼叫目前 5 支批次檔
- 可直接開啟本手冊

建議：
- 日常操作優先從 run-fyp-tools.bat 進入，減少手動輸入錯誤。
