import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Crest, MenuIcon, CloseIcon } from './Icons'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Shop' },
  { to: '/about', label: 'About Us' },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  // Close the mobile menu on navigation.
  const [lastPath, setLastPath] = useState(pathname)
  if (lastPath !== pathname) {
    setLastPath(pathname)
    setMenuOpen(false)
  }

  // Add a soft shadow once the page scrolls under the header.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="announce">
        <strong>Officially licensed Yale apparel</strong> · Visit us at 57 Broadway, New Haven
      </div>
      <div className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
        <div className="nav-inner">
          <Link to="/" className="brand" aria-label="Campus Customs home">
            <Crest size={32} />
            <span className="brand-text">
              <span className="brand-name">Campus Customs</span>
              <span className="brand-sub">Yale Apparel · New Haven</span>
            </span>
          </Link>
          <button
            className="nav-toggle"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <CloseIcon /> : <MenuIcon />}
          </button>
          <div className={`nav-menu ${menuOpen ? 'open' : ''}`}>
            <nav className="nav-links" aria-label="Main">
              {links.map((l) => (
                <NavLink key={l.to} to={l.to} end={l.end} className="nav-link">
                  {l.label}
                </NavLink>
              ))}
            </nav>
            <div className="nav-auth">
              {user ? (
                <>
                  <span className="nav-greeting">
                    Hi, <strong>{user.first_name}</strong>
                  </span>
                  <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/login" className="nav-link">
                    Log in
                  </NavLink>
                  <NavLink to="/signup" className="btn btn-primary btn-sm">
                    Create account
                  </NavLink>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
