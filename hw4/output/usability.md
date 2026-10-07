# Campus Customs — Usability Improvements

Four improvements on top of the working shop: two on the front end and two in the agent and backend. Each section explains what was added, why it helps a Campus Customs shopper or the business, and **where to see it in the running app**.

| # | Improvement | Area | Where to see it |
|---|---|---|---|
| 1 | Shop filters and sorting | Front end | **Products** page: category chips, size / price / sort dropdowns |
| 2 | Suggested questions + "Ask about this item" | Front end | Chat panel (chips above the input), **product pages** (blue "Ask about this item" button) |
| 3 | `find_similar_products` agent tool | Agent / backend | Ask about a sold-out size, e.g. on the Fencing Left Chest Hoodie page: "Is this in large?" or "Show me similar items" |
| 4 | Reply check for prices and privacy | Agent / backend | "✓ Prices verified" badge under chatbot replies that mention prices |

---

## 1. Shop filters and sorting (front end)

**What I added**
- **Category chips** at the top of the Products page: All, Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, Long Sleeves. They use the same category matching as the chatbot, so "Hoodies" includes all 27 hoodie-style items, including the ones labeled "hooded sweatshirt".
- **"In stock in size"** dropdown (XS–XXL). It only shows products that actually have that size available, based on the live `inventory` table.
- **Price cap** (Under $40 / $60 / $80) and **sort** (A–Z, price low→high, price high→low).
- The item count updates live ("25 items · T-Shirts · in stock in M"). A **Clear filters** button resets everything, and a friendly message appears when nothing matches.
- Filters are saved in the URL (e.g. `/products?category=hoodie&size=M&sort=price_asc`). Back/forward works and a filtered view can be shared as a link.
- Backend: `GET /api/products` now accepts `category`, `size`, `max_price`, and `sort`, reusing the same SQL helper (`query_products`) as the agent's search tool.

**Why it helps**
- **Shoppers:** with 102 products, scrolling is slow. A student who wears a medium can tap "Hoodies" + "M" and see only hoodies they can actually buy, instead of opening product pages one by one to find out a size is sold out.
- **Business:** shoppers who find something in their size quickly are more likely to buy. Fewer dead ends (clicking a sold-out item) means fewer abandoned visits.

---

## 2. Suggested questions + "Ask about this item" (front end)

**What I added**
- **Suggested-question chips** above the chat input. They change with the page:
  - On a **product page**: "Is this in stock in M?", "What sizes are left?", "Show me similar items".
  - When **assistant cards are on the page**: "Which of these is cheapest?", "Which are in stock in M?".
  - Elsewhere: "What hoodies do you have?", "Bulldog gear under $60", "Gifts for a Yale parent".
  
  Clicking a chip sends it right away. The page context (Problem 8) means "this" and "these" are understood.
- An **"Ask about this item"** button (with a chat icon) on every product page, below the size picker. It opens the chat panel, ready to ask about that product.

**Why it helps**
- **Shoppers:** many people don't know what a shopping bot can do, or don't want to type on a phone. One-tap questions show what's possible (stock checks, comparisons, gift ideas) and get answers faster.
- **Business:** more shoppers use the assistant, so more of them get accurate stock answers instead of leaving. The suggestions also steer people toward what the bot does well (catalogue, price and stock questions) and away from things it can't do.

---

## 3. `find_similar_products` agent tool (agent / backend)

**What I added**
A new tool in `backend/tools.py`, registered in `agent.py`, with a `SimilarProducts` return type in `models.py`:
```
find_similar_products(product, size?, color?)
```
- It finds products in the **same category** as the given product (hoodie, crewneck, T-shirt…), excluding the product itself.
- It ranks them by **how much they have in common**: shared search tags (e.g. "bulldog", "vintage", "hockey"), shared colors, and similar price.
- If `size` is given, it **only returns items that have that size in stock**, and says how many are left. If `color` is given, it only returns items that include that color.
- Each result carries a short `why` ("same category; also bulldog, vintage; 15 left in M") so the agent can explain its suggestion.
- The prompt tells the agent to use it whenever a requested size is sold out, a color isn't available, or the shopper asks for "something like this". The suggestions appear as product cards on the page.

**Why it helps**
- **Shoppers:** a sold-out answer is now useful. Instead of "Sorry, L is sold out", they get "L is sold out, but these similar hoodies have L in stock", with cards they can click.
- **Business:** fewer lost sales when an item runs out. Alternatives are real in-stock products from the database, chosen by one SQL-backed tool instead of several guesswork searches. That means fewer model round-trips, so it's also faster and cheaper per question.

---

## 4. Reply check for prices and privacy (agent / backend)

