# Matic Digital — Retina Voice & Style Guide

Derived from analysis of Matic client deliverables, recommendation frameworks, heuristic reports, and the Retina report design system.

---

## 1. Tone of Voice

### Core Identity
Matic positions itself as a **strategic consultancy**, not a technical auditor. Every piece of client-facing text should read like it came from a senior strategist who understands both the technical reality and the business implications.

### Voice Characteristics
- **Confident and direct** — state findings as clear assessments, not tentative observations. "The site lacks..." not "It appears that the site may lack..."
- **Outcome-oriented** — every technical finding connects to a business outcome. Never present a metric without explaining what it means for the business.
- **Constructive, not critical** — frame gaps as opportunities. The ratio is roughly 30% acknowledgment of what works, 70% where improvement drives results.
- **Consultative, not prescriptive** — "This creates an opportunity to..." rather than "You must fix..."
- **Specific, never generic** — every observation references something concrete about the site. Avoid filler sentences that could apply to any website.

### Language Patterns

**Opening an observation:**
- "The site presents..."
- "From a competitive standpoint..."
- "The current implementation..."
- "[Site] demonstrates a [level] of digital maturity..."

**Identifying strengths (acknowledge first):**
- "The site's [specific element] effectively communicates..."
- "A notable strength is..."
- "The [feature] is well-positioned to..."

**Identifying gaps (frame as opportunity):**
- "This creates an opportunity to..."
- "There is a clear path to improvement in..."
- "The gap between [current] and [competitor/standard] represents..."
- "Addressing this will improve [specific outcome]..."

**Connecting to business impact:**
- "...which directly impacts conversion rates"
- "...creating friction that costs pipeline"
- "...reducing the likelihood that visitors take action"
- "...strengthening competitive positioning against [competitor]"

### Words to Use
- "digital readiness" (not "website quality")
- "competitive positioning" (not "ranking")
- "visitor experience" (not "UX")
- "conversion pathway" (not "funnel")
- "trust signals" (not "social proof elements")
- "digital maturity" (not "website score")

### Words to Avoid
- "broken" — use "needs attention" or "underperforming"
- "bad" — use "below threshold" or "creating friction"
- "fix" (as a noun) — use "improvement" or "optimization"
- "problem" — use "gap" or "opportunity"
- "you should" — use "we recommend" or "this creates an opportunity to"
- Any raw technical jargon without business context

---

## 2. Report Structure

### Sequence (from Retina report design)
1. **Cover** — branded, clean, client name prominent
2. **About This Report** — what Retina is, what it measures, why it matters
3. **Performance Summary** — overall score with tier context, lens breakdown
4. **Lens Deep-Dives** — each of the 5 lenses with detailed findings
5. **Competitive Comparison** — side-by-side positioning
6. **Strategic Quadrant** — recommendations mapped by effort/impact
7. **Prioritized Roadmap** — ordered action items with execution tiers
8. **Methodology** — data sources, scoring approach, analyst involvement

### Section Introductions
Every section opens with a brief contextual statement explaining what the reader is about to see and why it matters. Examples from reference materials:

- "Retina evaluates real-world digital experiences to reveal where online performance is being won or lost."
- "Digital experience is now the primary driver of awareness, consideration, and conversion. Gaps in clarity, usability, or technical performance create friction that costs pipeline — even for strong brands."
- "Five lenses assess digital experience readiness across complementary dimensions of website performance and strategic effectiveness."

### Score Context Tiers
Always present scores with human-readable tier labels:
- **0–25**: Poor experience, modernization needed
- **26–50**: Challenging experience, focus needed
- **51–75**: Functional, some optimization needed
- **76–100**: Ideal experience for digital growth

For individual lenses (0-20 scale):
- **0–5**: Critical gaps, immediate attention needed
- **6–10**: Below expectations, targeted improvement required
- **11–15**: Functional with room for growth
- **16–20**: Strong execution, competitive advantage

---

## 3. Data Presentation

### Principle: Context Over Numbers
Never present a metric alone. Every data point gets:
1. **What it is** — one-line plain-English explanation
2. **What the number means** — good/needs work/poor relative to established thresholds
3. **Why it matters** — business impact in one sentence

### Metric Framing Examples
Instead of: "LCP: 4200ms"
Use: "Largest Contentful Paint: 4.2s — Poor. The main content takes over 4 seconds to appear, well above the 2.5s threshold. Slow LCP increases bounce rates and signals to Google that the page delivers a poor experience."

Instead of: "SEO Score: 78"
Use: "SEO visibility scores 78/100 — functional but leaving opportunity on the table. Key gaps in structured data and meta completeness reduce the site's ability to win featured snippets and AI-generated answers."

