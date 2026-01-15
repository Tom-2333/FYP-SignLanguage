import React, { useCallback, useEffect, useRef, useState } from 'react'
import './vocabulary.css'
import { Hands } from '@mediapipe/hands'
import { Camera } from '@mediapipe/camera_utils'

// Get confidence score for a word (currently hard-coded, will connect to API later)
const getConfidence = (wordId) => {
  // TODO: Replace with API call to detect hand gesture accuracy
  // Example: const response = await fetch(`/api/confidence/${wordId}`)
  return 85 // Hard-coded value for now
}

export default function Vocabulary() {
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
  const [gestureServiceOnline, setGestureServiceOnline] = useState(false) // Python service reachability
  const frameThrottleRef = useRef(0) // Throttle MediaPipe frames to lower CPU
  const userName = localStorage.getItem('userName') || 'User'
  const wordsPerPage = 10

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
        const response = await fetch('http://localhost/SL-Database_api/get_words.php')
        if (!response.ok) throw new Error('Failed to fetch data')
        const data = await response.json()
        if (active) setDictionaryData(data)
      } catch (error) {
        if (error.name === 'AbortError') return
        console.error('Error fetching dictionary data:', error)
        // Fallback to empty data or show error
      }
    }
    fetchData()
    return () => {
      active = false
    }
  }, [])

  // Fetch gesture data from Python API
  useEffect(() => {
    let active = true
    const fetchGestureData = async () => {
      try {
        const response = await fetch('http://localhost:5001/gesture', {
          signal: AbortSignal.timeout(1000)  // Add 1 second timeout to prevent hanging
        })
        if (!response.ok) throw new Error('Failed to fetch gesture data')
        const data = await response.json()
        if (!active) return
        setGestureData(data)
        setGestureServiceOnline(true)
        // Update detected gesture for display
        if (data.sequence_gesture_text) {
          setDetectedGesture(`Sequence: ${data.sequence_gesture_text}`)
        } else if (data.hand_sign_text) {
          setDetectedGesture(`Hand Sign: ${data.hand_sign_text}`)
        } else {
          setDetectedGesture('No gesture detected')
        }
      } catch (error) {
        if (error.name === 'AbortError') return
        console.error('Error fetching gesture data:', error)
        setGestureServiceOnline(false)
        setDetectedGesture('Gesture detection unavailable')
      }
    }

    // Fetch immediately and then every 3 seconds (optimized to reduce lag)
    fetchGestureData()
    const interval = setInterval(fetchGestureData, 3000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [])

  // Camera setup useEffect
  useEffect(() => {
    const videoElement = videoRef.current

    // request camera when component mounts
    const start = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }
        })
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          // Wait for metadata and play
          await videoRef.current.play().catch((err) => {
            console.error('Video play was aborted:', err)
          })
        }
        setCameraAllowed(true)

        // Try to initialize MediaPipe Hands
        try {
          
        } catch (mediaPipeError) {
          console.error('MediaPipe initialization failed, falling back to basic camera:', mediaPipeError)
          // Camera is still working, just no hand tracking
          setDetectedGesture('Hand tracking unavailable')
        }

        // Simple video display loop (lightweight, no MediaPipe processing)
        const renderLoop = () => {
          if (videoRef.current && canvasRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
            const canvas = canvasRef.current
            const ctx = canvas.getContext('2d')
            const video = videoRef.current
            
            // Draw mirrored video
            ctx.save()
            ctx.scale(-1, 1)
            ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height)
            ctx.restore()
          }
          if (videoRef.current?.srcObject) {
            requestAnimationFrame(renderLoop)
          }
        }
        renderLoop()
      } catch (err) {
        console.error('Camera error:', err)
        setCameraAllowed(false)
      }
    }
    start().catch((err) => {
      if (err?.name === 'AbortError') return
      console.error('Camera initialization error:', err)
    })

    return () => {
      // stop tracks on unmount
      if (videoElement && videoElement.srcObject) {
        const tracks = videoElement.srcObject.getTracks()
        tracks.forEach(t => t.stop())
      }
      
      // Close MediaPipe instances
      if (cameraRef.current) {
        cameraRef.current.stop()
        cameraRef.current = null
      }
      if (handsRef.current) {
        handsRef.current.close()
        handsRef.current = null
      }
    }
  }, [onHandsResults])

  // Ensure data is loaded before rendering
  if (!dictionaryData || Object.keys(dictionaryData).length === 0) {
    return <div>Loading... (Data Not Found/Server Error)</div>
  }

  const categoryKeys = Object.keys(dictionaryData)

  // Create All category with all words from other categories
  const allWords = categoryKeys
    .filter(key => key !== 'All')
    .flatMap(key => dictionaryData[key].words)

  const currentCategoryData = selectedCategory === 'All'
    ? { name: 'All Words', words: allWords }
    : dictionaryData[selectedCategory]

  // Filter words based on search query
  const filteredWords = currentCategoryData.words.filter(word =>
    word.word.toLowerCase().includes(searchQuery.toLowerCase())
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
    <div className="vocab-container">
      <header className="vocab-header">
        <div className="vocab-progress">
          <span>Recognition Rate</span>
          <div className="vocab-progress-bar" aria-hidden>
            <div className="vocab-progress-fill" style={{ width: `${selectedWord ? getConfidence(selectedWord.id) : 0}%` }} />
          </div>
          <span>{selectedWord ? getConfidence(selectedWord.id) : 0}%</span>
        </div>
        <div className="vocab-greeting">Hello, {userName}! </div>
      </header>

      {/* Progress and Selected Word Info */}
      <div className="vocab-info-bar">
        <div className="info-item">
          <span className="info-label">Progress:</span>
          <span className="info-value">{selectedWord ? `${currentCategoryData.words.findIndex(w => w.id === selectedWord.id) + 1}/${currentCategoryData.words.length}` : `0/${currentCategoryData.words.length}`}</span>
        </div>
        {selectedWord && (
          <div className="info-item">
            <span className="info-label">Selected Word:</span>
            <span className="info-value selected-word-name">{selectedWord.word}</span>
          </div>
        )}
        <div className="search-container">
          <input
            type="text"
            placeholder="Search words..."
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
                  <span className="suggestion-word">{word.word}</span>
                  <span className="suggestion-id">ID: {word.id}</span>
                </div>
              ))}
              {filteredWords.length > 10 && (
                <div className="suggestion-more">
                  +{filteredWords.length - 10} more results
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <section className="vocab-main">
        {/* Category Buttons */}
        <aside className="vocab-sidebar combined">
          <h3>Categories</h3>
          <div className="category-buttons">
            {categoryKeys.map(key => (
              <button
                key={key}
                className={`category-btn ${key === selectedCategory ? 'active' : ''} ${key === 'All' ? 'all-btn' : ''}`}
                onClick={() => handleCategoryClick(key)}
              >
                {dictionaryData[key].name}
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
                {currentCategoryData.name}
              </div>
              <div className="word-grid">
                {currentWords.map((item) => (
                  <button
                    key={item.id}
                    className={`word-btn ${selectedWord?.id === item.id ? 'selected' : ''}`}
                    onClick={() => handleWordClick(item)}
                  >
                    {item.word}
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
                <div className="box-title">Sign Demonstration</div>
                <div className="gif-area">
                  {selectedWord ? (
                    <img
                      src={`http://localhost/SL-Database_api/video-webp/${selectedWord.id.padStart(8, '0')}.webp`}
                      alt={selectedWord.word}
                      className="sign-video"
                      onError={(e) => {
                        console.error('Failed to load image:', e.target.src)
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                  ) : (
                    <div className="placeholder-text">Select a word to view sign</div>
                  )}
                  <div className="placeholder-text" style={{ display: 'none' }}>
                    Video not available
                  </div>
                </div>
                {selectedWord && (
                  <div className="card-meta">
                    <h2>{selectedWord.word}</h2>
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
                        Previous
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
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Camera Box - Always rendered, but hidden when not in demo view */}
          <div className="vocab-card cam-box" style={{ display: showDemo ? 'block' : 'none' }}>
            <div className="box-title">
              Your Sign (Camera)
              {detectedGesture && <span style={{ marginLeft: '10px', fontSize: '14px', color: '#4CAF50' }}>• {detectedGesture}</span>}
            </div>
            <div className="cam-wrap" style={{ position: 'relative' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ display: 'none' }}
              />
              <canvas
                ref={canvasRef}
                width={640}
                height={480}
                className={cameraAllowed ? 'live' : 'hidden'}
                style={{ width: '100%', height: 'auto', backgroundColor: '#000' }}
              />
              {!cameraAllowed && (
                <div className="cam-placeholder">
                  <div style={{ fontSize: 28 }}>📷</div>
                  <div>Camera Feed</div>
                  <small>Allow camera permission to practice</small>
                </div>
              )}
              {handLandmarks && (
                <div style={{
                  position: 'absolute',
                  bottom: '10px',
                  left: '10px',
                  background: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  Hands detected: {handLandmarks.length}
                </div>
              )}
            </div>
            {/* Gesture Detection Results */}
            <div style={{
              padding: '12px',
              background: '#f5f5f5',
              borderTop: '1px solid #ddd',
              fontSize: '14px'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Gesture Recognition:</span>
                <span style={{ 
                  fontSize: '11px', 
                  padding: '2px 8px', 
                  borderRadius: '12px',
                  backgroundColor: gestureServiceOnline ? '#d4edda' : '#f8d7da',
                  color: gestureServiceOnline ? '#155724' : '#721c24',
                  fontWeight: 'normal'
                }}>
                  {gestureServiceOnline ? '● Connected' : '● Offline - Run app.py'}
                </span>
              </div>
              {gestureServiceOnline ? (
                <>
                  {gestureData.sequence_gesture_text && (
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Sequence:</strong> {gestureData.sequence_gesture_text}
                    </div>
                  )}
                  {gestureData.hand_sign_text && (
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Hand Sign:</strong> {gestureData.hand_sign_text}
                    </div>
                  )}
                  {gestureData.finger_gesture_text && (
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Details:</strong> {gestureData.finger_gesture_text}
                    </div>
                  )}
                  {gestureData.handedness && (
                    <div style={{ marginBottom: '4px' }}>
                      <strong>Hand:</strong> {gestureData.handedness}
                    </div>
                  )}
                  {gestureData.fps && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      FPS: {gestureData.fps}
                    </div>
                  )}
                </>
              ) : (
                <div style={{ color: '#666', fontSize: '13px' }}>
                  Connecting to gesture detection server...<br/>
                  <div style={{ marginTop: '8px', padding: '8px', background: '#fff3cd', borderRadius: '4px', color: '#856404' }}>
                    <strong>To start gesture detection:</strong><br/>
                    1. Open terminal<br/>
                    2. Run: <code style={{ background: '#fff', padding: '2px 6px', borderRadius: '3px' }}>cd /Users/ronald8931/Desktop/FYP-SL/cv_hands</code><br/>
                    3. Run: <code style={{ background: '#fff', padding: '2px 6px', borderRadius: '3px' }}>python3 app_simple.py</code><br/>
                    <div style={{ marginTop: '6px', fontSize: '12px' }}>
                      Server should start on <strong>http://localhost:5001</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </section>
    </div>
  )
}