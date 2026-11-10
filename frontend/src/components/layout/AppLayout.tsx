import { Outlet, NavLink, Link, useLocation, useNavigate } from 'react-router-dom'
import { FileSearch, LayoutDashboard, GitCompare, History, LogOut, Menu, X, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'

const navigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/checker', label: 'Plagiarism checker', icon: FileSearch },
  { to: '/compare', label: 'Compare documents', icon: GitCompare },
  { to: '/history', label: 'Analysis history', icon: History },
]

export function AppLayout() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const title = navigation.find((item) => item.to === location.pathname)?.label ?? 'Workspace'
  return (
    <div className="saas-shell">
      <aside className={`saas-sidebar ${open ? 'open' : ''}`}>
        <Link to="/" className="saas-brand"><span className="brand-icon"><Sparkles size={20} /></span><span><b>PlagiarismAI</b><small>Research-grade text intelligence</small></span></Link>
        <nav className="saas-nav">
          <span className="nav-caption">Workspace</span>
          {navigation.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => `saas-nav-link ${isActive ? 'active' : ''}`}><Icon size={18} /><span>{label}</span></NavLink>)}
        </nav>
        <div className="sidebar-note"><Sparkles size={16} /><span>Compare against your available document corpus. No internet-wide claims.</span></div>
        <button className="saas-logout" onClick={() => { logout(); navigate('/login') }}><LogOut size={16} /> Sign out</button>
      </aside>
      <div className="saas-main">
        <header className="saas-topbar"><button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">{open ? <X /> : <Menu />}</button><div><span className="topbar-kicker">PlagiarismAI workspace</span><h2>{title}</h2></div><div className="topbar-user"><span>{user?.name || user?.email || 'Researcher'}</span><span className="avatar">{(user?.name || user?.email || 'R').charAt(0).toUpperCase()}</span></div></header>
        <main className="saas-content"><Outlet /></main>
      </div>
    </div>
  )
}
