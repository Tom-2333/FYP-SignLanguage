# FYP 手語辨識專案 — 全面代碼優化報告

> 生成日期：2026-02-28  
> 範圍：React 前端、Python CV/FastAPI 後端、PHP API、AI 訓練 Notebook、專案整體架構

---

## 目錄

1. [前端 GUI 優化](#1-前端-gui-優化)
2. [AI 訓練代碼優化](#2-ai-訓練代碼優化)
3. [Python 後端 / 推論服務優化](#3-python-後端--推論服務優化)
4. [PHP 後端 API 優化](#4-php-後端-api-優化)
5. [專案整體優化](#5-專案整體優化)

---

## 1. 前端 GUI 優化

### 1.1 元件拆分與架構

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 1 | `vocabulary.jsx` 長達 **791 行**，處理搜尋、分頁、分類、影片播放、攝影機串流、手勢比對、進度追蹤等所有邏輯 | `my-app/src/pages/vocabulary.jsx` | 拆分為 `WordGrid`、`DemoVideoPlayer`、`CameraGestureMatch`、`CategoryFilter`、`ProgressTracker` 等子元件 |
| 2 | `chatBox.jsx` 約 **430 行**，同時處理聊天、API 呼叫、攝影機、GIF 序列顯示 | `my-app/src/pages/chatBox.jsx` | 將聊天邏輯抽離為 `useChatAPI` hook，GIF 顯示拆為 `SignSequenceDisplay` 元件 |
| 3 | `settings.jsx` 包含語言切換、密碼修改、登出等不同功能的混合 | `my-app/src/pages/settings.jsx` | 各設定區塊拆為獨立子元件 |

### 1.2 效能問題

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 4 | `HAND_CONNECTIONS` 常數陣列定義在元件**內部**，導致每次渲染都重新建立，並造成 `useCallback` 依賴鏈失效 | `vocabulary.jsx` | 移至元件外部或獨立 `constants.js` |
| 5 | 手勢偵測使用 `setInterval` 輪詢（vocabulary 為 3 秒、chatBox 為 250ms），效率低且不一致 | `vocabulary.jsx`、`chatBox.jsx` | 改用 WebSocket 或 Server-Sent Events 取代輪詢；統一輪詢間隔 |
| 6 | 影片 `<video>` 元素在詞彙卡片中可能大量同時渲染 | `vocabulary.jsx` | 使用懶載入（Intersection Observer）或虛擬捲軸（react-window） |
| 7 | 搜尋使用即時 `filter()`，無防抖（debounce） | `vocabulary.jsx` | 加入 300ms debounce 減少不必要的重新渲染 |
| 8 | CSS 全域樣式（如 `chatBox.css`、`vocabulary.css`）可能造成命名衝突 | 各 `.css` 檔案 | 改用 CSS Modules 或 styled-components |

### 1.3 安全性問題

| # | 問題 | 檔案 | 嚴重程度 |
|---|------|------|----------|
| 9 | **NVIDIA API Key** 硬編碼在 `.env` 中（`REACT_APP_` 前綴會被打包進前端 bundle） | `my-app/.env` | 🔴 嚴重 — 任何人可從瀏覽器 DevTools 取得 API Key |
| 10 | 登入認證僅依賴 `localStorage` 存取，無 token 過期機制 | `auth.jsx`、`App.js` | 🟡 中等 — 應改用 JWT + refresh token |
| 11 | `uuid` 套件在 `chatBox.jsx` 中被引用但未列在 `package.json` 依賴中 | `chatBox.jsx`、`package.json` | 🟡 中等 — 可能在不同環境安裝失敗 |

### 1.4 UX 改善

| # | 問題 | 建議 |
|---|------|------|
| 12 | 聊天輸入框設為 `readOnly`，使用者無法自行輸入文字 | 開放手動輸入功能，手勢輸入與文字輸入並行 |
| 13 | 聊天記錄硬編碼初始歷史（"你好，請問你想學什麼手語？"） | 改為從 API 或 localStorage 載入歷史 |
| 14 | 離線指示中包含 macOS 路徑（`/opt/homebrew/...`）但目標平台為 Windows | 替換為 Windows 路徑或根據 `navigator.platform` 動態顯示 |
| 15 | 手勢比對成功僅顯示文字，無動畫或音效回饋 | 加入成功動畫（confetti / 脈動效果）和可選音效 |
| 16 | 無載入骨架屏（skeleton screen），API 等待時畫面空白 | 新增 Skeleton 元件提升感知載入速度 |

---

## 2. AI 訓練代碼優化

### 2.1 訓練 Notebook 架構

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 17 | `train_gru_sequence.ipynb` 與 `train_lstm_sequence.ipynb` **幾乎完全相同**（僅 GRU↔LSTM 一處差異） | 兩個 notebook | 合併為單一 notebook，透過參數選擇模型類型 |
| 18 | `train_gru_sequence_incremental.ipynb` 與上述 notebook 也大量重複 | incremental notebook | 提取共用函式至 `train_utils.py` 模組 |

### 2.2 模型訓練改善

| # | 問題 | 建議 |
|---|------|------|
| 19 | 無 **Learning Rate Scheduler** | 加入 `ReduceLROnPlateau` 或 `CosineDecay` 排程器 |
| 20 | 無**資料增強**（Data Augmentation） | 對關鍵點序列加入隨機縮放、平移、時間扭曲、雜訊注入 |
| 21 | 使用普通 `train_test_split`，無**分層抽樣** | 改用 `StratifiedShuffleSplit` 確保各類別比例一致 |
| 22 | 無**混淆矩陣**或 per-class 準確率報告 | 訓練完成後加入 `classification_report` 和 `confusion_matrix` 視覺化 |
| 23 | 未使用 **K-Fold 交叉驗證** | 對小型資料集加入 5-fold 或 10-fold 交叉驗證 |
| 24 | EarlyStopping 的 `patience` 設為 20，可能過早停止或過晚停止 | 根據資料集大小調整，建議搭配 `restore_best_weights=True` |
| 25 | 標籤索引有 **1-based / 0-based 不一致**（CSV 標籤從 1 開始，但 `np.argmax` 從 0 開始） | 統一索引方式，確保轉換正確 |

### 2.3 模型轉換

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 26 | TFLite 轉換使用 `Select TF Ops` 時路徑參考 `.so` 檔案（Linux），但訓練平台為 Windows | notebook 最後 cell | 修改為 `.dll` 路徑或使用自動偵測 |
| 27 | OpenVINO 轉換腳本 `convert_openvino_models.py` 無錯誤處理 | `tools/convert_openvino_models.py` | 加入 try-except 和日誌記錄 |

---

## 3. Python 後端 / 推論服務優化

### 3.1 代碼重複

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 28 | `app.py`（~1000 行）與 `app_simple.py`（~500 行）有**大量重複代碼**（手勢辨識邏輯、MediaPipe 初始化、關鍵點處理） | `app.py`、`app_simple.py` | 提取共用邏輯至 `gesture_engine.py` 模組，兩者共享 |

### 3.2 效能問題

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 29 | `app.py` 中字體在**每一幀**都重新載入（`ImageFont.truetype()`） | `app.py` | 移至初始化階段，全域載入一次 |
| 30 | `draw_landmarks` 函式有 **21 個完全相同的 if 分支**（每個手指節點一個） | `app.py` | 使用迴圈 + 節點分組字典替代 |
| 31 | `np.append` 在迴圈中使用（每次複製整個陣列，`O(n²)` 效能） | `app.py` | 改用 list append + 最後 `np.array()` 轉換 |
| 32 | `extract_face_features` 回傳 8 個特徵值但模型期望 10 個 | `app.py` | 修正特徵數量一致性 |
| 33 | `select_mode` 函式已定義但**未被引用** | `app.py` | 移除或正確整合 |

### 3.3 API 設計

| # | 問題 | 檔案 | 建議 |
|---|------|------|------|
| 34 | `/gesture` endpoint 不回傳前端期望的 `hands` 陣列 | `app_simple.py` | 修正 response schema 使前後端一致 |
| 35 | 使用 MJPEG 串流（HTTP long polling），高延遲 | `app_simple.py` | 改用 WebSocket 傳輸幀資料，或 WebRTC |
| 36 | CORS 設為 `allow_origins=["*"]` | `app_simple.py` | 限制為前端 origin（`http://localhost:3000`） |
| 37 | 無 API 版本管理 | `app_simple.py` | 加入 `/api/v1/` 前綴 |

---

## 4. PHP 後端 API 優化

### 4.1 安全性

| # | 問題 | 檔案 | 嚴重程度 |
|---|------|------|----------|
| 38 | 資料庫使用 **root 帳號且密碼為空** | 所有 `.php` 檔案 | 🔴 嚴重 — 建立專用帳號並設定強密碼 |
| 39 | 無 **CSRF 保護**和**速率限制** | 所有 `.php` 檔案 | 🔴 嚴重 — 加入 CSRF token 和每 IP 請求頻率限制 |
| 40 | `CORS` 設為 `Access-Control-Allow-Origin: *` | 所有 `.php` 檔案 | 🟡 中等 — 限制來源 |
| 41 | `login.php` 使用 `md5()` 雜湊密碼 | `login.php` | 🔴 嚴重 — 改用 `password_hash()` / `password_verify()` (bcrypt) |

### 4.2 架構問題

| # | 問題 | 建議 |
|---|------|------|
| 42 | 資料庫連線設定（host/user/pass/db）在每個 PHP 檔案中**重複定義** | 抽取為 `config.php` 或 `.env` 統一管理 |
| 43 | `words` 資料表使用 `VARCHAR` 作為主鍵 ID | 改用自增 `INT` 主鍵 |
| 44 | `user_progress` 無 `UNIQUE(user_id, word_id)` 約束 | 可能產生重複記錄，加入唯一約束 |
| 45 | 無統一的錯誤回應格式 | 定義 JSON 標準回應格式 `{ "success": bool, "data": ..., "error": ... }` |
| 46 | 無 API 路由框架 | 考慮使用 Slim Framework 或 Laravel Lumen 替代純 PHP |

---

## 5. 專案整體優化

### 5.1 開發環境

| # | 問題 | 建議 |
|---|------|------|
| 47 | Python 環境依賴 batch 腳本手動管理（`run-app-py310.bat` 等） | 使用 Docker Compose 統一開發環境 |
| 48 | CUDA/cuDNN 需手動安裝複製 | 製作 Docker GPU Image 或使用 conda 管理 CUDA toolkit |
| 49 | 無 `.gitignore` 規則（可能洩漏 `.env`、`__pycache__`、`node_modules`） | 確認 `.gitignore` 涵蓋所有敏感檔案和建構產物 |

### 5.2 CI/CD 與測試

| # | 問題 | 建議 |
|---|------|------|
| 50 | **零測試覆蓋率** — 前端無 Jest/RTL 測試，後端無 PHPUnit，Python 無 pytest | 至少為核心邏輯（手勢辨識、API 端點）加入單元測試 |
| 51 | 無 CI/CD 管線 | 加入 GitHub Actions：lint → test → build → deploy |
| 52 | 無程式碼風格規範 | 前端加入 ESLint + Prettier；Python 加入 black + flake8 |

### 5.3 文件與維護

| # | 問題 | 建議 |
|---|------|------|
| 53 | 前端缺乏 JSDoc / PropTypes / TypeScript 型別定義 | 為元件 props 加入 PropTypes 或遷移至 TypeScript |
| 54 | Python 函式缺乏 docstring | 為公開函式加入 Google-style docstring |
| 55 | API endpoint 無文件 | 使用 Swagger/OpenAPI 自動產生 API 文件（FastAPI 內建支援） |
| 56 | 環境變數和設定散佈在多個檔案、多種格式中 | 統一為 `.env` + 設定模組載入模式 |

---

## 優先排序建議

### 🔴 立即修復（安全性）
1. **#9** — 移除前端 bundle 中的 API Key，改由後端 proxy 轉發
2. **#38** — 資料庫移除 root 空密碼
3. **#41** — 密碼雜湊從 md5 改為 bcrypt
4. **#39** — 加入 CSRF 和速率限制

### 🟠 短期改善（效能 & 品質）
5. **#28** — 合併 app.py / app_simple.py 重複代碼
6. **#17** — 合併 GRU/LSTM notebook
7. **#4** — 修正 HAND_CONNECTIONS 位置
8. **#29** — 修正逐幀字體載入

### 🟡 中期優化（架構 & UX）
9. **#1** — vocabulary.jsx 元件拆分
10. **#5** — 輪詢改 WebSocket
11. **#19-23** — 訓練管線改善
12. **#42-46** — PHP 後端重構

### 🟢 長期目標
13. **#47-48** — Docker 化
14. **#50-52** — 測試和 CI/CD
15. **#53-56** — 文件完善

---

*本報告由 GitHub Copilot 根據全專案代碼審查生成。*
