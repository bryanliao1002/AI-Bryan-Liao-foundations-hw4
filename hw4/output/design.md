# Campus Customs — Visual Design

**Goal:** make the site feel like a real, premium Yale merchandise store instead of a class project, so shoppers trust it, browse longer, and are more likely to buy. Every feature from Problems 3–9 still works (re-tested end to end after the redesign).

## 1. Brand and color
- **Yale-inspired palette:** deep **Yale Blue `#00356B`** for the brand, buttons and active states. **White** for content. **Warm neutrals** (`#FAF8F4` paper, `#F6F4F0` product tiles, `#E6E2DA` lines) instead of cold grays. Green is used only for "verified / in stock", and amber only for "Low stock".
- **Crest logo:** a shield with a serif "CC", used in the header, footer, favicon, the chat avatar and the account pages.
- **Announcement bar:** a dark-blue strip at the top: "Officially licensed Yale apparel · Visit us at 57 Broadway".
- *Why:* blue and white instantly read as "Yale". A consistent, restrained palette looks like an established store, and the licensing message builds trust before anyone scrolls.

## 2. Typography and hierarchy
- **Libre Baskerville** (a collegiate serif) for headlines, prices on product pages, and the wordmark. **Inter** for all UI and body text.
- Clear levels everywhere: small blue uppercase **eyebrow** → serif **headline** → muted **supporting text** → action.
- *Why:* the serif/sans pairing feels academic and premium. A predictable hierarchy lets shoppers scan a page in seconds and find the price and the button.

## 3. Product presentation
- **Consistent product photos.** 73 of 102 catalogue photos had a pure-black background and the rest were white, so grids looked patchy. `backend/images.py` makes a display copy of each photo with the background replaced by the tile color. It does this by flood-filling from the edges through near-black or near-white pixels only, then cleaning the JPEG halo, so navy garments stay intact. Originals in `data/` are untouched (`image_url` is unchanged; cards use the new `display_image_url`), and the generated copies are cached outside Git.
- **Product cards:** image on a neutral tile, garment type, name, 2-line description, price, and **size chips** (XS–XXL, sold-out sizes struck through) from live inventory. A **"Low stock"** badge appears when ≤ 30 units remain, based on real data rather than fake urgency. On hover the card lifts, the photo zooms slightly, and a "View details →" pill slides up.
- **Product page:** breadcrumb (Home / Shop / Hoodies / item), a large photo that zooms gently on hover and stays in view while you scroll, a serif title, a big blue price, an "Officially licensed" badge, **color swatches**, size buttons (selected = solid blue, sold out = struck through), a live stock line, the "Ask about this item" button, three assurances (licensed, live stock, 57 Broadway), and a **"More like this"** row of in-stock items from the same category.
- *Why:* clean, uniform photos are the biggest single signal of a professional store. Showing sizes on the card answers "do they have mine?" before the click. "More like this" keeps people browsing instead of leaving at a dead end.

## 4. Home page
- **Hero:** a full-width Yale-blue gradient with a faint pinstripe texture, the headline "Wear the Blue, *every day.*", a **collage of three real products** with price tags, and two CTAs (Shop / Ask our assistant). Below the CTAs are quick facts: 102 styles · XS–XXL live stock · 57 Broadway.
- **Trust strip** (licensed · live size stock · shopping assistant · local shop), **Shop by category** tiles with product photos and counts, **Campus classics** product grid, a **"Not sure what fits? Just ask."** assistant promo with a sample conversation, and a **Visit us on Broadway** band.
- *Why:* within one screen the visitor knows what the store is, sees real products and prices, and has two clear next steps. The category tiles get people to the right products in one click.

## 5. Navigation, forms and buttons
- **Header:** sticky and slightly translucent, with a soft shadow once you scroll. Nav links get an animated underline, and "Create account" is the primary button. On phones it collapses into a **menu button**.
- **Buttons:** pill-shaped. Primary is solid blue and lifts 1px on hover. Secondary buttons are outlines, and there are light/outline variants for blue backgrounds. Every interactive element has a visible blue focus ring for keyboard users.
- **Log in / Create account:** a split card. The left is a blue crest panel listing what an account gets you (saved chat, personal help, live stock); the right is the form with clear labels, full-width submit, and red inline errors.
- **Footer:** dark blue with Shop (category links), Help (opens the assistant), and Visit columns.
- *Why:* explaining the benefit of an account next to the form increases sign-ups. Consistent buttons and focus states make the site feel finished and accessible.

## 6. Chat experience
- **Launcher:** a blue pill, **"Ask our assistant"**, with a green "online" dot (just an icon on phones).
- **Panel:** a Yale-blue gradient header with a crest avatar, title, and status ("Chat saved to Test's account" / "Guest chat · not saved"), plus New chat and close buttons. The panel opens with a short scale/fade.
- **Messages:** shopper bubbles in Yale blue, assistant bubbles as white cards on a warm background with blue bold product names, and an **animated typing indicator** ("Checking the shelves…"). Each message fades in, and the green **"✓ Prices verified"** line and the **"N products · Show on page"** chip sit under replies.
- **Suggested-question chips** in light blue, plus a round blue **send** button with an arrow icon.
- All icons are inline SVGs instead of emoji, so they render the same on every device.
- *Why:* the assistant looks like part of the brand instead of a bolt-on widget. The typing indicator and verified badge make it feel responsive and trustworthy, which keeps shoppers asking questions on the path to buying.

## 7. Motion (subtle by design)
- **Page changes:** a single soft fade-up per route change. Filtering on the same page doesn't re-animate.
- **Hover:** cards lift with a slight photo zoom, collage tiles straighten, and buttons rise 1px.
- **Chat:** messages fade in and the panel scales in.
- **Timing:** all transitions are 160–600ms with one easing curve. The site respects **`prefers-reduced-motion`**, which turns animations off for people who ask for that.
- *Why:* motion confirms that an action happened and makes the site feel alive, without distracting from the products.

## 8. Responsive layout
- The hero, product page, home promo and account pages go to a single column on smaller screens. The grids drop from 4 to 2 columns.
- On phones, the category chips become one swipeable row and the filter dropdowns sit two per row. The chat panel becomes nearly full-screen, and the header collapses into a menu.
- Checked at 1440px desktop and 390px phone widths.
