import React, { useCallback, useEffect, useRef, useState } from 'react'
import './vocabulary.css'
import { Hands } from '@mediapipe/hands'
import { Camera } from '@mediapipe/camera_utils'
import { useLanguage } from '../contexts/LanguageContext'

// Get confidence score for a word (currently hard-coded, will connect to API later)
const getConfidence = (wordId) => {
  // TODO: Replace with API call to detect hand gesture accuracy
  // Example: const response = await fetch(`/api/confidence/${wordId}`)
  return 85 // Hard-coded value for now
}

export default function Vocabulary() {
  const apiBase = process.env.REACT_APP_GESTURE_API || 'http://127.0.0.1:5001'
  const sldbApiBase = process.env.REACT_APP_SLDB_API_BASE || 'http://localhost/SL-Database_api'
  const normalizeSldbUrl = (path) => {
    if (!path) return null
    try {
      return new URL(path, `${sldbApiBase.replace(/\/$/, '')}/`).href
    } catch (error) {
      return path
    }
  }
  const { language, setLanguage, t } = useLanguage()
  const videoRef = useRef(null)

  const canvasRef = useRef(null)
  const handsRef = useRef(null)
  const cameraRef = useRef(null)
  const [cameraAllowed, setCameraAllowed] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedWord, setSelectedWord] = useState(null)
  const [showDemo, setShowDemo] = useState(false) // true: show demo, false: show word list
  const [searchQuery, setSearchQuery] = useState('') // Search query state
  const [showSuggestions, setShowSuggestions] = useState(false) // Show search suggestions
  const [detectedGesture, setDetectedGesture] = useState('') // Detected hand gesture
  const [gestureData, setGestureData] = useState({}) // Detailed gesture data from Python API
  const [handLandmarks, setHandLandmarks] = useState(null) // Hand landmarks data
  const [dictionaryData, setDictionaryData] = useState({}) // Dictionary data fetched from API
  const [dictionaryError, setDictionaryError] = useState('')
  const [gestureServiceOnline, setGestureServiceOnline] = useState(false) // Python service reachability
  const [streamError, setStreamError] = useState(false)
  const [streamFrameUrl, setStreamFrameUrl] = useState('')
  const [showDiagnostics, setShowDiagnostics] = useState(false)
  const [wsStatus, setWsStatus] = useState('connecting')
  const [wsError, setWsError] = useState('')
  const [lastWsMessageAt, setLastWsMessageAt] = useState(null)
  const [healthInfo, setHealthInfo] = useState({
    status: 'checking',
    latencyMs: null,
    error: '',
    lastCheckedAt: null
  })
  const frameThrottleRef = useRef(0) // Throttle MediaPipe frames to lower CPU
  const userName = localStorage.getItem('userName') || 'User'
  const userId = localStorage.getItem('userId')
  const [isCompleted, setIsCompleted] = useState(false)
  const [colorMode, setColorMode] = useState(() => localStorage.getItem('colorMode') || 'light')
  const [completedWordIds, setCompletedWordIds] = useState(new Set())
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('fontSize') || '100%')
  const wordsPerPage = 10
  const wordSize = fontSize === '90%' ? 'small' : fontSize === '125%' ? 'large' : 'medium'
  const normalizedGestureText = (gestureData.sequence_gesture_text || '').toLowerCase()
  const normalizedSelectedWord = (selectedWord?.word || '').toLowerCase()
  const isMatch = Boolean(selectedWord && gestureData.sequence_gesture_text && normalizedGestureText === normalizedSelectedWord)

  // CRA (react-scripts) does not automatically serve MediaPipe's WASM/asset files from node_modules.
  // Without a proper locateFile, MediaPipe will request assets from your app origin and often get
  // index.html ("<"), causing "Unexpected token '<'" runtime errors.
  const MEDIAPIPE_HANDS_VERSION = '0.4.1675469240'

  // Hand connections (simplified - MediaPipe has 21 landmarks)
  const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
    [0, 5], [5, 6], [6, 7], [7, 8], // Index
    [5, 9], [9, 10], [10, 11], [11, 12], // Middle
    [9, 13], [13, 14], [14, 15], [15, 16], // Ring
    [13, 17], [17, 18], [18, 19], [19, 20], // Pinky
    [0, 17] // Palm
  ]

  // Helper functions for drawing (simplified versions)
  const drawConnectors = (ctx, landmarks, connections, style) => {
    ctx.strokeStyle = style.color
    ctx.lineWidth = style.lineWidth

    for (const connection of connections) {
      const [start, end] = connection
      ctx.beginPath()
      ctx.moveTo(
        (1 - landmarks[start].x) * ctx.canvas.width,
        landmarks[start].y * ctx.canvas.height
      )
      ctx.lineTo(
        (1 - landmarks[end].x) * ctx.canvas.width,
        landmarks[end].y * ctx.canvas.height
      )
      ctx.stroke()
    }
  }

  const drawLandmarks = (ctx, landmarks, style) => {
    ctx.fillStyle = style.color

    for (const landmark of landmarks) {
      ctx.beginPath()
      ctx.arc(
        (1 - landmark.x) * ctx.canvas.width,
        landmark.y * ctx.canvas.height,
        style.radius,
        0,
        2 * Math.PI
      )
      ctx.fill()
    }
  }

  // Apply color mode from localStorage
  useEffect(() => {
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

  const onHandsResults = useCallback((results) => {
    // Save canvas reference
    const canvas = canvasRef.current
    if (!canvas) return

    const canvasCtx = canvas.getContext('2d')
    if (!canvasCtx) return

    // Clear canvas
    canvasCtx.save()
    canvasCtx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw the video frame
    if (results.image) {
      canvasCtx.save()
      canvasCtx.scale(-1, 1)
      canvasCtx.drawImage(results.image, -canvas.width, 0, canvas.width, canvas.height)
      canvasCtx.restore()
    }

    // Draw hand landmarks if detected
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
      for (const landmarks of results.multiHandLandmarks) {
        drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
          color: '#00FF00',
          lineWidth: 3
        })
        drawLandmarks(canvasCtx, landmarks, {
          color: '#FF0000',
          lineWidth: 1,
          radius: 3
        })
      }

      // Store landmarks for gesture recognition
      setHandLandmarks(results.multiHandLandmarks)

      // Simple gesture detection (placeholder - you can expand this)
      const numHands = results.multiHandLandmarks.length
      if (numHands === 1) {
        setDetectedGesture('One hand detected')
      } else if (numHands === 2) {
        setDetectedGesture('Two hands detected')
      }
    } else {
      setHandLandmarks(null)
      setDetectedGesture('No hands detected')
    }

    canvasCtx.restore()
  }, [HAND_CONNECTIONS, drawConnectors, drawLandmarks])


  // Fetch dictionary data from XAMPP API
  useEffect(() => {
    let active = true
    const fetchData = async () => {
      try {
        const response = await fetch(`${sldbApiBase}/get_words.php`)
        if (!response.ok) throw new Error('Failed to fetch data')
        const data = await response.json()
        if (active) {
          setDictionaryData(data)
          setDictionaryError('')
        }
      } catch (error) {
        if (error.name === 'AbortError') return
        console.error('Error fetching dictionary data:', error)
        if (active) {
          setDictionaryData({})
          setDictionaryError(error.message || 'Unknown error')
        }
      }
    }
    fetchData()
    return () => {
      active = false
    }
  }, [])

  // Real-time gesture + frame updates from WebSocket
  useEffect(() => {
    let active = true
    let socket = null
    let reconnectTimer = null

    const wsBase = apiBase.replace(/^http/i, 'ws')
    const wsUrl = `${wsBase}/api/v1/ws/gesture`

    const connect = () => {
      if (!active) return
      setWsStatus('connecting')
      socket = new WebSocket(wsUrl)

      socket.onopen = () => {
        if (!active) return
        setWsStatus('online')
        setWsError('')
        setGestureServiceOnline(true)
        setStreamError(false)
      }

      socket.onmessage = (event) => {
        if (!active) return
        try {
          const payload = JSON.parse(event.data)
          const data = payload?.gesture || {}
          setLastWsMessageAt(Date.now())
          setGestureData(data)

          if (data.sequence_gesture_text) {
            setDetectedGesture(`Sequence: ${data.sequence_gesture_text}`)
          } else if (data.hand_sign_text) {
            setDetectedGesture(`Hand Sign: ${data.hand_sign_text}`)
          } else {
            setDetectedGesture('No gesture detected')
          }

          if (payload?.frame_data_url) {
            setStreamFrameUrl(payload.frame_data_url)
            setCameraAllowed(true)
            setStreamError(false)
          }
        } catch (error) {
          console.error('Invalid WebSocket payload:', error)
        }
      }

      socket.onerror = () => {
        if (!active) return
        setWsStatus('error')
        setWsError('WebSocket error')
        setGestureServiceOnline(false)
        setStreamError(true)
      }

      socket.onclose = () => {
        if (!active) return
        setWsStatus('reconnecting')
        setGestureServiceOnline(false)
        reconnectTimer = setTimeout(connect, 1200)
      }
    }

    connect()

    return () => {
      active = false
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (socket) socket.close()
    }
  }, [apiBase])

  // Lightweight health check for frontend diagnostics
  useEffect(() => {
    let active = true
    let intervalId = null

    const healthUrl = `${apiBase}/api/v1/health`

    const checkHealth = async () => {
      const started = performance.now()
      try {
        const response = await fetch(healthUrl, {
          signal: AbortSignal.timeout(1500)
        })
        const latencyMs = Math.round(performance.now() - started)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        if (!active) return
        setHealthInfo({
          status: 'online',
          latencyMs,
          error: '',
          lastCheckedAt: Date.now()
        })
      } catch (error) {
        if (!active) return
        setHealthInfo({
          status: 'offline',
          latencyMs: null,
          error: error?.message || 'health check failed',
          lastCheckedAt: Date.now()
        })
      }
    }

    checkHealth()
    intervalId = setInterval(checkHealth, 8000)

    return () => {
      active = false
      if (intervalId) clearInterval(intervalId)
    }
  }, [apiBase])

  const formatTimestamp = (ts) => {
    if (!ts) return 'N/A'
    return new Date(ts).toLocaleTimeString()
  }

  // Fetch completed words for user
  useEffect(() => {
    if (!userId) return
    let active = true
    const fetchProgress = async () => {
      try {
        const response = await fetch(`${sldbApiBase}/get_user_progress.php?user_id=${encodeURIComponent(userId)}`)
        if (!response.ok) throw new Error('Failed to fetch user progress')
        const data = await response.json()
        if (!active) return
        if (data.success && Array.isArray(data.word_ids)) {
          setCompletedWordIds(new Set(data.word_ids.map(String)))
        }
      } catch (error) {
        if (error.name === 'AbortError') return
        console.error('Error fetching user progress:', error)
      }
    }

    fetchProgress()
    return () => {
      active = false
    }
  }, [userId, sldbApiBase])

  // Check for word match and save progress
  useEffect(() => {
    console.log('Checking match', selectedWord?.word, gestureData.sequence_gesture_text, isCompleted, userId)
    if (isMatch && !isCompleted && userId) {
      console.log('Match found, saving progress')
      setIsCompleted(true)
      // Save to database
      fetch(`${sldbApiBase}/save_progress.php`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: parseInt(userId),
          word_id: selectedWord.id,
          confidence: getConfidence(selectedWord.id)
        })
      })
        .then(response => {
          console.log('Fetch response status:', response.status)
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          return response.json()
        })
        .then(data => {
          console.log('Save response:', data)
          if (data.success) {
            console.log('Progress saved successfully')
            setCompletedWordIds(prev => {
              const next = new Set(prev)
              if (selectedWord?.id) next.add(String(selectedWord.id))
              return next
            })
          } else {
            console.error('Save failed:', data.error)
          }
        })
        .catch(err => {
          console.error('Save progress error:', err)
        })
    }
  }, [isMatch, isCompleted, userId, selectedWord, gestureData, sldbApiBase])

  // Reset completion when word changes
  useEffect(() => {
    if (!selectedWord) {
      setIsCompleted(false)
      return
    }
    const existsInProgress = completedWordIds.has(String(selectedWord.id))
    setIsCompleted(existsInProgress || isMatch)
  }, [selectedWord, completedWordIds, isMatch])

  // Camera setup useEffect
  useEffect(() => {
    setCameraAllowed(false)
    return () => { }
  }, [onHandsResults])

  // Ensure data is loaded before rendering
  if (dictionaryError) {
    return <div>{`Failed to load vocabulary data: ${dictionaryError}`}</div>
  }

  if (!dictionaryData || Object.keys(dictionaryData).length === 0) {
    return <div>{t('vocab.loadingData')}</div>
  }

  const categoryKeys = Object.keys(dictionaryData)

  // Create All category with all words from other categories
  const allWords = categoryKeys
    .filter(key => key !== 'All')
    .flatMap(key => dictionaryData[key].words)

  const totalAllWords = allWords.length
  const completedCount = allWords.filter(word => completedWordIds.has(String(word.id))).length
  const completionRate = totalAllWords > 0 ? Math.round((completedCount / totalAllWords) * 100) : 0

  const currentCategoryData = selectedCategory === 'All'
    ? { name: 'All Words', name_en: 'All Words', words: allWords }
    : dictionaryData[selectedCategory]

  // Filter words based on search query (search both Chinese and English)
  const filteredWords = currentCategoryData.words.filter(word =>
    word.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (word.engword && word.engword.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const totalWords = filteredWords.length
  const totalPages = Math.ceil(totalWords / wordsPerPage)

  // Get words for current page
  const startIndex = (currentPage - 1) * wordsPerPage
  const endIndex = startIndex + wordsPerPage
  const currentWords = filteredWords.slice(startIndex, endIndex)

  const handleCategoryClick = (category) => {
    setSelectedCategory(category)
    setCurrentPage(1)
    setSelectedWord(null)
    setShowDemo(false) // Show word list when category is clicked
  }

  const handleWordClick = (word) => {
    setSelectedWord(word)
    setShowDemo(true) // Show demo when word is clicked
  }

  const handlePageChange = (page) => {
    setCurrentPage(page)
  }

  const handleSuggestionClick = (word) => {
    setSelectedWord(word)
    setShowDemo(true)
    setSearchQuery('')
    setShowSuggestions(false)
  }

  const renderPagination = () => {
    const pages = []
    const maxVisiblePages = 5

    // Previous button
    pages.push(
      <button
        key="prev"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="page-btn"
      >
        «
      </button>
    )

    // Page numbers
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)

    if (endPage - startPage < maxVisiblePages - 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1)
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`page-btn ${i === currentPage ? 'active' : ''}`}
        >
          {i}
        </button>
      )
    }

    // Next button
    pages.push(
      <button
        key="next"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="page-btn"
      >
        »
      </button>
    )

    return pages
  }

  return (
    <div
      className={`vocab-container ${fontSize === '90%' ? 'font-size-90' : fontSize === '125%' ? 'font-size-125' : 'font-size-100'}`}
      data-theme={colorMode}
    >
      <header className="vocab-header">
        <div className="vocab-progress">
          <span className={`progress-label word-size-${wordSize}`}>{t('vocab.recognitionRate')}</span>
          <div className="vocab-progress-bar" aria-hidden>
            <div className="vocab-progress-fill" style={{ width: `${completionRate}%` }} />
          </div>
          <span className={`progress-value word-size-${wordSize}`}>{completionRate}%</span>
        </div>
        <div className={`vocab-greeting word-size-${wordSize}`}>{t('vocab.hello')}{userName}! </div>
      </header>

      {/* Progress and Selected Word Info */}
      <div className="vocab-info-bar">
        <div className="info-item">
          <span className={`info-label word-size-${wordSize}`}>{t('vocab.progress')}</span>
          <span className={`info-value word-size-${wordSize}`}>{selectedWord ? `${currentCategoryData.words.findIndex(w => w.id === selectedWord.id) + 1}/${currentCategoryData.words.length}` : `0/${currentCategoryData.words.length}`}</span>
        </div>
        {selectedWord && (
          <div className="info-item">
            <span className={`info-label word-size-${wordSize}`}>{t('vocab.selectedWord')}</span>
            <span className={`info-value selected-word-name word-size-${wordSize}`}>{language === 'en' ? (selectedWord.engword || selectedWord.word) : selectedWord.word}</span>
          </div>
        )}
        <div className="search-container">
          <input
            type="text"
            placeholder={t('vocab.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setCurrentPage(1)
              setShowSuggestions(e.target.value.length > 0)
            }}
            onFocus={() => searchQuery.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            className="search-input"
          />

          {searchQuery && (
            <button
              className="clear-search"
              onClick={() => {
                setSearchQuery('')
                setCurrentPage(1)
                setShowSuggestions(false)
              }}
            >
              ✕
            </button>
          )}
          {/* Search Suggestions Dropdown */}
          {showSuggestions && filteredWords.length > 0 && (
            <div className="search-suggestions">
              {filteredWords.slice(0, 10).map((word) => (
                <div
                  key={word.id}
                  className="suggestion-item"
                  onClick={() => handleSuggestionClick(word)}
                >
                  <span className="suggestion-word">{language === 'en' ? (word.engword || word.word) : word.word}</span>
                  <span className="suggestion-id">ID: {word.id}</span>
                </div>
              ))}
              {filteredWords.length > 10 && (
                <div className="suggestion-more">
                  +{filteredWords.length - 10} {t('vocab.moreResults')}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="vocab-header-controls">
          <div className="vocab-language-toggle" role="group" aria-label="Language selector">
            <span className="vocab-language-icon" aria-hidden>🌐</span>
            <button
              type="button"
              className={`vocab-language-btn ${language === 'zh' ? 'active' : ''}`}
              onClick={() => setLanguage('zh')}
            >
              粵
            </button>
            <span className="vocab-language-divider">|</span>
            <button
              type="button"
              className={`vocab-language-btn ${language === 'en' ? 'active' : ''}`}
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
      </div>

      <section className="vocab-main">
        {/* Category Buttons */}
        <aside className="vocab-sidebar combined">
          <h3>{t('vocab.categories')}</h3>
          <div className="category-buttons">
            {categoryKeys.map(key => (
              <button
                key={key}
                className={`category-btn ${key === selectedCategory ? 'active' : ''} ${key === 'All' ? 'all-btn' : ''}`}
                onClick={() => handleCategoryClick(key)}
              >
                {language === 'en' ? (dictionaryData[key].name_en || dictionaryData[key].name) : dictionaryData[key].name}
              </button>
            ))}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className={`vocab-content ${showDemo ? 'demo-view' : ''}`}>
          {!showDemo ? (
            /* Word List View */
            <div className="vocab-card word-list-box">
              <div className="box-title">
                {language === 'en' ? (currentCategoryData.name_en || currentCategoryData.name) : currentCategoryData.name}
              </div>
              <div className="word-grid">
                {currentWords.map((item) => (
                  <button
                    key={item.id}
                    className={`word-btn ${selectedWord?.id === item.id ? 'selected' : ''} ${completedWordIds.has(String(item.id)) ? 'completed' : ''}`}
                    onClick={() => handleWordClick(item)}
                  >
                    {language === 'en' ? (item.engword || item.word) : item.word}
                  </button>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  {renderPagination()}
                </div>
              )}
            </div>
          ) : (
            /* Demo View */
            <>
              {/* Video/Image Display */}
              <div className="vocab-card demo-box">
                <div className="box-title">{t('vocab.signDemo')}</div>
                <div className="gif-area">
                  {selectedWord ? (
                    <img
                      src={normalizeSldbUrl(`video-webp/${selectedWord.id.padStart(8, '0')}.webp`)}
                      alt={language === 'en' ? (selectedWord.engword || selectedWord.word) : selectedWord.word}
                      className="sign-video"
                      onError={(e) => {
                        console.error('Failed to load image:', e.target.src)
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                  ) : (
                    <div className="placeholder-text">{t('vocab.selectWord')}</div>
                  )}
                  <div className="placeholder-text hidden">
                    {t('vocab.videoNotAvailable')}
                  </div>
                </div>
                {selectedWord && (
                  <div className="card-meta">
                    <h2 className={`demo-word-title word-size-${wordSize}`}>{language === 'en' ? (selectedWord.engword || selectedWord.word) : selectedWord.word}</h2>
                    {isCompleted && <div className="completion-status">{t('vocab.completed')}</div>}
                    <div className="translation">ID: {selectedWord.id}</div>
                    {/* Navigation Buttons */}
                    <div className="demo-nav-buttons">
                      <button
                        className="nav-btn prev"
                        onClick={() => {
                          if (selectedWord) {
                            const currentIndex = currentCategoryData.words.findIndex(w => w.id === selectedWord.id)
                            const prevIndex = (currentIndex - 1 + totalWords) % totalWords
                            handleWordClick(currentCategoryData.words[prevIndex])
                            const newPage = Math.floor(prevIndex / wordsPerPage) + 1
                            if (newPage !== currentPage) setCurrentPage(newPage)
                          }
                        }}
                      >
                        {t('vocab.previous')}
                      </button>
                      <button
                        className="nav-btn next"
                        onClick={() => {
                          if (selectedWord) {
                            const currentIndex = currentCategoryData.words.findIndex(w => w.id === selectedWord.id)
                            const nextIndex = (currentIndex + 1) % totalWords
                            handleWordClick(currentCategoryData.words[nextIndex])
                            const newPage = Math.floor(nextIndex / wordsPerPage) + 1
                            if (newPage !== currentPage) setCurrentPage(newPage)
                          }
                        }}
                      >
                        {t('vocab.next')}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Camera Box - Always rendered, but hidden when not in demo view */}
          <div className={`vocab-card cam-box ${showDemo ? '' : 'is-hidden'}`}>
            <div className="box-title">
              {t('vocab.yourSign')}
              {detectedGesture && <span className="detected-gesture">• {detectedGesture}</span>}
            </div>
            <div className="cam-wrap">
              <img
                src={streamFrameUrl || `${apiBase}/api/v1/stream`}
                alt="Camera Stream"
                className="live"
                onLoad={() => {
                  setStreamError(false)
                  setCameraAllowed(true)
                }}
                onError={() => {
                  setStreamError(true)
                  setCameraAllowed(false)
                  setDetectedGesture('Camera stream unavailable')
                }}
              />
              {streamError && (
                <div className="cam-placeholder">
                  <div className="cam-placeholder-icon">📷</div>
                  <div>Camera Feed</div>
                  <small>Allow camera permission to practice</small>
                </div>
              )}
              {handLandmarks && (
                <div className="hand-detected-badge">
                  Hands detected: {handLandmarks.length}
                </div>
              )}
            </div>
            {/* Gesture Detection Results */}
            <div className="gesture-results">
              <div className="gesture-header">
                <div className="gesture-header-left">
                  <span>{t('vocab.gestureRecognition')}</span>
                  <span className={`gesture-status ${gestureServiceOnline ? 'online' : 'offline'}`}>
                    {gestureServiceOnline ? t('vocab.connected') : t('vocab.offline')}
                  </span>
                </div>
                <button
                  type="button"
                  className="diag-toggle-btn"
                  onClick={() => setShowDiagnostics((prev) => !prev)}
                >
                  {showDiagnostics ? 'Hide Diagnostics' : 'Show Diagnostics'}
                </button>
              </div>
              {showDiagnostics && (
                <div className="gesture-diagnostics">
                  <div className="diagnostic-title">Diagnostics</div>
                  <div className="diagnostic-row">
                    <span>WebSocket</span>
                    <span className={`diag-badge diag-${wsStatus}`}>{wsStatus}</span>
                  </div>
                  <div className="diagnostic-row">
                    <span>Health API</span>
                    <span className={`diag-badge diag-${healthInfo.status}`}>{healthInfo.status}</span>
                  </div>
                  <div className="diagnostic-row">
                    <span>Health latency</span>
                    <span>{healthInfo.latencyMs != null ? `${healthInfo.latencyMs} ms` : 'N/A'}</span>
                  </div>
                  <div className="diagnostic-row">
                    <span>Last WS message</span>
                    <span>{formatTimestamp(lastWsMessageAt)}</span>
                  </div>
                  <div className="diagnostic-row">
                    <span>Last health check</span>
                    <span>{formatTimestamp(healthInfo.lastCheckedAt)}</span>
                  </div>
                  <div className="diagnostic-meta">WS: {`${apiBase.replace(/^http/i, 'ws')}/api/v1/ws/gesture`}</div>
                  <div className="diagnostic-meta">Health: {`${apiBase}/api/v1/health`}</div>
                  {(wsError || healthInfo.error) && (
                    <div className="diagnostic-error">{wsError || healthInfo.error}</div>
                  )}
                </div>
              )}
              {gestureServiceOnline ? (
                <>
                  {gestureData.sequence_gesture_text && (
                    <div className={`gesture-line gesture-text word-size-${wordSize}`}>
                      <strong>{t('vocab.sequence')}</strong> {gestureData.sequence_gesture_text}
                    </div>
                  )}
                  {gestureData.hand_sign_text && (
                    <div className={`gesture-line gesture-text word-size-${wordSize}`}>
                      <strong>{t('vocab.handSign')}</strong> {gestureData.hand_sign_text}
                    </div>
                  )}
                  {/* Display All detected hands */}
                  {gestureData.hands && gestureData.hands.length > 0 && (
                    <div className="detected-hands">
                      <strong>{t('vocab.detectedHands')} {gestureData.hands.length}:</strong>
                      {gestureData.hands.map((hand, index) => (
                        <div key={index} className="detected-hand-row">
                          <span className={`hand-badge ${hand.hand === 'Left' ? 'left' : 'right'}`}>
                            {hand.hand === 'Left' ? t('vocab.leftHand') : t('vocab.rightHand')}
                          </span>
                          <span>{hand.gesture || t('vocab.noGesture')}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {gestureData.fps && (
                    <div className="fps-text">
                      FPS: {gestureData.fps}
                    </div>
                  )}
                </>
              ) : (
                <div className="gesture-offline">
                  {t('vocab.connecting')}<br />
                  <div className="gesture-offline-box">
                    <strong>{t('vocab.gestureOfflineTitle')}</strong><br />
                    {t('vocab.gestureOfflineStep1')}<br />
                    {t('vocab.gestureOfflineStep2')} <code className="inline-code">cd d:/Profile/Documents/GitHub/FYP-SignLanguage/cv_hands</code><br />
                    {t('vocab.gestureOfflineStep3')} <code className="inline-code">py -3.10 app_simple.py</code><br />
                    <div className="gesture-offline-note">
                      {t('vocab.gestureOfflineNote1')} <strong>{apiBase}</strong><br />
                      {t('vocab.gestureOfflineNote2')} <strong>{`${apiBase}/docs`}</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Match Display - Shows below camera when gesture matches selected word */}
          {showDemo && selectedWord && gestureServiceOnline && gestureData.sequence_gesture_text && (
            <div className={`match-display ${isMatch ? 'is-match' : ''}`}>
              <div>{t('vocab.selectedWordLabel')} {language === 'en' ? (selectedWord.engword || selectedWord.word) : selectedWord.word}</div>
              <div>{t('vocab.sequenceGesture')} {gestureData.sequence_gesture_text}</div>
              {isMatch && (
                <div className="match-badge">
                  <span>✓</span>
                  <span>{t('vocab.match')}</span>
                </div>
              )}
            </div>
          )}
        </main>
      </section>
    </div>
  )
}