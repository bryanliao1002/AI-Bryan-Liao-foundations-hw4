import { Link } from 'react-router-dom'
import { ArrowLeftIcon } from '../components/Icons'

export default function NotFound() {
  return (
    <section className="not-found">
      <p className="display">404</p>
      <h1>We couldn't find that page</h1>
      <p className="muted">It may have moved, or the link might be off by a letter.</p>
      <Link to="/" className="btn btn-primary">
        <ArrowLeftIcon size={16} /> Back home
      </Link>
    </section>
  )
}
