import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import {
  clearChatHistory,
  fetchChatHistory,
  sendChat,
  type ChatTurn,
  type PageContext,
  type ProductResults,
} from '../api'
import { useAssistantResults } from '../assistantResults'
import { useAuth } from '../auth'
import { OPEN_CHAT_EVENT } from '../chatEvents'
import { usePageContext } from '../pageContext'
import { BagIcon, ChatIcon, CheckIcon, CloseIcon, Crest, SendIcon } from './Icons'

function TypingDots() {
  return (
    <span className="typing" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  )
}

interface ChatMessage extends ChatTurn {
  results?: ProductResults | null
  verifiedPrices?: number // prices the backend's reply check confirmed against the database
  error?: boolean
  local?: boolean // shown in the widget only (greetings), never sent to the agent
}

// How many past turns a guest's browser sends with each message (keeps requests small).
// Logged-in shoppers' history is loaded by the server from the database instead.
const HISTORY_LIMIT = 20

/** One-tap starter questions that fit the page the shopper is on. */
function suggestionsFor(pageType: PageContext['page_type'], hasCardsOnPage: boolean): string[] {
  if (pageType === 'product_detail') {
    return ['Is this in stock in M?', 'What sizes are left?', 'Show me similar items']
  }
  if (hasCardsOnPage) {
    return ['Which of these is cheapest?', 'Which are in stock in M?', 'What hoodies do you have?']
  }
  return ['What hoodies do you have?', 'Bulldog gear under $60', 'Gifts for a Yale parent']
}

function greeting(firstName?: string, returning = false): ChatMessage {
  const content = returning
    ? `Welcome back${firstName ? `, ${firstName}` : ''}! Your earlier chat is above. Pick up where you left off, or start a new chat.`
    : `Hi${firstName ? ` ${firstName}` : ''}! I'm the Campus Customs shopping assistant. Ask me about hoodies, tees, sizes, or prices.`
  return { role: 'assistant', content, local: true }
}

export default function ChatWidget() {
  const { user, token } = useAuth()
  const assistantResults = useAssistantResults()
  const page = usePageContext()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>(() => [greeting()])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Reset the conversation when someone logs in or out...
  const [chatOwner, setChatOwner] = useState(user?.id)
  if (chatOwner !== user?.id) {
    setChatOwner(user?.id)
    setMessages([greeting(user?.first_name)])
    setLoadingHistory(Boolean(user && token))
  }

  // ...and for logged-in shoppers, load their saved chat from the database.
  useEffect(() => {
    if (!user || !token) return
    let cancelled = false
    fetchChatHistory(token)
      .then((saved) => {
        if (cancelled || saved.length === 0) return
        const restored: ChatMessage[] = saved.map((m) => ({ role: m.role, content: m.content, results: m.results }))
        setMessages([...restored, greeting(user.first_name, true)])
      })
      .catch(() => {
        // Keep the plain greeting if history can't be loaded.
      })
      .finally(() => !cancelled && setLoadingHistory(false))
    return () => {
      cancelled = true
    }
  }, [user, token])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking, open])

  // Other components (e.g. "Ask about this item" on product pages) can open the chat.
  useEffect(() => {
    const openChat = () => setOpen(true)
    window.addEventListener(OPEN_CHAT_EVENT, openChat)
    return () => window.removeEventListener(OPEN_CHAT_EVENT, openChat)
  }, [])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || thinking) return
    const history: ChatTurn[] = messages
      .filter((m) => !m.error && !m.local)
      .slice(-HISTORY_LIMIT)
      .map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setThinking(true)
    try {
      const res = await sendChat(text, history, token, page)
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: res.reply, results: res.results, verifiedPrices: res.verified_prices },
      ])
      // Structured results go straight onto the page as regular product cards.
      if (res.results) assistantResults.show(res.results)
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: (err as Error).message, error: true }])
    } finally {
      setThinking(false)
    }
  }

  async function handleNewChat() {
    if (!token || thinking) return
    if (!window.confirm('Start a new chat? Your saved conversation will be deleted.')) return
    try {
      await clearChatHistory(token)
      setMessages([greeting(user?.first_name)])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: (err as Error).message, error: true }])
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" aria-label="Shopping assistant">
          <header className="chat-header">
            <span className="chat-avatar">
              <Crest size={24} />
            </span>
            <div className="chat-title">
              <strong>Campus Customs Assistant</strong>
              <span className="chat-status">
                {user ? `Chat saved to ${user.first_name}'s account` : 'Guest chat · not saved'}
              </span>
            </div>
            <div className="chat-header-actions">
              {user && (
                <button className="chat-new" onClick={handleNewChat} disabled={thinking} title="Start a new chat">
                  New chat
                </button>
              )}
              <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
                <CloseIcon size={18} />
              </button>
            </div>
          </header>
          <div className="chat-messages">
            {loadingHistory && (
              <div className="chat-bubble chat-assistant chat-thinking">
                <TypingDots /> Loading your chat…
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-row chat-row-${m.role}`}>
                <div className={`chat-bubble chat-${m.role} ${m.error ? 'chat-error' : ''} ${m.local ? 'chat-local' : ''}`}>
                  {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
                </div>
                {Boolean(m.verifiedPrices) && (
                  <span className="chat-verified" title="Every price in this reply was checked against the store database">
                    <CheckIcon size={13} /> {m.verifiedPrices === 1 ? 'Price' : 'Prices'} verified with our store database
                  </span>
                )}
                {m.results && (
                  <button
                    className="chat-results-chip"
                    onClick={() => assistantResults.show(m.results!)}
                    title="Show these products on the page"
                  >
                    <BagIcon size={14} /> {m.results.total} {m.results.total === 1 ? 'product' : 'products'} · Show on
                    page
                  </button>
                )}
              </div>
            ))}
            {thinking && (
              <div className="chat-bubble chat-assistant chat-thinking">
                <TypingDots /> Checking the shelves…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          {!thinking && !loadingHistory && (
            <div className="chat-suggestions" aria-label="Suggested questions">
              {suggestionsFor(page.page_type, page.shown_product_ids.length > 0).map((s) => (
                <button key={s} className="chat-suggestion" onClick={() => void send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={page.page_type === 'product_detail' ? 'Ask about this item…' : 'Ask about products…'}
              aria-label="Message"
              maxLength={1000}
            />
            <button className="chat-send" type="submit" disabled={!input.trim() || thinking} aria-label="Send">
              <SendIcon size={18} />
            </button>
          </form>
        </section>
      )}
      <button
        className={`chat-toggle ${open ? 'chat-toggle-open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? (
          <CloseIcon size={22} />
        ) : (
          <>
            <ChatIcon size={22} />
            <span className="chat-toggle-label">Ask our assistant</span>
            <span className="chat-toggle-dot" />
          </>
        )}
      </button>
    </div>
  )
}
