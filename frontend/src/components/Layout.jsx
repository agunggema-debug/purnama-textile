import { NavLink } from 'react-router-dom'
import { clearToken } from '../api.js'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▤' },
  { to: '/ppic', label: 'PPIC', icon: '◈' },
  { to: '/purchasing', label: 'Purchasing', icon: '⟳' },
  { to: '/warehouse', label: 'Warehouse', icon: '▣' },
  { to: '/produksi', label: 'Produksi', icon: '⚙' },
  { to: '/distribusi', label: 'Distribusi & Logistik', icon: '➤' },
  { to: '/finance', label: 'Finance & Accounting', icon: '₨' },
]

export default function Layout({ user, onLogout, children }) {
  const logout = () => {
    clearToken()
    if (typeof onLogout === 'function') onLogout()
    // Buang seluruh memori aplikasi dengan muat ulang halaman login.
    window.location.assign('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div className="titles">
            <strong>Purnama Textile</strong>
            <small>ERP &amp; SCM · On-Premise</small>
          </div>
        </div>
        <div className="menu-label">Menu</div>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === '/'}>
              <span className="icon">{n.icon}</span>
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
        <button className="logout" onClick={logout}>⏻ Keluar</button>
      </aside>
      <main className="main">
        <div className="topbar">
          <span />
          <div className="user">
            {user?.full_name || (user?.username || '')} · <span className="badge badge-blank">{user?.role}</span>
          </div>
        </div>
        {children}
      </main>
    </div>
  )
}