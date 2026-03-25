---
name: asymmetric-landing
description: Design and build asymmetrical but visually balanced landing pages with production-ready code. Use this skill whenever the user asks to create a landing page, hero section, marketing page, product page, or any full-page web layout — especially when they mention asymmetry, unconventional layouts, editorial design, off-grid composition, dynamic balance, or breaking the grid. Also trigger when the user wants a landing page that feels distinctive, magazine-like, or avoids the typical centered-hero-with-symmetric-columns pattern. This skill produces real, deployable HTML/CSS/JS or React code — not mockups.
---

# Asymmetric Landing Page Design

This skill creates landing pages that use **asymmetrical composition with intentional visual balance** — the kind of layouts you see in high-end editorial design, architecture portfolios, and premium brand sites, but rarely in AI-generated output.

The core idea: symmetry is easy and safe, but asymmetry done well creates visual tension, hierarchy, and movement that pulls people through a page. The hard part is keeping it *balanced* — asymmetry without balance is just chaos.

## Before You Code

Read the pattern library at `references/patterns.md` before starting any build. It contains 8 curated asymmetric layout patterns with visual descriptions, CSS grid structures, and guidance on when each works best. Pick a pattern (or combine elements from multiple patterns) based on the content and purpose of the page.

Also read `references/balance-principles.md` for the theory behind asymmetric balance — the visual weight system, counterbalancing techniques, and common failure modes. Understanding *why* a layout feels balanced matters more than memorizing grid coordinates.

## Design Process

### 1. Understand the content hierarchy

Before picking a layout pattern, identify:
- **Primary action**: What's the one thing the visitor should do? (sign up, buy, learn more)
- **Content weight**: How much text vs. imagery? Is there a hero video, illustration, or product shot?
- **Information density**: Is this a sparse, atmospheric page or a dense, information-rich one?

The content determines the layout, not the other way around. A SaaS product with a complex value prop needs different asymmetric treatment than a single-product launch with one hero image.

### 2. Select and adapt a pattern

Choose from the pattern library based on content needs. Patterns are starting points — adapt column ratios, spacing, and element placement to fit the specific content. The patterns are:

1. **Heavy Left** — dominant visual left, text + CTA right
2. **Diagonal Flow** — content arranged along an implicit diagonal, pulling the eye corner to corner
3. **Offset Grid** — columns that don't align vertically, creating rhythm through misalignment
4. **Anchored Float** — one large anchored element with smaller elements floating asymmetrically around it
5. **Split Tension** — page divided into two unequal zones (roughly 60/40 or 70/30) with contrasting treatments
6. **Staggered Stack** — vertically stacked sections where each section is offset horizontally from the previous
7. **Overlap Collage** — elements deliberately overlap, creating depth and breaking the flat-page feel
8. **Negative Space Anchor** — large intentional empty space used as a compositional element, not just leftover room

### 3. Apply balance principles

Every layout must pass the "squint test" — if you blur the page, the visual weight should feel distributed, not lopsided. Balance asymmetric layouts using these counterweights:

- **Size vs. intensity**: A large, light element can balance a small, dark/saturated one
- **Quantity vs. mass**: Several small elements can balance one heavy one
- **Position vs. weight**: Elements further from center exert more visual leverage (like a seesaw)
- **Texture vs. void**: Dense texture/pattern areas balance large empty spaces
- **Movement vs. stillness**: An animated or dynamic element draws weight, balancing a static mass elsewhere

### 4. Build production-ready code

Output must be deployable code, not a concept. Requirements:

**Layout engine**:
- Use CSS Grid for the macro composition — the asymmetric section-level structures. Grid handles 2D asymmetry far better than flexbox because you're positioning elements along both axes simultaneously. In Tailwind: `grid`, `grid-cols-12`, `col-span-*`, `col-start-*`, `row-span-*`, `row-start-*`.
- Use flexbox for micro components *within* grid cells — button groups, icon+text pairs, nav items. In Tailwind: `flex`, `items-center`, `gap-*`.
- This is how most production React/Tailwind codebases work. Grid for structure, flex for components.
- When outputting vanilla HTML, use raw CSS Grid with named grid areas for readability. When outputting React/Tailwind, use Tailwind's grid utilities and avoid custom CSS unless the layout genuinely can't be expressed in utility classes (rare for grid structures, more common for overlap/z-index compositions).

**Responsive approach**:
- Use Tailwind's responsive prefixes (`md:`, `lg:`) or standard media queries at mobile (<768px), tablet (768-1024px), and desktop (>1024px)
- Use `clamp()` and fluid typography for smooth scaling between breakpoints
- Asymmetric layouts are harder to make responsive than symmetric ones. The key insight: **asymmetry can simplify on mobile without becoming symmetric**. A heavy-left desktop layout might become a staggered stack on mobile, not a boring centered column. Preserve the *feeling* of asymmetry at all breakpoints even if the specific grid changes.

**Typography**:
- Pair a distinctive display font (from Google Fonts) with a refined body font
- Use typographic scale that reinforces hierarchy — oversized headings and deliberate size jumps, not uniform scaling
- Consider text alignment as a compositional element: left-aligned text in an asymmetric layout has different visual weight than centered text

**Color and atmosphere**:
- Commit to a palette that supports the asymmetric composition. High-contrast palettes emphasize boundaries between asymmetric zones. Low-contrast palettes unify them.
- Use background treatments (gradients, subtle textures, color blocks) to reinforce the grid structure, not fight it

**Animation** (use sparingly):
- Entrance animations should follow the visual flow of the layout — if the layout reads top-left to bottom-right, animate elements in that sequence
- Scroll-triggered reveals work well for staggered/offset layouts
- Parallax-like depth effects reinforce overlap compositions
- Avoid animation that undermines the compositional balance (e.g., an element flying in from the wrong direction)

## What To Avoid

- **Symmetric fallback**: Don't default to centered layouts when stuck. If an asymmetric approach isn't working, try a *different* asymmetric approach.
- **Arbitrary asymmetry**: Every off-center placement should have a reason — creating hierarchy, directing flow, or balancing another element. Random offset ≠ good design.
- **Over-complexity**: Asymmetry doesn't mean every element needs unique positioning. Two or three strong asymmetric moves per viewport height is plenty. The rest can be quieter.
- **Ignoring visual weight**: A common failure is making text-heavy sections too light and image sections too heavy. Text blocks have weight — use font size, color, and density to control it.
- **Mobile afterthought**: Design the mobile layout alongside the desktop layout, not after. Asymmetric mobile layouts are distinctive and memorable when done well.

## Output Format

**Default output: React JSX with Tailwind CSS.** If the user specifies a different stack (vanilla HTML, Vue, Svelte, etc.), adapt accordingly. The output should be:
- Immediately runnable — drop into a project and it works
- Well-commented, especially around grid class choices and balance decisions
- Using Google Fonts (loaded via `<link>` in HTML, or imported in the component/layout)
- Including placeholder content that demonstrates the layout (not lorem ipsum — write realistic placeholder copy that shows how real content fills the space)
- Using Tailwind utility classes for layout and spacing; only dropping to custom CSS or `style` attributes for things Tailwind can't express (complex grid-template-areas, clip-paths, specific overlap positioning)

If the user provides specific content, use it. If not, write contextually appropriate placeholder content based on what the page is for.

## Quick Reference

When in doubt: **read `references/patterns.md` and `references/balance-principles.md`**. The patterns give you structure. The balance principles tell you why it works.
