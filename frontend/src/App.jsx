import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import PPIC from './pages/PPIC.jsx'
import Purchasing from './pages/Purchasing.jsx'
import Warehouse from './pages/Warehouse.jsx'
import Production from './pages/Production.jsx'
import Distribution from './pages/Distribution.jsx'
import Finance from './pages/Finance.jsx'
import { api, getToken } from './api.js'

function RequireAuth({ children }) {
  const location = useLocation()
  if (!getToken()) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

export default function App() {
  const [user, setUser] = useState(null)
  const [authing, setAuthing] = useState(true)

  useEffect(() => {
    if (getToken()) {
      api('/auth/me')
        .then(setUser)
        .catch(() => setUser(null))
        .finally(() => setAuthing(false))
    } else {
      setAuthing(false)
    }
  }, [])

  if (authing) return <div className="loading" style={{ padding: 40 }}>Memuat…</div>

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={setUser} />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout user={user} onLogout={() => { setUser(null) }}>
              <Dashboard user={user} />
            </Layout>
          </RequireAuth>
        }
      />
      <Route path="/ppic" element={<RequireAuth><Layout user={user}><PPIC /></Layout></RequireAuth>} />
      <Route path="/purchasing" element={<RequireAuth><Layout user={user}><Purchasing /></Layout></RequireAuth>} />
      <Route path="/warehouse" element={<RequireAuth><Layout user={user}><Warehouse /></Layout></RequireAuth>} />
      <Route path="/produksi" element={<RequireAuth><Layout user={user}><Production /></Layout></RequireAuth>} />
      <Route path="/distribusi" element={<RequireAuth><Layout user={user}><Distribution /></Layout></RequireAuth>} />
      <Route path="/finance" element={<RequireAuth><Layout user={user}><Finance /></Layout></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}