# AI Prompts Log — HW4 Campus Customs

A record of the prompts I typed to my vibe coder (Claude Code) while working on each problem.

---

## Setup (before Problem 1)

**Prompt 1:**

> Hi Claude, I am working on hw4. Im giving you this scenario.
>
> For this homework, I need to build a full Campus Customs shopping website with a chatbot. The front end should use React, Vite, and TypeScript, and the backend should use Python FastAPI with a PydanticAI agent.
> The website should let users browse products, create an account and log in, chat with the shopping assistant, and see relevant products show up on the page based on what they ask. The chatbot also needs to give accurate information about product prices and inventory by checking the local database instead of making things up.
> I was given a campus_customs.db SQLite database that contains product catalogue information, inventory by size, and user data with hashed passwords. There is also a products folder with the product images, and the database stores the paths to those images.
> I should also look at yalebulldogblue.com to understand the general Campus Customs style and brand information, but I should not directly copy the website text.
> For the AI agent, I can use my existing API key setup. I should work through the assignment one problem at a time instead of trying to build everything at once.
> At the end, the whole project needs to be pushed to a public GitHub repository, and I will submit the repo URL on Canvas. The database, product images, and real API keys should stay local and should not be committed to GitHub.

**Prompt 2:**

> Hey Claude! I also have the data files for this homework in the hw4 folder!!! After unzipping the provided data.zip, the project should include a data folder with two main parts.
> The file data/campus_customs.db is a SQLite database. It contains the catalogue, inventory, and users tables, and there is already one test user in the database.
> The folder data/products/ contains the product images. The image file paths correspond to the paths stored in the catalogue table.
> This is only background information for the project right now. No action is needed yet.

---

## Problem 1 — AI Prompts Log

**Prompt:**

> Hey Claude, this is my problem 1:
>
> For Problem 1, I need to create an AI_prompts.md file at the beginning of the homework and keep updating it throughout the project. This file should basically be a record of what I actually type to my vibe coder while I work.
>
> Inside AI_prompts.md, I need a separate section for each problem. Each section should include the problem number and title, at least one prompt that I actually used written in my own words word for word, and a follow-up prompt if I needed one. If I did need a follow-up, I should also include one sentence explaining what was missing or not good enough after the first prompt.
>
> I do not need to write a separate proof essay for this. My running website, any database changes or writes, and the screenshots from the finished work will serve as the evidence, together with the prompts I recorded.

**Follow-up prompt:** None needed.

---

## Problem 2 — Understanding the Database / Harness

**Prompt:**

> Hey Claude, this is problem 2:
>
> For Problem 2, I need to look through data/campus_customs.db and understand the fields in each table. At a minimum, I should fully understand the catalogue, inventory, and users tables.
> I also need to start an output/harness.md file. In that file, I should list each table and all of its fields, then add one short explanation for each field describing why it matters for either the shopping website or the chatbot.
> This harness.md file is not just for this problem. I will keep adding to it later in the assignment as I build out the models, tools, safety rules, and system specs.

**Follow-up prompt:** None needed.

---

## Problem 3 — Campus Customs Front End

**Prompt:**

> Hi Claude, this is my problem 3:  So basiclly I need u to build the Campus Customs front end using React, Vite, and TypeScript.
>
> The site should have a navigation bar at the top that links to the main pages: Home, Products, About Us, Log in, and Create account.
>
> For the Home and About Us pages, I should look at yalebulldogblue.com to get a sense of the Campus Customs style and wording, but I still need to write the content in my own voice and should not directly copy the original website text.
>
> On the Products page, I need to display the product images from the catalogue using the image paths stored in the database. Each product card should also show the basic product information, including the product name, price, and a short description.
>
> Each product should also have its own single-item page. When a shopper clicks a product card from the Products page, it should open that product’s detail page. The detail page should have a large product image on one side and the full product information on the other side, including the description, price, and the available sizes and stock once that information is available.
>
> I also need to add a chat interface in the bottom-right corner of the website. A floating chat panel is fine. For this problem, the chat does not need to be connected to the real agent yet. It can just be a placeholder or stub that will connect to the backend later.
>
> Since I will soon need an API to read from the database, I can also start a simple FastAPI app in backend/main.py. For now, it only needs to serve products and product images. Later, in Problem 5, I can expand the same backend into the full agent backend.

**Follow-up prompt:** None needed.

---

## Problem 4 — Account Creation and Login

**Prompt:**

> Hi Claude! Here comes problem 4: For Problem 4, I need u to build a normal account creation and login system for the website.
> For creating an account, the user should enter their first name, last name, email, and password. Adding a confirm-password field would also be a nice extra. For logging in, the user only needs their email and password.
> Any new account that gets created should be saved into the users table in the database. Passwords need to be stored securely, so they should not be saved in a form that a person or an AI system could directly access or read.
> The starter database already includes a test account that I can use while I am building and testing the login flow:
> Email: test@campuscustoms.yale.edu
> Password: password
> I need to make sure that I can successfully log in with this existing test user, and I also need to confirm that a completely new account I create can log in successfully too.
> I also need to update output/harness.md to explain how the authentication system works, including what user information is stored and how the passwords are protected.

