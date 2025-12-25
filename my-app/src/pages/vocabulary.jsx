import React, { useEffect, useRef, useState } from 'react'
import './vocabulary.css'

// Get confidence score for a word (currently hard-coded, will connect to API later)
const getConfidence = (wordId) => {
  // TODO: Replace with API call to detect hand gesture accuracy
  // Example: const response = await fetch(`/api/confidence/${wordId}`)
  return 85 // Hard-coded value for now
}

// Dictionary data from the file
const dictionaryData = {
  'All': {
    name: 'All Words',
    words: [] // Will be populated dynamically
  },
  'A': {
    name: 'Emotion / Attitude / Feelings',
    words: [
      { id: '002', word: 'Puzzled' },
      { id: '003', word: 'Surprise' },
      { id: '006', word: 'Bored' },
      { id: '010', word: 'Awkward' },
      { id: '028', word: 'Shy' },
      { id: '040', word: 'Good' },
      { id: '042', word: 'Wrong' },
      { id: '044', word: 'Doubt' },
      { id: '056', word: 'Angry' },
      { id: '057', word: 'Serious' },
      { id: '058', word: 'Sick' },
      { id: '067', word: 'Important' },
      { id: '075', word: 'Silly' },
      { id: '088', word: 'Really' },
      { id: '112', word: 'Sad' },
      { id: '134', word: 'Wonder' },
      { id: '142', word: 'Bad' }
    ]
  },
  'B': {
    name: 'Person / Family / Social Roles',
    words: [
      { id: '051', word: 'Brother' },
      { id: '052', word: 'Brother' },
      { id: '053', word: 'Person' },
      { id: '062', word: 'Father' },
      { id: '080', word: 'Mother' },
      { id: '099', word: 'Grandfather' },
      { id: '100', word: 'Grandfather' },
      { id: '111', word: 'Boss' },
      { id: '146', word: 'Son' },
      { id: '150', word: 'Boy' }
    ]
  },
  'C': {
    name: 'Actions / Verbs / Activities',
    words: [
      { id: '001', word: 'Start' },
      { id: '008', word: 'Bath' },
      { id: '013', word: 'Hunt' },
      { id: '021', word: 'Warn' },
      { id: '029', word: 'Lookat' },
      { id: '030', word: 'Learn' },
      { id: '034', word: 'Print' },
      { id: '039', word: 'Bake' },
      { id: '076', word: 'Eat' },
      { id: '082', word: 'Drink' },
      { id: '085', word: 'Wait' },
      { id: '086', word: 'Swallow' },
      { id: '091', word: 'Subtract' },
      { id: '092', word: 'Win' },
      { id: '093', word: 'After' },
      { id: '094', word: 'Wear' },
      { id: '096', word: 'Try' },
      { id: '097', word: 'Try' },
      { id: '102', word: 'Act' },
      { id: '103', word: 'Parade' },
      { id: '104', word: 'Vote' },
      { id: '106', word: 'Grow' },
      { id: '114', word: 'Zoomin' },
      { id: '120', word: 'Dance' },
      { id: '131', word: 'Sew' },
      { id: '132', word: 'Decide' },
      { id: '144', word: 'Leave' },
      { id: '149', word: 'Travel' }
    ]
  },
  'D': {
    name: 'Objects / Things / Physical Items',
    words: [
      { id: '004', word: 'Hearingaid' },
      { id: '024', word: 'Flag' },
      { id: '025', word: 'Film' },
      { id: '027', word: 'Videophone' },
      { id: '038', word: 'Pill' },
      { id: '041', word: 'Hotel' },
      { id: '049', word: 'Wristwatch' },
      { id: '050', word: 'Breakdown' },
      { id: '054', word: 'Bug' },
      { id: '055', word: 'Salt' },
      { id: '059', word: 'Cabbage' },
      { id: '061', word: 'Speakers' },
      { id: '066', word: 'Certificate' },
      { id: '090', word: 'Hospital' },
      { id: '095', word: 'Key' },
      { id: '113', word: 'Cigar' },
      { id: '115', word: 'Creditcard' },
      { id: '137', word: 'Hairdryer' },
      { id: '141', word: 'Blinds' }
    ]
  },
  'E': {
    name: 'Abstract / Concepts / Relations',
    words: [
      { id: '007', word: 'Responsibili' },
      { id: '011', word: 'Relationship' },
      { id: '012', word: 'Favorite' },
      { id: '020', word: 'Impossible' },
      { id: '026', word: 'Last' },
      { id: '035', word: 'Mind' },
      { id: '036', word: 'Body' },
      { id: '037', word: 'Because' },
      { id: '043', word: 'Type' },
      { id: '045', word: 'Judge' },
      { id: '046', word: 'Patient' },
      { id: '047', word: 'Much' },
      { id: '065', word: 'Nothing' },
      { id: '069', word: 'Freckles' },
      { id: '070', word: 'Engagement' },
      { id: '071', word: 'Engagement' },
      { id: '074', word: 'Peace' },
      { id: '077', word: 'Possible' },
      { id: '083', word: 'Scarcely' },
      { id: '119', word: 'Government' },
      { id: '121', word: 'Experience' },
      { id: '122', word: 'Experience' },
      { id: '123', word: 'Wet' },
      { id: '124', word: 'Disagreement' },
      { id: '126', word: 'Lookappearan' },
      { id: '127', word: 'Mean' },
      { id: '128', word: 'New' },
      { id: '129', word: 'Age' },
      { id: '130', word: 'About' },
      { id: '133', word: 'Stress' },
      { id: '135', word: 'Pile' },
      { id: '136', word: 'Pile' },
      { id: '143', word: 'Health' },
      { id: '148', word: 'Character' }
    ]
  },
  'F': {
    name: 'Places / Locations',
    words: [
      { id: '017', word: 'City' },
      { id: '018', word: 'City2' },
      { id: '022', word: 'Newyork' },
      { id: '041', word: 'Hotel' },
      { id: '072', word: 'Farm' },
      { id: '090', word: 'Hospital' }
    ]
  },
  'G': {
    name: 'Time / Days / Units / Seasons',
    words: [
      { id: '032', word: 'Three' },
      { id: '033', word: 'Three' },
      { id: '060', word: 'Minute' },
      { id: '084', word: 'Year' },
      { id: '087', word: 'Friday' },
      { id: '101', word: 'Summer' },
      { id: '109', word: 'Thursday' },
      { id: '138', word: 'Week' },
      { id: '139', word: 'Week' },
      { id: '140', word: 'Time' },
      { id: '147', word: 'Sunset' }
    ]
  },
  'H': {
    name: 'Colors / Appearance / Physical Traits',
    words: [
      { id: '069', word: 'Freckles' },
      { id: '078', word: 'Black' },
      { id: '125', word: 'Purple' },
      { id: '145', word: 'Green' },
      { id: '126', word: 'Lookappearan' }
    ]
  },
  'I': {
    name: 'Food / Taste',
    words: [
      { id: '039', word: 'Bake' },
      { id: '055', word: 'Salt' },
      { id: '059', word: 'Cabbage' },
      { id: '068', word: 'Delicious' }
    ]
  },
  'J': {
    name: 'Health / Medical / Disability',
    words: [
      { id: '004', word: 'Hearingaid' },
      { id: '005', word: 'Blind' },
      { id: '015', word: 'Headache' },
      { id: '058', word: 'Sick' },
      { id: '090', word: 'Hospital' },
      { id: '143', word: 'Health' }
    ]
  },
  'K': {
    name: 'Quantifiers / Numerals / Determiners / Question Words',
    words: [
      { id: '009', word: 'Some' },
      { id: '032', word: 'Three' },
      { id: '033', word: 'Three' },
      { id: '047', word: 'Much' },
      { id: '048', word: '5dollars' },
      { id: '065', word: 'Nothing' },
      { id: '073', word: 'Which' },
      { id: '098', word: 'Where' },
      { id: '130', word: 'About' }
    ]
  },
  'L': {
    name: 'Devices / Technology / Media',
    words: [
      { id: '004', word: 'Hearingaid' },
      { id: '025', word: 'Film' },
      { id: '027', word: 'Videophone' },
      { id: '049', word: 'Wristwatch' },
      { id: '061', word: 'Speakers' },
      { id: '115', word: 'Creditcard' },
      { id: '137', word: 'Hairdryer' }
    ]
  },
  'M': {
    name: 'Events / Accidents / Celebrations',
    words: [
      { id: '089', word: 'Congratulati' },
      { id: '116', word: 'Accident' },
      { id: '117', word: 'Accident' },
      { id: '118', word: 'Accident' }
    ]
  },
  'N': {
    name: 'Variants / Duplicates / Uncertain',
    words: [
      { id: '032', word: 'Three' },
      { id: '033', word: 'Three' },
      { id: '051', word: 'Brother' },
      { id: '052', word: 'Brother' },
      { id: '067', word: 'Important' },
      { id: '069', word: 'Freckles' },
      { id: '070', word: 'Engagement' },
      { id: '071', word: 'Engagement' },
      { id: '084', word: 'Year' },
      { id: '099', word: 'Grandfather' },
      { id: '100', word: 'Grandfather' },
      { id: '116', word: 'Accident' },
      { id: '117', word: 'Accident' },
      { id: '118', word: 'Accident' },
      { id: '121', word: 'Experience' },
      { id: '122', word: 'Experience' },
      { id: '135', word: 'Pile' },
      { id: '136', word: 'Pile' },
      { id: '138', word: 'Week' },
      { id: '139', word: 'Week' }
    ]
  }
}

