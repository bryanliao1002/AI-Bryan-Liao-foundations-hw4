import { useEffect } from 'react'
import { Route, Routes, useLocation, useMatch } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import AssistantResults from './components/AssistantResults'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetailPage from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Signup from './pages/Signup'
import NotFound from './pages/NotFound'

export default function App() {
  // Assistant results sit at the top of most pages. On a product page they move below
  // the product so the detail view (opened from one of those cards) comes first.
  const onDetailPage = useMatch('/products/:productId') !== null
  const { pathname } = useLocation()

  // Start each new page at the top (e.g. after clicking a product card lower down).
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="app">
      <Navbar />
      <main className="main">
        {!onDetailPage && <AssistantResults />}
        {/* Keyed by path so each new page fades in once (filters on the same page don't re-animate). */}
        <div key={pathname} className="page-enter">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:productId" element={<ProductDetailPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
        {onDetailPage && <AssistantResults />}
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