**Follow-up prompt:** None needed.

---

## Problem 5 — PydanticAI Shopping Agent behind FastAPI

**Prompt:**

> Hey Claude! So this is problem 5:  I need u to turn the shop chatbot into a real PydanticAI agent that runs behind FastAPI and connects to the chat widget on the front end.
> The FastAPI app should live in backend/main.py, and this is the file I will run with Uvicorn. The agent itself should stay organized in four separate files next to it, similar to the setup from Homework 3:
> backend/prompts/prompt.md for the system prompt, and I will keep expanding this same file later
> backend/agent.py for the agent setup and wiring
> backend/tools.py for the tools the agent can call
> backend/models.py for the Pydantic and PydanticAI structured types
> Inside main.py, I need to create a chat route so messages from the website can be sent to the backend and return a reply from the agent. I can also keep any other API routes I need there for things like products and authentication. The agent will need access to my AI model API key.
> I also need to start putting the Campus Customs tone and basic safety rules into prompts/prompt.md. I will add more tools and stronger safety rules later in the assignment.
> In models.py, I should create or update the structured types I need for things like chat responses and product cards.
> I also need to update output/harness.md to explain how the front end communicates with FastAPI and how the agent gets loaded, including the prompt file and the model being used.
> Finally, I need to make sure the backend can be run from inside the backend/ folder with:
> uvicorn main:app --reload --port 8000

**Follow-up prompt:** None needed.

---

## Problem 6 — Product Lookup Tools (Price, Description, Inventory)

**Prompt:**

> Yo Claude, this is problem 6: So I need u to give the agent tools that can look up real product information directly from campus_customs.db.
> So the tools should be able to get the product description, the price, and the inventory quantity. If the customer asks about a specific size, the agent should be able to check the stock for that size too.
> Hey Claude! The agent has to rely on the database for this information. It should never make up a price or an inventory number. If a certain size is out of stock, the agent should clearly tell the customer that it is unavailable.
> I also need to expand prompts/prompt.md so the agent knows it should call these tools whenever the user asks about price or stock. In models.py, I should add or update the return types needed for these lookup results.
> Finally, I also need u to update output/harness.md by listing each tool and explaining which model fields I chose for the lookup results and why I included those fields.

**Follow-up prompt:** None needed.

---

## Problem 7 — Chatbot Product Search → Product Cards on the Page

**Prompt:**

> yooo claude, this is my problem 7: For Problem 7, I need u to add a feature where the chatbot can search the product catalogue and update the website with matching products.
> For example, if a customer asks something like, “What hoodies do you have?”, the agent should search the catalogue for hoodies and return the matching products. The front end should then dynamically display those results as product cards on the page. Each card should include the product image, name, price, and a short description or short product info.
> This should work through a clear API contract: the agent returns the matching products in a structured format, and then the front end uses that structured data to render the product cards on the website.
> I also need u to make sure the product cards added by the chatbot behave the same way as the regular product cards from Problem 3. If the user clicks one of these dynamically added cards, it should still open the normal single-item detail page with the large product image and the full product information.
> Finally, I need u  to update prompts/prompt.md and output/harness.md so they clearly explain how the product search works and how the search results move from the agent to the front end and appear on the page. Thank u!

**Follow-up prompt:** None needed.

---

## Problem 8 — Customer Memory and Page Context

**Prompt:**

> Hi Claude, this is my problem 8:
>
> For Problem 8, I need to add customer memory to the chatbot.
> When a shopper is logged in, their chat history should be saved into the database in an appropriate table. If they leave and come back later, that history should load again so the conversation can continue.
> The agent should also know which customer it is talking to, including at least their name and email. I can pass this through the agent dependencies or use another clear pattern, such as tools the agent can call.
> I also need to pass enough page context to the agent so it understands what the customer is currently looking at. For example, if someone is on a specific product page and asks, “Do you have this in pink?”, the agent should know which product “this” refers to. The page or product information can be included in the agent context.
> Guests should still be able to use the chatbot, but their chat history does not need to be saved permanently. Persistent chat history is only required for logged-in users.
> Finally, I need to update output/harness.md to explain how the chat history is stored, which customer fields the agent can see, and how the current page context is passed to the agent.

**Follow-up prompt:** None needed.

---

## Problem 9 — Usability Improvements

**Prompt:**

