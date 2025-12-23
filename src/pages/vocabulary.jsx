import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './vocabulary.css'

export default function Vocabulary() {
  const navigate = useNavigate()
  const videoRef = useRef(null)
  const [cameraAllowed, setCameraAllowed] = useState(false)

  const entries = [
    // `confidence` represents AI recognition rate (0-100%) for the detected sign
    { word: 'Hello', translation: '你好', confidence: 70, gif: '' },
    { word: 'Thank you', translation: '謝謝', confidence: 40, gif: '' },
    { word: 'Cat', translation: '貓', confidence: 20, gif: '' },
    { word: 'School', translation: '學校', confidence: 85, gif: '' }
  ]
  const categories = [
    'Greetings',
    'Family',
    'Food & Drink',
    'Animals',
    'Numbers',
    'Colors',
    'Daily Activities',
    'Emotions',
    'Travel',
    'School & Work'
  ]

  const [index, setIndex] = useState(0)
  const [selectedCategory, setSelectedCategory] = useState('Greetings')
  const current = entries[index]

  useEffect(() => {
    // request camera when component mounts
    const start = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
        if (videoRef.current) videoRef.current.srcObject = stream
        setCameraAllowed(true)
      } catch (err) {
        console.warn('Camera not available:', err)
        setCameraAllowed(false)
      }
    }
    start()

    return () => {
      // stop tracks on unmount
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks()
        tracks.forEach(t => t.stop())
      }
    }
  }, [])

  return (
    <div className="vocab-container">
      <header className="vocab-header">
        <div className="vocab-progress">
          <span>Recognition Rate</span>
          <div className="vocab-progress-bar" aria-hidden>
            <div className="vocab-progress-fill" style={{ width: `${current.confidence}%` }} />
          </div>
          <span>{current.confidence}%</span>
        </div>
        <div className="vocab-greeting">Hello 👋 <small className="muted">(Practice Mode)</small></div>
      </header>

      <section className="vocab-main">
        <aside className="vocab-sidebar combined">
          <div className="vocab-search">
            <input placeholder="Search sign language..." />
          </div>

          <div className="vocab-categories">
            <h3>Categories</h3>
            <ul>
              {categories.map(cat => (
                <li key={cat} className={cat === selectedCategory ? 'active' : ''} onClick={() => setSelectedCategory(cat)}>
                  {cat}
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <main className="vocab-content">
          <div className="vocab-card demo-box">
            <div className="box-title">Demonstration</div>
            <div className="gif-area">No GIF loaded (mock)</div>
            <div className="card-meta">
              <h2>{current.word}</h2>
              <div className="translation">中文 - {current.translation}</div>
              <div className="controls">
                <button onClick={() => alert('Play GIF mock')}>Play GIF</button>
              </div>
            </div>
          </div>

          <div className="vocab-card cam-box">
            <div className="box-title">Your Sign (Camera)</div>
            <div className="cam-wrap">
              <video ref={videoRef} autoPlay playsInline muted className={cameraAllowed ? 'live' : 'hidden'} />
              {!cameraAllowed && (
                <div className="cam-placeholder">
                  <div style={{fontSize:28}}>📷</div>
                  <div>Camera Feed</div>
                  <small>Allow camera to practice</small>
                </div>
              )}
            </div>
          </div>
        </main>

        <aside className="vocab-progress-side">
          <div className="progress-count">17/50</div>
          <small>{current.confidence}%</small>
        </aside>
      </section>

      <footer className="vocab-footer">
        <button className="nav-btn prev" onClick={() => setIndex((index - 1 + entries.length) % entries.length)}>Previous</button>
        <div>
          <button className="nav-btn next" onClick={() => setIndex((index + 1) % entries.length)}>Next</button>
        </div>
      </footer>
    </div>
  )
}