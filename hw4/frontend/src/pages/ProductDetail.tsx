import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, fetchProducts, formatPrice, type Product, type ProductDetail } from '../api'
import { categoryOf, swatchFor } from '../categories'
import { openChat } from '../chatEvents'
import ProductCard from '../components/ProductCard'
import { ArrowLeftIcon, ArrowRightIcon, ChatIcon, ShieldIcon, StoreIcon, RulerIcon } from '../components/Icons'

const RELATED_COUNT = 4

export default function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [related, setRelated] = useState<Product[]>([])
  const [error, setError] = useState<string | null>(null)
  const [selectedSize, setSelectedSize] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return
    setProduct(null)
    setRelated([])
    setError(null)
    setSelectedSize(null)
    fetchProduct(productId)
      .then((p) => {
        setProduct(p)
        // "More like this": other in-stock items from the same category.
        const category = categoryOf(p.garment_type)
        if (category) {
          fetchProducts({ category: category.value })
            .then((list) =>
              setRelated(list.filter((x) => x.product_id !== p.product_id && x.total_stock > 0).slice(0, RELATED_COUNT)),
            )
            .catch(() => setRelated([]))
        }
      })
      .catch((e: Error) => setError(e.message === 'Not found' ? 'We couldn’t find that product.' : 'Could not load this product.'))
  }, [productId])

  if (error) {
    return (
      <section className="section">
        <p className="error">{error}</p>
        <Link to="/products" className="link-accent">
          <ArrowLeftIcon size={16} /> Back to products
        </Link>
      </section>
    )
  }
  if (!product) return <section className="section muted">Loading…</section>

  const category = categoryOf(product.garment_type)
  const selected = product.inventory.find((s) => s.size === selectedSize)

  return (
    <>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span className="sep">/</span>
        <Link to="/products">Shop</Link>
        {category && (
          <>
            <span className="sep">/</span>
            <Link to={`/products?category=${category.value}`}>{category.label}</Link>
          </>
        )}
        <span className="sep">/</span>
        <span aria-current="page">{product.name}</span>
      </nav>

      <section className="detail">
        <div className="detail-image">
          <img src={product.display_image_url || product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <span className="licensed">
            <ShieldIcon size={15} /> Officially licensed Yale apparel
          </span>
          <p className="detail-desc">{product.description}</p>

          <div className="detail-block">
            <h3>Colors</h3>
            <div className="chips">
              {product.colors.map((c) => (
                <span key={c} className="chip">
                  <span className="swatch" style={{ background: swatchFor(c) }} />
                  {c}
                </span>
              ))}
            </div>
          </div>

          <div className="detail-block">
            <h3>Sizes &amp; stock</h3>
            <div className="sizes">
              {product.inventory.map((s) => (
                <button
                  key={s.size}
                  className={`size ${s.quantity === 0 ? 'size-out' : ''} ${selectedSize === s.size ? 'size-selected' : ''}`}
                  disabled={s.quantity === 0}
                  onClick={() => setSelectedSize(s.size)}
                  aria-pressed={selectedSize === s.size}
                >
                  <span className="size-label">{s.size}</span>
                  <span className="size-qty">{s.quantity === 0 ? 'Sold out' : `${s.quantity} left`}</span>
                </button>
              ))}
            </div>
            <p className="stock-note">
              {product.total_stock === 0 ? (
                'This item is currently sold out in every size.'
              ) : selected ? (
                <>
                  <strong>In stock:</strong> {selected.quantity} left in size {selected.size}.
                </>
              ) : (
                `${product.total_stock} in stock across all sizes. Pick a size to see availability.`
              )}
            </p>
          </div>

          <div className="ask-item">
            <button className="btn btn-primary" onClick={openChat}>
              <ChatIcon size={17} /> Ask about this item
            </button>
            <span className="muted">Sizing, stock, or similar styles: our assistant knows which item you're viewing.</span>
          </div>

          <ul className="assurances">
            <li>
              <ShieldIcon size={18} /> Authentic, officially licensed Yale marks
            </li>
            <li>
              <RulerIcon size={18} /> Stock shown live from our store inventory
            </li>
            <li>
              <StoreIcon size={18} /> Find us at 57 Broadway, New Haven
            </li>
          </ul>
        </div>
      </section>

      {related.length > 0 && category && (
        <section className="section">
          <div className="section-head">
            <div>
              <p className="eyebrow">More like this</p>
              <h2>More {category.label.toLowerCase()}</h2>
            </div>
            <Link to={`/products?category=${category.value}`} className="link-accent">
              Shop all {category.label.toLowerCase()} <ArrowRightIcon size={16} />
            </Link>
          </div>
          <div className="product-grid">
            {related.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}
    </>
  )
}
