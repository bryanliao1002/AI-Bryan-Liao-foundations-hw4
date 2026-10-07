import { Link } from 'react-router-dom'
import { CATEGORIES } from '../categories'
import { openChat } from '../chatEvents'
import { Crest } from './Icons'

const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="footer">
      <div className="bleed-inner footer-grid">
        <div>
          <Link to="/" className="brand">
            <Crest size={30} />
            <span className="brand-text">
              <span className="brand-name">Campus Customs</span>
              <span className="brand-sub">Yale Apparel · New Haven</span>
            </span>
          </Link>
          <p className="footer-blurb">
            Officially licensed Yale hoodies, crewnecks, tees and outerwear for students, alumni and families.
          </p>
        </div>
        <div className="footer-col">
          <h4>Shop</h4>
          {CATEGORIES.slice(0, 5).map((c) => (
            <Link key={c.value} to={`/products?category=${c.value}`}>
              {c.label}
            </Link>
          ))}
        </div>
        <div className="footer-col">
          <h4>Help</h4>
          <button onClick={openChat}>Ask our assistant</button>
          <Link to="/about">About us</Link>
          <Link to="/login">Your account</Link>
        </div>
        <div className="footer-col">
          <h4>Visit</h4>
          <span>57 Broadway</span>
          <span>New Haven, CT 06511</span>
        </div>
      </div>
      <div className="bleed-inner footer-bottom">© {YEAR} Campus Customs · Class project demo</div>
    </footer>
  )
}
