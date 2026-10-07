import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, formatPrice, type Product } from '../api'
import { CATEGORIES, categoryOf } from '../categories'
import { openChat } from '../chatEvents'
import ProductCard from '../components/ProductCard'
import { ArrowRightIcon, ChatIcon, CheckIcon, PinIcon, RulerIcon, ShieldIcon, StoreIcon } from '../components/Icons'

const HERO_IDS = ['basic-hoodie-big-yale', 'district-vit-crewneck-vintage-standing-bulldog', 'boola-boola-t-shirt']
const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  'boola-boola-t-shirt',
  'district-vit-hoodie-vintage-bulldog',
  '2025-yale-vs-harvard-t-shirt',
]

export default function Home() {
  const [all, setAll] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts({})
      .then(setAll)
      .catch(() => setAll([]))
  }, [])

  const byId = (id: string) => all.find((p) => p.product_id === id)
  const pick = (ids: string[]) => ids.map(byId).filter((p): p is Product => p !== undefined)
  const hero = pick(HERO_IDS)
  const featured = pick(FEATURED_IDS)
  const categoryCount = (value: string) => all.filter((p) => categoryOf(p.garment_type)?.value === value).length
  const shopCategories = CATEGORIES.filter((c) => c.feature)

  return (
    <>
      <section className="hero bleed">
        <div className="bleed-inner hero-grid">
          <div>
            <p className="eyebrow">Official Yale apparel · New Haven</p>
            <h1>
              Wear the Blue,
              <br />
              <em>every day.</em>
            </h1>
            <p className="hero-sub">
              Heavyweight hoodies, classic crewnecks and game-day tees for students, alumni and every proud Yale
              family. Real stock from our Broadway shop, ready when you are.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-light">
                Shop the collection <ArrowRightIcon size={16} />
              </Link>
              <button className="btn btn-outline-light" onClick={openChat}>
                <ChatIcon size={17} /> Ask our assistant
              </button>
            </div>
            <div className="hero-meta">
              <div>
                <strong>{all.length || '100+'}</strong> Yale styles
              </div>
              <div>
                <strong>XS–XXL</strong> Live size stock
              </div>
              <div>
                <strong>57</strong> Broadway, New Haven
              </div>
            </div>
          </div>
          <div className="hero-collage" aria-hidden="true">
            {hero.map((p) => (
              <Link key={p.product_id} to={`/products/${p.product_id}`} className="collage-tile" tabIndex={-1}>
                <img src={p.display_image_url} alt="" />
                <span className="collage-tag">
                  {p.name.length > 22 ? `${p.name.slice(0, 20)}…` : p.name}
                  <span>{formatPrice(p.price)}</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="trust bleed">
        <div className="bleed-inner trust-grid">
          <div className="trust-item">
            <span className="trust-icon">
              <ShieldIcon />
            </span>
            <span>
              <strong>Officially licensed</strong>Authentic Yale marks
            </span>
          </div>
          <div className="trust-item">
            <span className="trust-icon">
              <RulerIcon />
            </span>
            <span>
              <strong>Live size stock</strong>XS through XXL, updated from the store
            </span>
          </div>
          <div className="trust-item">
            <span className="trust-icon">
              <ChatIcon />
            </span>
            <span>
              <strong>Shopping assistant</strong>Real prices, real answers
            </span>
          </div>
          <div className="trust-item">
            <span className="trust-icon">
              <StoreIcon />
            </span>
            <span>
              <strong>Local shop</strong>57 Broadway, New Haven
            </span>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Shop by category</p>
            <h2>Find your fit</h2>
          </div>
          <Link to="/products" className="link-accent">
            View all products <ArrowRightIcon size={16} />
          </Link>
        </div>
        <div className="category-grid">
          {shopCategories.map((c) => {
            const p = byId(c.feature)
            return (
              <Link key={c.value} to={`/products?category=${c.value}`} className="category-tile">
                {p ? <img src={p.display_image_url} alt="" loading="lazy" /> : <div style={{ aspectRatio: '1' }} />}
                <span className="category-label">
                  {c.label}
                  <small>{categoryCount(c.value) || ''}</small>
                </span>
              </Link>
            )
          })}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Fan favorites</p>
            <h2>Campus classics</h2>
          </div>
          <Link to="/products" className="link-accent">
            Shop all <ArrowRightIcon size={16} />
          </Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="promo">
        <div>
          <p className="eyebrow">Your personal shopper</p>
          <h2>Not sure what fits? Just ask.</h2>
          <p className="muted">
            Our assistant checks live prices and size stock, finds similar styles when your size is gone, and
            remembers your conversation when you're logged in.
          </p>
          <button className="btn btn-primary" onClick={openChat}>
            <ChatIcon size={17} /> Start a chat
          </button>
        </div>
        <div className="promo-chat" aria-hidden="true">
          <div className="chat-row chat-row-user">
            <div className="chat-bubble chat-user">Do you have the Basic Hoodie Big Yale in medium?</div>
          </div>
          <div className="chat-row chat-row-assistant">
            <div className="chat-bubble chat-assistant">
              Yes! The <strong>Basic Hoodie Big Yale</strong> is in stock in M, and it's{' '}
              <strong>{byId('basic-hoodie-big-yale') ? formatPrice(byId('basic-hoodie-big-yale')!.price) : '$68.00'}</strong>.
            </div>
            <span className="chat-verified">
              <CheckIcon size={13} /> Prices verified with our store database
            </span>
          </div>
        </div>
      </section>

      <section className="visit">
        <div>
          <h2>Visit us on Broadway</h2>
          <p>
            <PinIcon size={16} style={{ verticalAlign: '-3px', marginRight: 6 }} />
            57 Broadway, New Haven, CT 06511. A short walk from Old Campus.
          </p>
        </div>
        <Link to="/about" className="btn btn-light">
          Our story <ArrowRightIcon size={16} />
        </Link>
      </section>
    </>
  )
}
