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