**What I added**
A PydanticAI **output validator** (`check_reply` in `agent.py`) runs on every agent answer **before** it reaches the shopper:
- **Price check:** every dollar amount in the reply (e.g. "$68.00") must match the real `catalogue.price` of a product the tools looked up in this turn, or be an amount the shopper typed themselves ("under $60"). If not, the agent gets a `ModelRetry` saying which amount was unverified, and must look the price up and fix its answer.
- **Privacy check:** the reply may not contain any email address other than the logged-in customer's own, or anything that looks like a password hash or API key. Otherwise it is retried.
- **Visible result:** `ChatResponse` has a new `verified_prices` count. When a reply mentions prices and all of them passed, the chat shows a small **"✓ Prices verified with our store database"** badge under it.

**Why it helps**
- **Shoppers:** they can trust the prices they're told, and the badge makes that trust visible. Even if the model slips (e.g. remembers an old price from a previous visit), the wrong number is caught before it's shown.
- **Business:** quoting a wrong price causes complaints and lost trust at the register. Leaking another customer's email would be a serious privacy problem. This is an automatic safety net on top of the prompt rules, and it costs almost nothing: it's a regex check plus one small database query, and only triggers an extra model call when something is actually wrong.

---

## How each improvement was verified
All four were tested in the running app (Playwright browser test as a guest, plus API and unit tests). Numbers were checked against SQL on `campus_customs.db`.

**1. Filters and sorting**
- Products page: 102 items → **Hoodies** + **In stock in M** + **Price: low to high** → "21 items · Hoodies · in stock in M". SQL agrees: 21 hoodies have M in stock. Prices run $45.00 → $88.00 in order.
- URL became `/products?category=hoodie&size=M&sort=price_asc`. Adding **Under $40** showed the "No products match these filters" empty state with a Clear button. **Clear filters** went back to 102, and the browser **Back** button restored the previous filters.
- API: `category=hoodie` 27, `crewneck` 28, `t-shirt` 25, `quarter-zip` 11, `jacket` 8, `long-sleeve` 2 (+1 mockneck = 102 ✓). `size=XXXL` is rejected with a validation error.

**2. Suggested questions + "Ask about this item"**
- On the Fencing Left Chest Hoodie page, **💬 Ask about this item** opened the chat panel, which showed the product-page chips: "Is this in stock in M?", "What sizes are left?", "Show me similar items".
- Clicking **Show me similar items** sent it immediately and put 6 similar hoodies on the page.
- The Home page shows the general chips ("What hoodies do you have?", "Bulldog gear under $60", "Gifts for a Yale parent"). With assistant cards on the page, it shows "Which of these is cheapest?" etc.

**3. `find_similar_products`**
| Situation | Result |
|---|---|
| Fencing Left Chest Hoodie page: "Is this in large?" | "…sold out in **L**. It's available in S, M, and XL; I've also put similar hoodies with L in stock on the page, including the **Crew Left Chest Hoodie** and **Squash Left Chest Hoodie**." 7 cards. |
| District Vit Crewneck Vintage Bulldog page: "Show me similar items" | First match: District Vit Crewneck **Vintage Standing Bulldog** (shared "vintage", "district vit"), then other bulldog and crest crewnecks. |
| Basic Hoodie Big Yale page: "Do you have this in gray?" | "comes in navy… not gray", then 6 real gray hoodies on the page. |
| Tool unit test: Fencing hoodie, size L | Crew / Squash / Volleyball **Left Chest** hoodies first, each with "N left in L" (Sailing and Ice Hockey Left Chest are excluded because L = 0 in the DB ✓). |

Ranking uses rarity weights: features shared by few products ("fencing", "left chest", "vintage") count much more than ones on almost every product ("hoodie", "kangaroo pocket"). The first version ranked by raw tag overlap and put generic matches first; this was fixed before shipping.

**4. Reply check**
- Browser: "How much is the Boola Boola T Shirt and the Basic Hoodie Big Yale?" → "$32.00 … $68.00" with **✓ Prices verified with our store database** under the reply.
- Validator unit tests: a correct price passes. A wrong price ($28.00 for the $32.00 tee) → retry. A price for a product not looked up this turn → retry. The shopper's own "under $60" is allowed. The customer's own email passes. Another customer's email (`tauhid.zaman@…`) → retry. Password-hash text → retry.
- **End-to-end retry** (real agent loop with a scripted model that answers "$28.00" from memory first): the check blocked it and sent back "Your reply mentions $28.00, which doesn't match…". The model called `get_price` and answered again. The shopper only saw **"$32.00"**, with `verified_prices = 1`.
- If a reply still fails after the retries, the shopper sees "Sorry, I couldn't double-check that answer against our store database, so I won't guess…" instead of unverified information.
