import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Users, UsersRound, LogOut } from 'lucide-react'
import Logo from './Logo'
import Avatar from './ui/Avatar'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/dashboard" className="navbar-brand">
          <Logo size={28} />
          <span className="brand-name">DevMatch</span>
        </NavLink>

        <nav className="navbar-links">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={16} />
            <span>My Profile</span>
          </NavLink>
          <NavLink to="/teammates" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Users size={16} />
            <span>Find Teammates</span>
          </NavLink>
          <NavLink to="/teams" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <UsersRound size={16} />
            <span>Teams</span>
          </NavLink>
        </nav>

        <div className="navbar-actions">
          <div className="navbar-user">
            <Avatar name={user?.username || ''} size={32} />
            <span className="navbar-username">{user?.username}</span>
          </div>
          <button className="nav-logout" onClick={handleLogout} title="Log out">
            <LogOut size={17} />
          </button>
        </div>
      </div>
    </header>
  )
}
