import { CheckIcon, Crest } from './Icons'

/** Yale-blue side panel for the Log in / Create account pages: why an account is worth it. */
export default function AuthAside({ title }: { title: string }) {
  return (
    <aside className="auth-aside">
      <Crest size={40} />
      <h2>{title}</h2>
      <p>Your Campus Customs account makes shopping for Yale gear faster.</p>
      <ul>
        <li>
          <CheckIcon size={18} /> Your chat with our assistant is saved, so you can pick up where you left off
        </li>
        <li>
          <CheckIcon size={18} /> Personal help: the assistant knows who you are and what you're looking at
        </li>
        <li>
          <CheckIcon size={18} /> Live prices and size stock on every Yale style
        </li>
      </ul>
    </aside>
  )
}
