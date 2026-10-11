import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { House, Users, UsersRound, LogOut, MessageCircle } from 'lucide-react'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import Avatar from './ui/Avatar'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [pendingChats, setPendingChats] = useState(0)

  useEffect(() => {
    if (!isAuthenticated) {
      setPendingChats(0)
      return
    }
    api
      .chatOverview()
      .then((o) => setPendingChats((o.incoming_requests || []).length))
      .catch(() => {})
  }, [isAuthenticated, location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/home" className="navbar-brand">
          <Logo size={28} />
          <span className="brand-name">Dev<span className="brand-accent">Match</span></span>
        </NavLink>

        <nav className="navbar-links" aria-label="Primary">
          <NavLink to="/home" aria-label="Home" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <House size={16} />
            <span>Home</span>
          </NavLink>
          <NavLink to="/teammates" aria-label="Find Teammates" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Users size={16} />
            <span>Find Teammates</span>
          </NavLink>
          <NavLink to="/teams" aria-label="Teams" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <UsersRound size={16} />
            <span>Teams</span>
          </NavLink>
          <NavLink to="/messages" aria-label="Messages" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <MessageCircle size={16} />
            <span>Messages</span>
            {pendingChats > 0 && <span className="tab-count">{pendingChats}</span>}
          </NavLink>
        </nav>

        <div className="navbar-actions">
          <NavLink to="/dashboard" className="navbar-user" aria-label="Open my profile" title="My profile">
            {user ? (
              <>
                <Avatar name={user.username || ''} size={32} />
                <span className="navbar-username">{user.username}</span>
              </>
            ) : (
              <>
                <div className="skeleton" style={{ width: 32, height: 32, borderRadius: '50%' }} />
                <span className="skeleton" style={{ width: 70, height: 14 }} />
              </>
            )}
          </NavLink>
          <button className="nav-logout" onClick={handleLogout} title="Log out" aria-label="Log out">
            <LogOut size={17} />
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