> Hey Claude, this is problem 9:
>
> For Problem 9, I need to improve the shop now that the main functionality is working.
> I need to choose and actually implement four usability improvements total: two on the front end and two for the agent or backend.
> The front-end improvements should make the website look better or make it easier for customers to use. The agent/backend improvements should make the chatbot’s responses better, more accurate, or safer. They could also be things like new agent tools or changes that make the agent faster or cheaper to run.
> I need to create output/usability.md before I build the improvements or while I am building them. For each improvement, I should explain what I added and why it helps either a Campus Customs shopper or the business.
> All four improvements also need to actually appear in the running app. The graders will read output/usability.md and then check the website to make sure the features I described are really there.

**Follow-up prompt:** None needed.

---

## Problem 10 — Visual Design

**Prompt:**

> Hey Claude, this is problem 10:
>
> For Problem 10, I need to improve the visual design so the website feels like a real Campus Customs storefront instead of a basic class project. I should improve the fonts, colors, visual hierarchy, motion, product presentation, and the overall chat experience. More creative and innovative design can earn more points.
> I also need to create output/design.md with a short and concrete explanation of what I changed and why those changes could help customers stay longer and be more interested in buying.
> For the design direction, I want the site to feel modern, polished, and Yale-inspired. Please use deep Yale-style blue with white and neutral tones, clean typography, strong spacing, and a premium e-commerce feel. Improve the home page, navigation, product cards, product detail page, forms, buttons, and chatbot so everything feels visually consistent.
> Add subtle hover effects and smooth transitions, but do not overuse animation. Keep the layout clean, responsive, and easy to read.
> Most importantly, keep all the functionality from the previous problems working. The goal here is mainly to improve the design and make the site feel more like a real Yale merchandise store.

**Follow-up prompt:** None needed.

---

## Problem 11 — Live App Check

**Prompt:**

> Hey Claude! Now lets do problem 11: I need u to test the live website and document the results in output/app_check.html. This should be a normal HTML page that I can open by double-clicking it.
> The page needs to include clear screenshots and short captions showing three things: the chatbot checking the inventory level of a product and giving real stock and price information from the database, the dynamic product cards appearing after a category-type question such as asking for hoodies, and one of the usability improvements I added in Problem 9.
> The HTML should be easy for the grader to review. Each check should have its own heading, a screenshot, and one or two short sentences explaining what that screenshot proves.
> I also need to save the screenshot image files inside output/app_check_images/ and link to them from app_check.html using relative paths, for example app_check_images/inventory.png. I will take the screenshots myself from the live site. Please do not generate or fake screenshots.

**Follow-up prompt:** None needed.

---

## Problem 12 — Audit Trail, Safety Rules, and Final Harness

**Prompt:**

> Yo lets move on to problem 12: For Problem 12, I need to keep an append-only output/audit_trail.json that records the agent loop activity. Each entry should include the time, the tool name, a short summary of the arguments and result, and the stop reason. The file should keep growing over time and should not be cleared or overwritten between runs.
> I also need to add some safety rules for the agent in prompts/prompt.md.
> Then I need to finish output/harness.md so it clearly explains how the whole system works. It should include the model fields in models.py and why I chose them, the tools and abilities of the agent, the safety rules, and the main system specs, including loop limits, result caps, which models are used, and how to run both the front end and the backend.

**Follow-up prompt:** None needed.

---

## Problem 13 — Push to a Public GitHub Repository

**Prompt:**

> Now lets do problem 13:
>
> For Problem 13, I need to put the finished project inside a folder named hw4 and push it to a public GitHub repository. On Canvas, I will submit the GitHub repository URL so the graders can open and clone the project. I should not submit a zip file for this homework.
> I need to make sure sensitive or local-only files are not included in the GitHub repo. Specifically, I should not commit my real .env file, campus_customs.db, or the product image files. I should use .gitignore to exclude them. I also need to include a .env.example file that only contains placeholder values.
> The final hw4 folder should include:
> hw4/
> ├── AI_prompts.md
> ├── requirements.txt
> ├── .env.example
> ├── .gitignore
> ├── README.md
> ├── frontend/
> ├── backend/
> │   ├── main.py
> │   ├── agent.py
> │   ├── models.py
> │   ├── tools.py
> │   └── prompts/
> │       └── prompt.md
> └── output/
>     ├── harness.md
>     ├── design.md
>     ├── usability.md
>     ├── app_check.html
>     ├── app_check_images/
>     └── audit_trail.json
> The frontend/ folder contains the Vite React TypeScript app.
> The FastAPI backend should be under backend/, and backend/main.py should still be runnable with:
> uvicorn main:app --reload --port 8000
> The agent itself should remain organized as four main files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py.
> The local data pack should stay outside Git and should contain:
> data/
> ├── campus_customs.db
> └── products/
> The products/ folder contains the images referenced by the catalogue in the database.
> Finally, README.md should explain how to run both the front end and the back end after the local data pack has been placed in the project.

**Follow-up prompt:** None needed.
