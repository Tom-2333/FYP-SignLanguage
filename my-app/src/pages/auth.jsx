import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import './auth.css'

export default function Auth({ mode = 'login' }) {
  const navigate = useNavigate()
  const [view, setView] = useState(mode) // 'login' or 'register'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!email || !password || (view === 'register' && !name)) {
      setError('Please complete all fields')
      return
    }
    if (!email.includes('@')) {
      setError('Please enter a valid email')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)
    // Mock async auth call
    setTimeout(() => {
      setLoading(false)
      // For demo, register always succeeds; login succeeds if password is 'password123'
      if (view === 'login' && password !== 'password123') {
        setError('Invalid credentials (demo: use password123)')
        return
      }

      // Save login state and username
      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem('userName', name || email.split('@')[0])
      
      // On success navigate to vocabulary
      navigate('/vocabulary')
    }, 900)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h2>{view === 'login' ? 'Login' : 'Register'}</h2>

        <form onSubmit={submit} className="auth-form">
          {view === 'register' && (
            <label className="field">
              <div className="label">Full name</div>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
            </label>
          )}

          <label className="field">
            <div className="label">Email</div>
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
          </label>

          <label className="field">
            <div className="label">Password</div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="min 6 chars" />
          </label>

          {error && <div className="error">{error}</div>}

          <div className="actions">
            <button className="primary" type="submit" disabled={loading}>{loading ? 'Please wait...' : (view === 'login' ? 'Login' : 'Create account')}</button>
          </div>
        </form>

        <div className="switch">
          {view === 'login' ? (
            <>
              <span>Don't have an account?</span>
              <button className="link" onClick={() => setView('register')}>Register</button>
            </>
          ) : (
            <>
              <span>Already have an account?</span>
              <button className="link" onClick={() => setView('login')}>Login</button>
            </>
          )}
        </div>

        <div className="alt-links">
          <Link to="/">Back to app</Link>
        </div>
      </div>
    </div>
  )
}
