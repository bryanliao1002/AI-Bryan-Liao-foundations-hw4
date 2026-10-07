import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'
import { ArrowRightIcon } from './Icons'

// Below this many units across all sizes, the card shows a "Low stock" badge (real inventory data).
const LOW_STOCK = 30

export default function ProductCard({ product }: { product: Product }) {
  const soldOut = product.total_stock === 0
  const lowStock = !soldOut && product.total_stock <= LOW_STOCK
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        <img src={product.display_image_url || product.image_url} alt={product.name} loading="lazy" />
        {soldOut && <span className="badge badge-muted">Sold out</span>}
        {lowStock && <span className="badge badge-low">Low stock</span>}
        <span className="product-card-cta" aria-hidden="true">
          View details <ArrowRightIcon size={14} />
        </span>
      </div>
      <div className="product-card-body">
        <p className="product-card-type">{product.garment_type}</p>
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.description}</p>
        <div className="product-card-foot">
          <p className="price">{formatPrice(product.price)}</p>
          {product.inventory && product.inventory.length > 0 && (
            <div className="size-dots" aria-label="Sizes in stock">
              {product.inventory.map((s) => (
                <span
                  key={s.size}
                  className={`size-dot ${s.quantity === 0 ? 'size-dot-out' : ''}`}
                  title={s.quantity === 0 ? `${s.size}: sold out` : `${s.size}: ${s.quantity} left`}
                >
                  {s.size}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