export default function Vocabulary() {
  const videoRef = useRef(null)
  const [cameraAllowed, setCameraAllowed] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedWord, setSelectedWord] = useState(null)
  const [showDemo, setShowDemo] = useState(false) // true: show demo, false: show word list
  const wordsPerPage = 10

  const categoryKeys = Object.keys(dictionaryData)
  
  // Create All category with all words from other categories
  const allWords = categoryKeys
    .filter(key => key !== 'All')
    .flatMap(key => dictionaryData[key].words)
  
  const currentCategoryData = selectedCategory === 'All' 
    ? { name: 'All Words', words: allWords }
    : dictionaryData[selectedCategory]
  
  const totalWords = currentCategoryData.words.length
  const totalPages = Math.ceil(totalWords / wordsPerPage)
  
  // Get words for current page
  const startIndex = (currentPage - 1) * wordsPerPage
  const endIndex = startIndex + wordsPerPage
  const currentWords = currentCategoryData.words.slice(startIndex, endIndex)

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
      const video = videoRef.current
      if (video && video.srcObject) {
        const tracks = video.srcObject.getTracks()
        tracks.forEach(t => t.stop())
      }
    }
  }, [])

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
        <div className="vocab-greeting">Hello 👋 <small className="muted">(Practice Mode)</small></div>
      </header>

      {/* Progress and Selected Word Info */}
      <div className="vocab-info-bar">
        <div className="info-item">
          <span className="info-label">Progress:</span>
          <span className="info-value">{selectedWord ? `${currentCategoryData.words.findIndex(w => w.id === selectedWord.id) + 1}/${totalWords}` : `0/${totalWords}`}</span>
        </div>
        {selectedWord && (
          <div className="info-item">
            <span className="info-label">Selected Word:</span>
            <span className="info-value selected-word-name">{selectedWord.word}</span>
          </div>
        )}
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
                {key}. {dictionaryData[key].name}
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
                {selectedCategory}. {currentCategoryData.name}
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
                      src={`../../HKSLLEX-video-2023-webp/${selectedWord.id}.webp`}
                      alt={selectedWord.word}
                      className="sign-video"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                  ) : (
                    <div className="placeholder-text">Select a word to view sign</div>
                  )}
                  <div className="placeholder-text" style={{display: 'none'}}>
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

              {/* Camera Box */}
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
            </>
          )}
        </main>

      </section>
    </div>
  )
}