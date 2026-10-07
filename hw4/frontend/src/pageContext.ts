import { useLocation, useMatch, useSearchParams } from 'react-router-dom'
import type { PageContext } from './api'
import { useAssistantResults } from './assistantResults'

const PAGE_TYPES: Record<string, PageContext['page_type']> = {
  '/': 'home',
  '/products': 'products',
  '/about': 'about',
  '/login': 'login',
  '/signup': 'signup',
}

/**
 * Describes what the shopper is looking at, sent with every chat message so the agent
 * knows what "this" or "these" means. Only ids and short strings are sent; the backend
 * looks the products up in the database itself.
 */
export function usePageContext(): PageContext {
  const { pathname } = useLocation()
  const detail = useMatch('/products/:productId')
  const [searchParams] = useSearchParams()
  const { results } = useAssistantResults()

  return {
    path: pathname,
    page_type: detail ? 'product_detail' : (PAGE_TYPES[pathname] ?? 'other'),
    product_id: detail?.params.productId ?? null,
    search_query: pathname === '/products' ? searchParams.get('q') : null,
    shown_results_title: results?.title ?? null,
    shown_product_ids: results?.products.map((p) => p.product_id) ?? [],
  }
}
