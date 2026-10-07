import { Link } from 'react-router-dom'
import { openChat } from '../chatEvents'
import { ArrowRightIcon, ChatIcon, PinIcon, ShieldIcon, SparkIcon } from '../components/Icons'

export default function About() {
  return (
    <>
      <section className="page-hero bleed">
        <div className="bleed-inner">
          <p className="eyebrow">About Campus Customs</p>
          <h1>Made for the Yale community, right on Broadway.</h1>
          <p>
            We're a local shop a short walk from Old Campus, here to help you rep Yale, whether it's your first week or
            your fiftieth reunion.
          </p>
        </div>
      </section>

      <section className="section prose">
        <p className="eyebrow">Our story</p>
        <h2>Gear with a sense of place</h2>
        <p>
          Campus Customs makes it easy to wear your Yale pride. A first-year picking out their first hoodie, a parent
          visiting for the weekend, an alum who wants something new for The Game: our shelves are stocked for all of
          them.
        </p>
        <p>
          We focus on officially licensed apparel: heavyweight hoodies, classic crewnecks, everyday tees, quarter-zips
          and fleece. You'll find big block-letter YALE designs, vintage bulldog graphics, residential college
          crests, varsity team gear and pieces made for Harvard–Yale weekend.
        </p>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">What we care about</p>
            <h2>Our promise</h2>
          </div>
        </div>
        <div className="values-grid">
          <div className="value-card">
            <span className="trust-icon">
              <SparkIcon />
            </span>
            <h3>School spirit</h3>
            <p>Boola Boola is more than a song. Every piece should feel like part of campus.</p>
          </div>
          <div className="value-card">
            <span className="trust-icon">
              <ShieldIcon />
            </span>
            <h3>Honest information</h3>
            <p>Prices and size availability on this site come straight from our store inventory.</p>
          </div>
          <div className="value-card">
            <span className="trust-icon">
              <ChatIcon />
            </span>
            <h3>Friendly help</h3>
            <p>Stop by the shop or ask our online assistant. We'll help you find the right fit.</p>
          </div>
        </div>
      </section>

      <section className="visit">
        <div>
          <h2>Visit us</h2>
          <p>
            <PinIcon size={16} style={{ verticalAlign: '-3px', marginRight: 6 }} />
            57 Broadway, New Haven, CT 06511
          </p>
        </div>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-light">
            Browse products <ArrowRightIcon size={16} />
          </Link>
          <button className="btn btn-outline-light" onClick={openChat}>
            <ChatIcon size={17} /> Ask our assistant
          </button>
        </div>
      </section>
    </>
  )
}
