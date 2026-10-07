import { useEffect, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product, type ProductFilters } from '../api'
import { CATEGORIES as SHOP_CATEGORIES } from '../categories'
import { SearchIcon } from '../components/Icons'
import ProductCard from '../components/ProductCard'

const CATEGORIES = [{ value: '', label: 'All' }, ...SHOP_CATEGORIES]
const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
const PRICE_CAPS = ['40', '60', '80']
const SORTS = [
  { value: 'name', label: 'Name (A–Z)' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
]
const FILTER_KEYS = ['q', 'category', 'size', 'max_price', 'sort'] as const

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters: ProductFilters = Object.fromEntries(
    FILTER_KEYS.map((k) => [k, searchParams.get(k) ?? '']),
  )
  const filterKey = searchParams.toString()
  const [input, setInput] = useState(filters.q ?? '')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchProducts(Object.fromEntries(new URLSearchParams(filterKey)))
      .then(setProducts)
      .catch(() => setError('Could not load products. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [filterKey])

  // Update one filter in the URL (empty value removes it), keeping the others.
  function setFilter(key: (typeof FILTER_KEYS)[number], value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next)
  }

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setFilter('q', input.trim())
  }

  function clearFilters() {
    setInput('')
    setSearchParams({})
  }

  const hasFilters = FILTER_KEYS.some((k) => filters[k] && !(k === 'sort' && filters[k] === 'name'))
  const categoryLabel = CATEGORIES.find((c) => c.value === filters.category)?.label
  const summary = [
    filters.q && `matching “${filters.q}”`,
    filters.category && categoryLabel,
    filters.size && `in stock in ${filters.size}`,
    filters.max_price && `under $${filters.max_price}`,
  ].filter(Boolean)

  return (
    <section>
      <div className="page-head section-head">
        <div>
          <p className="eyebrow">Shop Campus Customs</p>
          <h1>{categoryLabel && filters.category ? `Yale ${categoryLabel}` : 'All Yale apparel'}</h1>
          <p className="muted">Officially licensed hoodies, crewnecks, tees and outerwear, with live size stock.</p>
        </div>
        <form className="search" onSubmit={handleSearch}>
          <div className="search-field">
            <SearchIcon size={17} />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Search bulldog, hockey, Berkeley…"
              aria-label="Search products"
            />
          </div>
          <button className="btn btn-primary btn-sm" type="submit">
            Search
          </button>
        </form>
      </div>

      <div className="filters">
        <div className="category-chips" role="group" aria-label="Category">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              className={`filter-chip ${(filters.category ?? '') === c.value ? 'filter-chip-active' : ''}`}
              onClick={() => setFilter('category', c.value)}
              aria-pressed={(filters.category ?? '') === c.value}
            >
              {c.label}
            </button>
          ))}
        </div>
        <div className="filter-selects">
          <label>
            In stock in size
            <select value={filters.size} onChange={(e) => setFilter('size', e.target.value)}>
              <option value="">Any size</option>
              {SIZES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Price
            <select value={filters.max_price} onChange={(e) => setFilter('max_price', e.target.value)}>
              <option value="">Any price</option>
              {PRICE_CAPS.map((p) => (
                <option key={p} value={p}>
                  Under ${p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sort by
            <select value={filters.sort || 'name'} onChange={(e) => setFilter('sort', e.target.value === 'name' ? '' : e.target.value)}>
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          {hasFilters && (
            <button className="btn btn-ghost btn-sm" onClick={clearFilters}>
              Clear filters
            </button>
          )}
        </div>
      </div>

      {loading && <p className="muted">Loading products…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <>
          <p className="muted results-count">
            {products.length} {products.length === 1 ? 'item' : 'items'}
            {summary.length > 0 && <> · {summary.join(' · ')}</>}
          </p>
          {products.length === 0 ? (
            <div className="empty-state">
              <p>No products match these filters.</p>
              <button className="btn btn-primary btn-sm" onClick={clearFilters}>
                Clear filters
              </button>
            </div>
          ) : (
            <div className="product-grid">
              {products.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
