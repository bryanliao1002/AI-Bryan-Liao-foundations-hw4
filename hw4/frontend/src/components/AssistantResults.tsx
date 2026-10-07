import { useEffect, useRef } from 'react'
import { useAssistantResults } from '../assistantResults'
import { ChatIcon } from './Icons'
import ProductCard from './ProductCard'

/** Product cards picked by the chatbot, rendered with the same ProductCard as the Products page. */
export default function AssistantResults() {
  const { results, version, clear } = useAssistantResults()
  const ref = useRef<HTMLElement>(null)
  // The version already on screen when this component mounted (e.g. after navigating
  // to a product page), so only *new* results trigger a scroll.
  const seenVersion = useRef(version)

  useEffect(() => {
    if (version !== seenVersion.current) {
      seenVersion.current = version
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [version])

  if (!results) return null

  return (
    <section ref={ref} key={version} className="assistant-results" aria-live="polite">
      <div className="section-head">
        <div>
          <p className="eyebrow">
            <ChatIcon size={15} /> From your shopping assistant
          </p>
          <h2>{results.title}</h2>
          <p className="muted">
            {results.total} {results.total === 1 ? 'product' : 'products'}
          </p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={clear}>
          Clear results
        </button>
      </div>
      <div className="product-grid">
        {results.products.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  )
}
