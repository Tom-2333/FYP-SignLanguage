import React, { useState, useRef, useEffect } from 'react'
import { FaChevronRight, FaTrashAlt, FaCamera, FaKeyboard, FaSearch, FaHistory } from 'react-icons/fa'
import { v4 as uuidv4 } from 'uuid'
import './chatBox.css'

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
    </div>
  )
}