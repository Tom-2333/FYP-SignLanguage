import React, { useState, useEffect } from 'react'
import { FaChevronRight, FaCamera, FaKeyboard, FaSearch, FaHistory } from 'react-icons/fa'
import { v4 as uuidv4 } from 'uuid'
import { signLanguagePrompt } from './prompt.js'
import { useLanguage } from '../contexts/LanguageContext'
import './chatBox.css'

export default function ChatBox() {
  const apiBase = process.env.REACT_APP_GESTURE_API || 'http://127.0.0.1:5001'
  const dbApiBase = process.env.REACT_APP_SLDB_API_BASE || 'http://localhost/SL-Database_api'
  const { language, setLanguage, t } = useLanguage()
  const normalizeSldbUrl = (path) => {
    if (!path) return null
    try {
      return new URL(path, `${dbApiBase.replace(/\/$/, '')}/`).href
    } catch (error) {
      return path
    }
  }
  const [input, setInput] = useState('')
  const [isCamOpen, setIsCamOpen] = useState(false)
  const [detectedText, setDetectedText] = useState(t('chat.detectedWaiting'))
  const [messages, setMessages] = useState([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [genError, setGenError] = useState('')
  const [selectedWords, setSelectedWords] = useState([])
  const [signWords, setSignWords] = useState([])
  const [signWordImages, setSignWordImages] = useState([])
  const [isWebpPanelOpen, setIsWebpPanelOpen] = useState(false)
  const [streamFrameUrl, setStreamFrameUrl] = useState('')
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('fontSize') || '100%')
  const [colorMode, setColorMode] = useState(() => localStorage.getItem('colorMode') || 'light')
  const [sessionSearch, setSessionSearch] = useState('')
  const [sessions, setSessions] = useState([])
  const [selectedSessionId, setSelectedSessionId] = useState(null)

  const chatTexts = {
    newSession: language === 'zh' ? '新對話' : 'New Session',
    sessionFallback: language === 'zh' ? '對話' : 'Session',
    generateSentence: language === 'zh' ? '生成手語句子' : 'Generate Sign-language Sentence',
    continueGenerateSentence: language === 'zh' ? '繼續生成手語句子' : 'Continue Generate Sign-language Sentence',
    showWebp: language === 'zh' ? '顯示手語圖示' : 'Show WebP Display',
    hideWebp: language === 'zh' ? '隱藏手語圖示' : 'Hide WebP Display',
    detectedPrefix: language === 'zh' ? '偵測到：' : 'Detected:'
  }

  const extractSessionTopic = (rawText) => {
    if (!rawText || typeof rawText !== 'string') return ''
    const firstNonEmptyLine = rawText
      .split('\n')
      .map((line) => line.trim())
      .find((line) => line.length > 0) || ''

    const cleaned = firstNonEmptyLine
      .replace(/^手語表達[:：]\s*/i, '')
      .replace(/^sign\s*expression[:：]\s*/i, '')
      .replace(/^topic[:：]\s*/i, '')
      .replace(/^主題[:：]\s*/i, '')
      .replace(/\s+/g, ' ')
      .trim()

    if (!cleaned) return ''
    return cleaned.length > 38 ? `${cleaned.slice(0, 38)}...` : cleaned
  }

  const [chatSessionId, setChatSessionId] = useState(() => {
    const existing = localStorage.getItem('chatSessionId')
    if (existing) return existing
    const generated = uuidv4()
    localStorage.setItem('chatSessionId', generated)
    return generated
  })

  useEffect(() => {
    if (!isCamOpen) return
    let stopped = false
    let reconnectTimer = null
    let socket = null

    const wsBase = apiBase.replace(/^http/i, 'ws')
    const wsUrl = `${wsBase}/api/v1/ws/gesture`

    const connect = () => {
      if (stopped) return
      socket = new WebSocket(wsUrl)

      socket.onmessage = (event) => {
        if (stopped) return
        try {
          const payload = JSON.parse(event.data)
          const data = payload?.gesture || {}
          const sequenceText = (data?.sequence_gesture_text || '').trim()
          const handText = (data?.hand_sign_text || '').trim()
          const fingerText = (data?.finger_gesture_text || '').trim()
          const bestText = sequenceText || handText || fingerText

          if (bestText) {
            setInput(bestText)
            setDetectedText(`${chatTexts.detectedPrefix} ${bestText}`)
          } else {
            setDetectedText(t('chat.recognizing'))
          }

          if (payload?.frame_data_url) {
            setStreamFrameUrl(payload.frame_data_url)
          }
        } catch (err) {
          console.error('Invalid gesture payload:', err)
        }
      }

      socket.onerror = () => {
        if (!stopped) setDetectedText(t('chat.serverNotReachable'))
      }

      socket.onclose = () => {
        if (!stopped) reconnectTimer = setTimeout(connect, 1200)
      }
    }

    connect()

    return () => {
      stopped = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (socket) socket.close()
    }
  }, [isCamOpen, apiBase, t, chatTexts.detectedPrefix])

  const regenerateSelectedWords = async () => {
    try {
      const response = await fetch('/keypoint_sequence_classifier_label.csv')
      const csvText = await response.text()
      const words = csvText.trim().split('\n').filter(word => word.trim())
      if (words.length < 4) return
      const shuffled = words.sort(() => 0.5 - Math.random())
      const selectedWords = shuffled.slice(0, 4)
      setSelectedWords(selectedWords)
      setSignWords(selectedWords)
      const vocabList = words.join(', ')
      const prompt = signLanguagePrompt.replace('詞彙文件「keypoint_sequence_classifier_label.csv」內容（所有詞彙必須來自此列表，不能添加外部詞彙）', `詞彙文件「keypoint_sequence_classifier_label.csv」內容（所有詞彙必須來自此列表，不能添加外部詞彙）：${vocabList}`)
      await generateGeminiReply(prompt)
    } catch (error) {
      console.error('Error loading words:', error)
    }
  }

  useEffect(() => {
    // Apply color mode from localStorage
    const savedColorMode = localStorage.getItem('colorMode') || 'light'
    setColorMode(savedColorMode)
    if (savedColorMode === 'dark') {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }

    // Apply RG-CVD mode
    const savedRgCvdMode = localStorage.getItem('rgCvdMode') === 'true'
    if (savedRgCvdMode) {
      document.body.classList.add('rg-cvd-mode')
    } else {
      document.body.classList.remove('rg-cvd-mode')
    }
  }, [])

  useEffect(() => {
    if (!signWords || signWords.length === 0) {
      setSignWordImages([])
      return
    }

    const fetchImages = async () => {
      try {
        const resp = await fetch(`${dbApiBase}/get_webp_for_words.php`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ words: signWords })
        })
        const data = await resp.json()
        if (data.success && data.mapping) {
          const imgs = signWords.map((word) => ({ word, src: normalizeSldbUrl(data.mapping[word]) }))
          setSignWordImages(imgs)
        } else {
          setSignWordImages(signWords.map((word) => ({ word, src: null })))
        }
      } catch (err) {
        console.error('Failed to fetch webp mapping:', err)
        setSignWordImages(signWords.map((word) => ({ word, src: null })))
      }
    }

    fetchImages()
  }, [signWords, dbApiBase])

  const mapSession = (session) => ({
    id: session.session_id,
    text: extractSessionTopic(session.first_message || session.last_message || ''),
    time: session.last_timestamp,
    count: session.message_count
  })

  const fetchMessagesForSession = async (sessionId) => {
    const userId = localStorage.getItem('userId')
    if (!userId || !sessionId) return

    try {
      const resp = await fetch(
        `${dbApiBase}/get_chat_history.php?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}&limit=500`
      )
      const data = await resp.json()
      if (data.success && Array.isArray(data.messages)) {
        const ordered = data.messages.slice().reverse().map((item) => ({
          id: item.id || uuidv4(),
          role: item.role,
          text: item.message
        }))
        setMessages(ordered)
      }
    } catch (err) {
      console.error('Failed to load messages for session:', err)
    }
  }

  const refreshSessions = async (autoSelect = false) => {
    const userId = localStorage.getItem('userId')
    if (!userId) return

    try {
      const resp = await fetch(`${dbApiBase}/get_chat_sessions.php?user_id=${encodeURIComponent(userId)}&limit=50`)
      const data = await resp.json()
      if (!data.success || !Array.isArray(data.sessions)) return

      const mapped = data.sessions.map(mapSession)
      setSessions(mapped)

      if (autoSelect && mapped.length > 0) {
        const preferred = mapped.find((item) => item.id === chatSessionId)
        const target = preferred || mapped[0]
        setSelectedSessionId(target.id)
        setChatSessionId(target.id)
        localStorage.setItem('chatSessionId', target.id)
        fetchMessagesForSession(target.id)
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err)
    }
  }

  useEffect(() => {
    refreshSessions(true)
  }, [])

  useEffect(() => {
    if (isCamOpen) return
    const expected = selectedWords.join(' ').trim()
    if (!expected) return
    if (input.trim() === expected) {
      regenerateSelectedWords()
    }
  }, [input, selectedWords, isCamOpen])

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    const expected = selectedWords.join(' ').trim()
    if (!expected || input.trim() !== expected) return

    const userText = input.trim()
    setMessages(prev => ([...prev, { id: uuidv4(), role: 'user', text: userText }]))
    saveChatToDb(userText, 'user')
    setInput('')
    generateGeminiReply(userText)
  }

  const parseSignWordsFromReply = (reply) => {
    const lines = reply.split('\n')
    const signLine = lines.find((line) => line.trim().startsWith('手語表達：'))
    if (!signLine) return []
    return signLine.replace('手語表達：', '').trim().split(' ').filter((word) => word.trim())
  }

  const generateGeminiReply = async (promptText) => {
    if (isCamOpen) return

    setGenError('')
    setIsGenerating(true)

    try {
      let reply = ''
      const poeApiKey = process.env.REACT_APP_POE_API_KEY

      if (poeApiKey) {
        const poeModel = process.env.REACT_APP_POE_MODEL || 'grok-4.1-fast-reasoning'
        const resp = await fetch('https://api.poe.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${poeApiKey}`
          },
          body: JSON.stringify({
            model: poeModel,
            messages: [{ role: 'user', content: promptText }],
            temperature: 0.7,
            max_tokens: 200
          })
        })

        if (!resp.ok) {
          const errText = await resp.text()
          if (resp.status === 401 || resp.status === 403) {
            throw new Error('Unauthorized. Please check Poe API key/model access.')
          }
          if (resp.status === 429) {
            throw new Error('Rate limited. Please wait and try again.')
          }
          throw new Error(errText || `Poe API Error (${resp.status})`)
        }

        const data = await resp.json()
        reply = data?.choices?.[0]?.message?.content?.trim() || '(No reply)'
      } else {
        const grokUrl = process.env.REACT_APP_GROK_API_URL || '/api/grok/ask'
        const grokModel = process.env.REACT_APP_GROK_MODEL || 'grok-3-fast'
        const grokProxy = process.env.REACT_APP_GROK_PROXY || ''

        const resp = await fetch(grokUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: promptText,
            model: grokModel,
            proxy: grokProxy
          })
        })

        if (!resp.ok) {
          let errText = ''
          try { errText = await resp.text() } catch (_) { }
          if (resp.status === 429) {
            throw new Error('Rate limited. Please wait and try again.')
          }

          let detail = ''
          try {
            const errJson = JSON.parse(errText)
            detail = errJson?.detail || errJson?.error?.message || errJson?.message || ''
          } catch (_) {
            detail = errText?.substring(0, 200) || ''
          }

          throw new Error(`Grok API Error (${resp.status}): ${detail || 'Unknown error'}`)
        }

        const data = await resp.json()
        reply = (data?.response || data?.message || data?.choices?.[0]?.message?.content || '').trim() || '(No reply)'
      }

      const parsedSignWords = parseSignWordsFromReply(reply)
      if (parsedSignWords.length > 0) {
        setSignWords(parsedSignWords)
      }

      setMessages(prev => ([...prev, { id: uuidv4(), role: 'assistant', text: reply }]))
      saveChatToDb(reply, 'assistant')
    } catch (err) {
      console.error('Generation error:', err)
      setGenError(`Generation failed: ${err.message || 'please try again later'}`)
    } finally {
      setIsGenerating(false)
    }
  }

  const saveChatToDb = async (message, role) => {
    try {
      const userId = localStorage.getItem('userId')
      if (!userId) return

      await fetch(`${dbApiBase}/save_chat.php`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: parseInt(userId, 10),
          session_id: chatSessionId,
          message,
          role
        })
      })

      refreshSessions(false)
    } catch (err) {
      console.error('Failed to save chat:', err)
    }
  }

  const createNewSession = () => {
    const generated = uuidv4()
    localStorage.setItem('chatSessionId', generated)
    setChatSessionId(generated)
    setSelectedSessionId(generated)
    setMessages([])
    setSignWords([])
    setSignWordImages([])
  }

  const handleClickMessage = (message) => {
    if (!message?.text) return
    const parsedSignWords = parseSignWordsFromReply(message.text)
    if (parsedSignWords.length > 0) {
      setSignWords(parsedSignWords)
      return
    }

    const fallbackWords = message.text
      .replace(/\s+/g, ' ')
      .trim()
      .split(' ')
      .filter((word) => word.trim())
    if (fallbackWords.length > 0) {
      setSignWords(fallbackWords)
    }
  }

  const filteredSessions = sessions.filter((item) => {
    const keyword = sessionSearch.trim().toLowerCase()
    if (!keyword) return true
    return (`${item.text || ''} ${item.time || ''}`).toLowerCase().includes(keyword)
  })

  const handleGenerateSentence = () => {
    if (isGenerating || isCamOpen) return
    regenerateSelectedWords()
  }

  const hasConversation = messages.length > 0
  const generateButtonText = hasConversation ? chatTexts.continueGenerateSentence : chatTexts.generateSentence
  const selectedSession = sessions.find((item) => item.id === selectedSessionId)
  const liveTopic = extractSessionTopic(messages[0]?.text || '')
  const currentTopicTitle = selectedSession?.text || liveTopic || chatTexts.newSession

  return (
    <div className={`chat-app ${fontSize === '90%' ? 'font-size-90' : fontSize === '125%' ? 'font-size-125' : 'font-size-100'}`}>
      {/* 1. Left side sign language history panel */}
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <div className="search-bar">
            <FaSearch />
            <input
              type="text"
              placeholder={t('chat.searchHistory')}
              value={sessionSearch}
              onChange={(e) => setSessionSearch(e.target.value)}
            />
          </div>
        </div>
        <div className="history-container">
          <div className="history-label"><FaHistory /> {t('chat.conversionHistory')}</div>
          <div className="new-session-row">
            <button type="button" className="new-session-btn" onClick={createNewSession}>{chatTexts.newSession}</button>
          </div>

          {filteredSessions.map(item => (
            <div
              key={item.id}
              className={`history-card ${item.id === selectedSessionId ? 'active-session' : ''}`}
              onClick={() => {
                setSelectedSessionId(item.id)
                setChatSessionId(item.id)
                localStorage.setItem('chatSessionId', item.id)
                fetchMessagesForSession(item.id)
              }}
            >
              <div className="history-info">
                <span className="history-text">{item.text || chatTexts.sessionFallback}</span>
                <span className="history-time">{item.time}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* 2. 右側主內容區 */}
      <main className="app-main">
        <header className="main-nav">
          <span>{currentTopicTitle}</span>
          <div className="header-controls">
            <div className="chat-language-toggle" role="group" aria-label="Language selector">
              <span className="chat-language-icon" aria-hidden>🌐</span>
              <button
                type="button"
                className={`chat-language-btn ${language === 'zh' ? 'active' : ''}`}
                onClick={() => setLanguage('zh')}
              >
                粵
              </button>
              <span className="chat-language-divider">|</span>
              <button
                type="button"
                className={`chat-language-btn ${language === 'en' ? 'active' : ''}`}
                onClick={() => setLanguage('en')}
              >
                Eng
              </button>
            </div>
            <div className="font-size-controls">
              <button
                type="button"
                className={`font-size-btn size-small ${fontSize === '90%' ? 'active' : ''}`}
                onClick={() => {
                  setFontSize('90%')
                  localStorage.setItem('fontSize', '90%')
                }}
                title="Small (90%)"
              >
                aa
              </button>
              <button
                type="button"
                className={`font-size-btn size-normal ${fontSize === '100%' ? 'active' : ''}`}
                onClick={() => {
                  setFontSize('100%')
                  localStorage.setItem('fontSize', '100%')
                }}
                title="Normal (100%)"
              >
                Aa
              </button>
              <button
                type="button"
                className={`font-size-btn size-large ${fontSize === '125%' ? 'active' : ''}`}
                onClick={() => {
                  setFontSize('125%')
                  localStorage.setItem('fontSize', '125%')
                }}
                title="Large (125%)"
              >
                AA
              </button>
            </div>
            <button
              type="button"
              className="theme-toggle"
              onClick={() => {
                const nextMode = colorMode === 'light' ? 'dark' : 'light'
                setColorMode(nextMode)
                localStorage.setItem('colorMode', nextMode)
                if (nextMode === 'dark') {
                  document.body.classList.add('dark-mode')
                } else {
                  document.body.classList.remove('dark-mode')
                }
              }}
              aria-label={colorMode === 'light' ? t('vocab.switchDarkMode') : t('vocab.switchLightMode')}
              title={colorMode === 'light' ? t('vocab.darkMode') : t('vocab.lightMode')}
            >
              {colorMode === 'light' ? '🌙' : '☀️'}
            </button>
          </div>
        </header>

        <div className="sentence-generator-row">
          <button
            type="button"
            className="sentence-generator-btn"
            onClick={handleGenerateSentence}
            disabled={isGenerating || isCamOpen}
          >
            {generateButtonText}
          </button>
          <button
            type="button"
            className="webp-toggle-btn"
            onClick={() => setIsWebpPanelOpen((prev) => !prev)}
          >
            {isWebpPanelOpen ? chatTexts.hideWebp : chatTexts.showWebp}
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, idx) => {
            return (
              <div key={msg.id} className={`chat-row ${msg.role === 'user' ? 'user-row' : ''}`}>
                <div
                  className={`chat-bubble ${msg.role} ${msg.role === 'assistant' ? 'clickable' : ''}`}
                  onClick={() => handleClickMessage(msg)}
                >
                  {msg.text}
                </div>
              </div>
            )
          })}
          {isGenerating && (
            <div className="chat-row">
              <div className="chat-bubble assistant">{t('chat.generating')}</div>
            </div>
          )}
          {genError && (
            <div className="chat-error">{genError}</div>
          )}
        </div>

        {/* Figure 3 core optimization: visual feedback area */}
        <section className="sign-visual-section">

          {isWebpPanelOpen && (
            <div className="sign-status-bar x3-height">
              <div className="gif-sequence-wrapper">
                {isGenerating ? (
                  <span className="placeholder-text">{t('chat.waiting')}</span>
                ) : input && input.trim() === selectedWords.join(' ').trim() ? (
                  <div className="gif-flex-container">
                    {input.split(' ').map((word, i) => {
                      const matched = signWordImages.find((item) => item.word === word)
                      return (
                        <div key={i} className="gif-box-unit">
                          {matched?.src ? (
                            <img
                              className="gif-thumb"
                              src={matched.src}
                              alt={word}
                            />
                          ) : (
                            <div className="gif-placeholder-img">WEBP</div>
                          )}
                          <span className="gif-label">{word}</span>
                        </div>
                      )
                    })}
                  </div>
                ) : signWords.length > 0 ? (
                  <div className="gif-flex-container">
                    {signWords.map((word, i) => {
                      const matched = signWordImages.find((item) => item.word === word)
                      return (
                        <div key={i} className="gif-box-unit">
                          {matched?.src ? (
                            <img
                              className="gif-thumb"
                              src={matched.src}
                              alt={word}
                            />
                          ) : (
                            <div className="gif-placeholder-img">WEBP</div>
                          )}
                          <span className="gif-label">{word}</span>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <span className="placeholder-text">{t('chat.gifPlaceholder')}</span>
                )}
              </div>
            </div>
          )}

          {isCamOpen && (
            <>
              {/* 相機框保持正常比例 */}
              <div className="main-display-box">
                <img
                  className="video-stream"
                  src={streamFrameUrl || `${apiBase}/api/v1/stream`}
                  alt="Gesture stream"
                />
                <div className="gesture-status gesture-status-overlay">{detectedText}</div>
              </div>
            </>
          )}
        </section>

        {/* 底部輸入控制 */}
        <footer className="control-footer">
          <form className="main-input-group" onSubmit={handleSend}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isCamOpen ? t('chat.cameraMode') : t('chat.inputPlaceholder')}
              disabled={isCamOpen || isGenerating}
            />
            <button type="submit" className="icon-btn send-btn" disabled={!input || isGenerating}>
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