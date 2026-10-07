export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  display_image_url: string // same photo on the storefront's neutral tile (backend/images.py)
  price: number
  total_stock: number
  inventory?: SizeStock[]
}

export interface ProductDetail extends Product {
  inventory: SizeStock[]
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

export interface AuthResponse {
  token: string
  user: User
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(res.status === 404 ? 'Not found' : `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

// Turn FastAPI error bodies (string detail or validation list) into one readable message.
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((d: { msg: string }) => d.msg.replace(/^Value error, /, ''))
        .join(' ')
    }
  } catch {
    // fall through
  }
  return `Request failed (${res.status})`
}

async function postJson<T>(url: string, data: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json() as Promise<T>
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return postJson<AuthResponse>('/api/auth/login', { email, password })
}

export function signup(data: {
  first_name: string
  last_name: string
  email: string
  password: string
}): Promise<AuthResponse> {
  return postJson<AuthResponse>('/api/auth/signup', data)
}

export async function fetchMe(token: string): Promise<User> {
  const res = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json() as Promise<User>
}

export interface ProductFilters {
  q?: string
  category?: string
  size?: string
  max_price?: string
  sort?: string
}

export function fetchProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value)
  }
  const qs = params.toString()
  return getJson<Product[]>(`/api/products${qs ? `?${qs}` : ''}`)
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

/** Products the assistant wants shown on the page (see backend models.ProductResults). */
export interface ProductResults {
  title: string
  total: number
  products: ProductDetail[]
}

/** The /api/chat contract (see backend models.ChatResponse). */
export interface ChatResponse {
  reply: string
  results: ProductResults | null
  saved: boolean
  verified_prices: number
}

/** What the shopper is looking at (see backend models.PageContext). */
export interface PageContext {
  path: string
  page_type: 'home' | 'products' | 'product_detail' | 'about' | 'login' | 'signup' | 'other'
  product_id: string | null
  search_query: string | null
  shown_results_title: string | null
  shown_product_ids: string[]
}

export interface SavedChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  results: ProductResults | null
  created_at: string
}

function authHeaders(token: string | null): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function sendChat(
  message: string,
  history: ChatTurn[],
  token: string | null,
  page: PageContext,
): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify({ message, history, page }),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.json() as Promise<ChatResponse>
}

export async function fetchChatHistory(token: string): Promise<SavedChatMessage[]> {
  const res = await fetch('/api/chat/history', { headers: authHeaders(token) })
  if (!res.ok) throw new Error(await errorMessage(res))
  return ((await res.json()) as { messages: SavedChatMessage[] }).messages
}

export async function clearChatHistory(token: string): Promise<void> {
  const res = await fetch('/api/chat/history', { method: 'DELETE', headers: authHeaders(token) })
  if (!res.ok) throw new Error(await errorMessage(res))
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}