### Technology Stack
Present technologies as strategic choices with implications:
- Group by function (CMS, Hosting, CDN, Analytics, Frameworks)
- For each, explain what it means: "WordPress (CMS) — widely supported with extensive plugin ecosystem. Consider whether current implementation leverages caching and performance optimization plugins."

### Competitive Comparisons
Use the **Strengths / Differentiators** format from the competitive benchmarking deck:
- **Strengths**: What the site does well relative to competitors
- **Differentiators**: What sets it apart in the market
- Frame as positioning, not just scores

---

## 4. Recommendation Format

### Three Execution Tiers (from reference deliverables)

**Low Hanging Fruit** (Quick wins, do these first)
- Low effort, high or moderate impact
- Can be implemented in days, not weeks
- Example format:
  > **Ensure text on images is easy to read**
  > Text overlays on images should have sufficient contrast and legible font sizes to ensure clarity for all users, preventing readability issues.

**Moderate Implementation** (Planned improvements)
- Medium effort, meaningful impact
- Require some planning and design work
- Example format:
  > **Optimize the homepage to prioritize key content**
  > The homepage currently lacks clear product showcases and emphasizes non-primary CTAs. Redesigning it to feature top-selling products and promotions will improve user engagement.

**Significant Effort** (Strategic investments)
- High effort, transformational impact
- Require dedicated project planning and budget
- Example format:
  > **Implement account-based personalization for returning users**
  > The site lacks personalized recommendations or saved preferences. Adding user accounts with purchase history, saved items, and tailored recommendations will improve customer retention.

### Recommendation Writing Formula
Each recommendation follows this structure:
1. **Title**: Imperative verb phrase — "Improve...", "Optimize...", "Implement...", "Ensure...", "Add..."
2. **Current state**: What the site currently does (or doesn't do)
3. **Impact statement**: What fixing this will achieve, in business terms

### Strategic Quadrant Mapping
Recommendations also map to the Impact/Effort matrix:
- **No-Brainers** (low effort, high impact) — do immediately
- **Quick Wins** (low effort, lower impact) — build momentum
- **Growth Moves** (high effort, high impact) — invest strategically
- **Transformational** (high effort, long-term payoff) — plan for future

---

## 5. Visual & Layout Patterns

### Information Hierarchy
1. **Section label** — small, uppercase, colored (e.g., "Performance summary" in accent blue)
2. **Section title** — large, bold, clear statement (e.g., "[Site] Digital Readiness Score")
3. **Context paragraph** — 1-2 sentences framing what follows
4. **Data presentation** — scores, charts, cards
5. **Interpretation** — what the data means, written in consultative tone

### Card Patterns
- Light background (#FAFBFC or similar) with subtle border
- Left-colored border for emphasis/categorization
- Bold title + lighter description
- Category labels in small uppercase with letter spacing

### Recommendation Cards
- Grouped by execution tier (Low Hanging Fruit → Moderate → Significant Effort)
- Each card: Bold title, 2-3 sentence description on light background
- Clean, scannable, no clutter

### Score Visualization
- Large number prominently displayed with "/ max" in lighter weight
- Progress bar showing position within range
- Color coding: green (good), amber (needs work), red (poor)
- Tier label beneath the number

---

## 6. Lens Descriptions (Canonical)

These are the official one-line descriptions for each Retina lens, used across the report, UI, and all client-facing materials:

- **Brand & Messaging**: How clearly the website communicates who it is for, what it offers, and why it matters.
- **Experience & Design**: How intuitive, modern, and intentional the website feels — from navigation and layout to visual hierarchy and mobile responsiveness.
- **Conversion & Strategy**: How effectively the website turns attention into action through clear CTAs, logical user paths, and trust-building content.
- **SEO & AI Visibility**: How discoverable the website is to search engines, LLMs, and the algorithms that increasingly determine who gets found first.
- **Performance & Technical Health**: How fast, stable, and well-built the website is under the hood — page speed, code quality, security, and core web vitals.

---

## 7. Key Positioning Statements

Use these as section openers and framing throughout the platform:

- "Retina evaluates real-world digital experiences to reveal where online performance is being won or lost."
- "Digital experience is now the primary driver of awareness, consideration, and conversion."
- "Gaps in clarity, usability, or technical performance create friction that costs pipeline — even for strong brands."
- "Retina combines automated performance benchmarking with human strategic evaluation to surface exactly where those gaps are and what to do about them."
- "An intelligent lens on five pillars of your digital readiness."
