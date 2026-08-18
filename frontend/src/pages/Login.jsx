import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../api.js'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = new URLSearchParams({ username, password })
      const data = await api('/auth/login', { method: 'POST', body, isForm: true })
      setToken(data.access_token)
      onLogin({ username: data.username, full_name: data.full_name, role: data.role })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-brand">P</div>
        <h1>Purnama <span>Textile</span> ERP</h1>
        <p className="sub">Sistem ERP &amp; SCM Internal · On-Premise</p>
        <form className="auth-form" onSubmit={submit}>
          <div className="field">
            <label>Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          </div>
          <button className="btn-login" disabled={busy}>
            {busy ? 'Memeriksa…' : 'Masuk'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
        <div className="auth-foot">© {new Date().getFullYear()} Purnama Textile</div>
      </div>
    </div>
  )
}