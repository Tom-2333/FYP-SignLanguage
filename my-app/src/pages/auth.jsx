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
    try {
      const response = await fetch('http://localhost/SL-Database_api/login.php', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: view,
          email,
          username: name,
          password,
        }),
      })
      const data = await response.json()
      if (data.success) {
        if (view === 'register') {
          setView('login')
          setName('')
          setEmail('')
          setPassword('')
          // setError('Registration successful! Please log in.')
        } else {
          // Store user information in localStorage
          localStorage.setItem('isAuthenticated', 'true')
          localStorage.setItem('userName', data.username)
          localStorage.setItem('userId', data.user_id)
          localStorage.setItem('user', JSON.stringify({
            nickname: data.username,
            email: email,
            userId: data.user_id
          }))
          navigate('/vocabulary')
        }
      } else {
        setError(data.error || 'Authentication failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
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
