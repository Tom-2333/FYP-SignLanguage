import React, { useState, useRef, useEffect } from 'react'
import { FaChevronRight, FaTrashAlt, FaCamera, FaKeyboard, FaSearch, FaHistory } from 'react-icons/fa'
import { v4 as uuidv4 } from 'uuid'

export default function ChatBox() {
  const videoRef = useRef(null)
  const [input, setInput] = useState('')
  const [isCamOpen, setIsCamOpen] = useState(false)
  const [detectedText, setDetectedText] = useState('等待手語信號...') 
  
  // 左側手語轉換歷史 (對應圖三左側)
  const [history, setHistory] = useState([
    { id: '1', text: '我上課', time: '10:30' },
    { id: '2', text: '謝謝你', time: '09:15' }
  ])

  useEffect(() => {
    let stream = null
    if (isCamOpen) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(s => {
          stream = s
          if (videoRef.current) videoRef.current.srcObject = s
          setDetectedText("正在辨識手勢...")
        })
    }
    return () => stream?.getTracks().forEach(t => t.stop())
  }, [isCamOpen])

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    const newEntry = { id: uuidv4(), text: input, time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }
    setHistory([newEntry, ...history])
    setInput('')
  }

  return (
    <div className="chat-app">
      {/* 1. 左側手語紀錄欄 */}
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <div className="search-bar">
            <FaSearch />
            <input type="text" placeholder="搜尋歷史紀錄..." />
          </div>
        </div>
        <div className="history-container">
          <div className="history-label"><FaHistory /> 轉換紀錄</div>
          {history.map(item => (
            <div key={item.id} className="history-card" onClick={() => setInput(item.text)}>
              <div className="history-info">
                <span className="history-text">{item.text}</span>
                <span className="history-time">{item.time}</span>
              </div>
              <FaTrashAlt className="del-btn" />
            </div>
          ))}
        </div>
      </aside>

      {/* 2. 右側主內容區 */}
      <main className="app-main">
        <header className="main-nav">GPT-Sign-Language 助手</header>

        <div className="chat-messages">
          {/* 訊息流區塊 */}
        </div>

        {/* 圖三核心優化：視覺反饋區 */}
        <section className="sign-visual-section">
          
          {/* 【關鍵修改】：高度 x3 的輸出 Bar，用來放置多個 GIF 框 */}
          <div className="sign-status-bar x3-height">
            {isCamOpen ? (
              <span className="blinking">● {detectedText}</span>
            ) : (
              <div className="gif-sequence-wrapper">
                {input ? (
                  <div className="gif-flex-container">
                    {/* 這裡對應圖三底部的 gif1 + gif2 -> entire gif 邏輯 */}
                    {input.split('').map((char, i) => (
                      <div key={i} className="gif-box-unit">
                        <div className="gif-placeholder-img">GIF</div>
                        <span className="gif-label">{char}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="placeholder-text">請輸入文字，此處將顯示手語 GIF 序列</span>
                )}
              </div>
            )}
          </div>

          {/* 相機框保持正常比例 */}
          <div className="main-display-box">
            {isCamOpen ? (
              <video ref={videoRef} autoPlay playsInline className="video-stream" />
            ) : (
              <div className="empty-visual">
                <p>相機已關閉</p>
                <small>點擊下方相機圖標開啟實時辨識</small>
              </div>
            )}
          </div>
        </section>

        {/* 底部輸入控制 */}
        <footer className="control-footer">
          <form className="main-input-group" onSubmit={handleSend}>
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isCamOpen ? "相機模式辨識中..." : "請在此輸入文字..."}
              disabled={isCamOpen}
            />
            <button type="submit" className="icon-btn send-btn" disabled={!input}>
              <FaChevronRight />
            </button>
          </form>
          
          <button 
            className={`mode-toggle-btn ${isCamOpen ? 'cam-active' : ''}`}
            onClick={() => setIsCamOpen(!isCamOpen)}
          >
            {isCamOpen ? <FaKeyboard /> : <FaCamera />}
          </button>
        </footer>
      </main>

      <style jsx>{`
        .chat-app { display: flex; height: 100vh; width: 100vw; overflow: hidden; font-family: sans-serif; background: #fff; }
        
        /* Sidebar 樣式 */
        .app-sidebar { width: 300px; background: #f7f7f8; border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px 15px; }
        .search-bar { display: flex; align-items: center; background: white; padding: 10px 15px; border-radius: 8px; border: 1px solid #eee; }
        .search-bar input { border: none; outline: none; margin-left: 10px; width: 100%; }
        .history-container { flex: 1; overflow-y: auto; padding: 10px; }
        .history-label { font-size: 13px; color: #888; margin-bottom: 12px; font-weight: bold; }
        .history-card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border: 1px solid #eee; }
        .history-card:hover { border-color: #10a37f; }

        .app-main { flex: 1; display: flex; flex-direction: column; }
        .main-nav { padding: 15px 25px; border-bottom: 1px solid #eee; font-weight: bold; }
        .chat-messages { flex: 1; }

        /* 視覺反饋區 */
        .sign-visual-section { padding: 20px; background: #fff; display: flex; flex-direction: column; gap: 15px; }
        
        /* 【關鍵】加高 3 倍的 Bar */
        .sign-status-bar.x3-height { 
          width: 100%; 
          height: 180px; /* 原本約 60px，現在加高到 180px */
          background: #f9f9f9; 
          border: 2px solid #10a37f; 
          border-radius: 15px; 
          display: flex; 
          align-items: center; 
          justify-content: center;
          overflow-x: auto; /* 文字太長時可以橫向捲動 GIF */
          padding: 10px;
        }

        /* GIF 序列排版 */
        .gif-flex-container { display: flex; gap: 15px; padding: 0 10px; }
        .gif-box-unit { display: flex; flex-direction: column; align-items: center; gap: 5px; }
        .gif-placeholder-img { 
          width: 120px; height: 120px; background: #ddd; 
          border-radius: 8px; display: flex; align-items: center; 
          justify-content: center; font-size: 12px; font-weight: bold; color: #666;
        }
        .gif-label { font-size: 14px; font-weight: bold; color: #10a37f; }

        /* 相機展示框比例正常 */
        .main-display-box { 
          width: 100%; height: 350px; background: #1a1a1a; border-radius: 15px; 
          overflow: hidden; display: flex; justify-content: center; align-items: center;
        }
        .video-stream { width: 100%; height: 100%; object-fit: cover; }
        .empty-visual { color: #555; text-align: center; }

        /* 底部輸入控制 */
        .control-footer { padding: 20px; display: flex; gap: 15px; align-items: center; border-top: 1px solid #eee; }
        .main-input-group { flex: 1; background: #f0f0f0; border-radius: 25px; display: flex; padding: 5px 20px; align-items: center; }
        .main-input-group input { flex: 1; border: none; outline: none; background: transparent; padding: 10px; }
        .mode-toggle-btn { width: 50px; height: 50px; border-radius: 15px; border: none; background: #f0f0f0; cursor: pointer; font-size: 20px; }
        .mode-toggle-btn.cam-active { background: #10a37f; color: white; }
        .blinking { color: #ff4d4f; animation: blinker 1.5s linear infinite; }
        @keyframes blinker { 50% { opacity: 0; } }
      `}</style>
    </div>
  )
}