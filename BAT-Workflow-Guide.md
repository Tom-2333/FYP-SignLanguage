# FYP Sign Language 一鍵啟動說明

最後更新：2026-04-06

這份專案給一般使用者的啟動方式只需要一個批次檔：
- run-fyp-tools.bat

此批次檔會直接啟動：
1. Python 後端：cv_hands/app_simple.py
2. React 前端：my-app

不需要使用者自行部署或啟動 AI 訓練環境。

---

## 0. 需要先安裝的軟體

- Python（建議 3.10.x）
- Node.js 18+（建議 LTS）

> 其餘 Python / Node 套件會由 run-fyp-tools.bat 自動安裝。

---

## 1. Python 套件（自動安裝）

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

安裝方式：
- 使用系統 Python（python -m pip）直接安裝
- 不建立 .venv

---

## 2. React / Node.js 套件（自動安裝）

來源檔案：my-app/package.json

會自動安裝：
- react, react-dom, react-scripts
- react-router-dom, react-icons
- http-proxy-middleware
- @mediapipe/camera_utils, @mediapipe/drawing_utils, @mediapipe/hands
- 其他測試與工具相依套件

另外若專案根目錄 node_modules 不存在，也會自動安裝根目錄 package.json 的依賴。

---

## 3. 使用方式

在專案根目錄直接雙擊：
- run-fyp-tools.bat

啟動後會自動：
1. 檢查 Python 與 Node.js 是否可用
2. 使用系統 Python 安裝 cv_hands/requirements.txt（第一次執行）
3. 安裝 Node.js 依賴（第一次執行）
4. 開新視窗啟動 app_simple.py
5. 開新視窗啟動 React (npm start)

---

## 4. 啟動成功後網址

- 後端：http://localhost:5001
- 前端：http://localhost:3000
- FastAPI 文件：http://localhost:5001/docs

---

## 5. 常見問題

### 問題：Python not found in PATH
原因：系統找不到 Python。
處理：安裝 Python 並加入 PATH。

### 問題：Node.js not found in PATH
原因：系統找不到 Node.js。
處理：安裝 Node.js 並加入 PATH。

### 問題：React 沒有啟動
原因：首次安裝依賴失敗或 npm 套件不完整。
處理：
1. 到 my-app 資料夾執行 npm install
2. 再次執行 run-fyp-tools.bat

### 問題：想要重新安裝 Python 依賴
處理：
1. 刪除專案根目錄的 .python_deps_installed
2. 再次執行 run-fyp-tools.bat
