// src/pages/chatBox.jsx
import React, { useState, useRef, useEffect } from 'react'
import { FaRobot, FaChevronRight, FaTrashAlt } from 'react-icons/fa'
import { v4 as uuidv4 } from 'uuid'

export default function ChatBox() {
  const inputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const replyTimeoutRef = useRef(null)

  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  const [chatHistory, setChatHistory] = useState([
    {
      id: uuidv4(),
      title: '2025/10/10 測試對話',
      createdAt: new Date('2025-10-10'),
      updatedAt: new Date('2025-10-10'),
      messages: [
        { id: uuidv4(), role: 'assistant', text: '這是歷史訊息範例。' }
      ]
    },
    {
      id: uuidv4(),
      title: '2025/10/12 另一個對話',
      createdAt: new Date('2025-10-12'),
      updatedAt: new Date('2025-10-12'),
      messages: [
        { id: uuidv4(), role: 'assistant', text: '歡迎回來！' }
      ]
    }
  ])

  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // 滾動到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    return () => {
      if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current)
    }
  }, [])

  useEffect(() => {
    if (activeChatId) {
      const chat = chatHistory.find(c => c.id === activeChatId)
      if (chat) setMessages(chat.messages)
    } else {
      setMessages([])
    }
  }, [activeChatId, chatHistory])

  function sendMessage(text) {
    const trimmed = String(text || '').trim()
    if (!trimmed) return
    setError(null)
    setLoading(true)

    const userMsg = { id: uuidv4(), role: 'user', text: trimmed }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')

    if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current)
    replyTimeoutRef.current = setTimeout(() => {
      try {
        const reply = `已收到您的訊息：「${trimmed}」。這是一個範例回覆（模擬）。`
        const assistantMsg = { id: uuidv4(), role: 'assistant', text: reply }
        const updatedMessages = [...newMessages, assistantMsg]
        setMessages(updatedMessages)
        setLoading(false)
        setIsTyping(false)

        if (activeChatId) {
          setChatHistory(chats => chats.map(c => {
            if (c.id === activeChatId) {
              return {
                ...c,
                messages: updatedMessages,
                updatedAt: new Date()
              }
            }
            return c
          }))
        } else {
          const newChat = {
            id: uuidv4(),
            title: `新聊天 ${new Date().toLocaleString()}`,
            createdAt: new Date(),
            updatedAt: new Date(),
            messages: updatedMessages
          }
          setChatHistory(chats => [newChat, ...chats])
          setActiveChatId(newChat.id)
        }
      } catch (e) {
        setError('回覆出錯，請稍後再試。')
        setLoading(false)
        setIsTyping(false)
      }
    }, 800)

    setIsTyping(true)
  }

  function handleSubmit(e) {
    e.preventDefault()
    sendMessage(input)
  }

  function handleToggleSidebar() {
    setSidebarOpen(open => !open)
  }

  function handleNewChat() {
    setActiveChatId(null)
    setMessages([])
    setInput('')
    setSidebarOpen(false)
    inputRef.current?.focus()
  }

  function handleLoadHistory(chatId) {
    setActiveChatId(chatId)
    setSidebarOpen(false)
  }

  function handleDeleteChat(chatId) {
    if (!window.confirm('確定要刪除此聊天紀錄？此操作無法復原。')) return
    setChatHistory(chats => chats.filter(c => c.id !== chatId))
    if (activeChatId === chatId) {
      setActiveChatId(null)
      setMessages([])
    }
  }

  return (
    <div className="chatgpt-bg chatgpt-full" role="main" aria-label="聊天介面">
      
      {/* Sidebar */}
      <aside
        className={`chat-sidebar ${sidebarOpen ? 'open' : 'closed'}`}
        aria-label="聊天歷史側邊欄"
        aria-hidden={!sidebarOpen}
      >
        <button
          className="new-chat-btn"
          onClick={handleNewChat}
          aria-label="新增聊天"
        >
          新增聊天
        </button>

        <div className="chat-history-title">聊天歷史</div>

        <div
          className="chat-history-list"
          tabIndex={0}
          aria-label="聊天歷史列表"
        >
          {chatHistory.length === 0 ? (
            <div className="empty-history">尚無聊天紀錄</div>
          ) : (
            chatHistory.map(chat => (
              <div
                key={chat.id}
                role="button"
                tabIndex={0}
                aria-pressed={activeChatId === chat.id}
                className={`chat-history-item ${activeChatId === chat.id ? 'selected' : ''}`}
                onClick={() => handleLoadHistory(chat.id)}
                onKeyDown={e => { if (e.key === 'Enter') handleLoadHistory(chat.id) }}
              >
                <span className="chat-title">{chat.title}</span>
                <button
                  aria-label={`刪除聊天紀錄: ${chat.title}`}
                  onClick={e => {
                    e.stopPropagation()
                    handleDeleteChat(chat.id)
                  }}
                  className="delete-chat-btn"
                >
                  <FaTrashAlt />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* 遮罩 */}
      {sidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* 主內容區 */}
      <main className="chatgpt-main chatgpt-main-fixed">
        {/* Model Card */}
        <section className="model-card" aria-hidden="false">
          <div className="model-card-top">
            <div className="model-card-title">
              <div className="model-icon" aria-hidden="true">
                <FaRobot />
              </div>
              <div>
                <strong>GPT-Sign-Language</strong>
                <div className="muted" style={{ marginTop: 6 }}>
                  GPT-Sign-Language 是一個手語對話機器人。
                </div>
              </div>
            </div>
          </div>

          <div className="model-card-actions">
            <span
              className="tag"
              role="button"
              tabIndex={0}
              aria-pressed={sidebarOpen}
              onClick={handleToggleSidebar}
              onKeyDown={e => { if (e.key === 'Enter') handleToggleSidebar() }}
            >
              歷史紀錄
            </span>
            <span
              className="tag"
              role="button"
              tabIndex={0}
              onClick={handleNewChat}
              onKeyDown={e => { if (e.key === 'Enter') handleNewChat() }}
            >
              + 新訊息
            </span>
          </div>
        </section>

        {/* 訊息區 */}
        <div
          className="messages messages-scroll"
          role="log"
          aria-live="polite"
          aria-relevant="additions"
          tabIndex={-1}
        >
          {messages.length === 0 && !loading && (
            <div className="empty-message">尚無聊天訊息，請開始新的對話。</div>
          )}

          {messages.map(m => (
            <div key={m.id} className={`message ${m.role === 'user' ? 'user' : 'assistant'}`}>
              <div className="msg-avatar" aria-hidden="true">
                {m.role === 'assistant' ? <FaRobot /> : '您'}
              </div>
              <div className={`msg-content msg-content-${m.role}`}>{m.text}</div>
            </div>
          ))}

          {isTyping && (
            <div className="message assistant typing">
              <div className="msg-avatar" aria-hidden="true">
                <FaRobot />
              </div>
              <div className="msg-content typing-dots" aria-hidden="true">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 輸入框 */}
        {!sidebarOpen && (
          <form
            className="chatgpt-input-bar chatgpt-input-fixed"
            onSubmit={handleSubmit}
            aria-label="輸入訊息"
          >
            <input
              ref={inputRef}
              className="chatgpt-input"
              type="text"
              placeholder="輸入訊息..."
              value={input}
              onChange={e => setInput(e.target.value)}
              autoFocus
              aria-label="輸入訊息"
              disabled={loading}
            />
            <button
              className="chatgpt-send-btn"
              type="submit"
              aria-label="送出"
              disabled={loading || input.trim() === ''}
            >
              <FaChevronRight />
            </button>
          </form>
        )}

        {error && (
          <div
            role="alert"
            className="error-alert"
          >
            {error}
          </div>
        )}
      </main>
    </div>
  )
}