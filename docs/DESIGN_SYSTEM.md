# WISEBAR design system

The visual idea is an editorial food magazine that also behaves like a specification sheet. Light pages do the shopping. Deep green pages do the brand. Lime is reserved for the main action.

## Colour

| Token | Hex | Use |
| --- | --- | --- |
| cream.50 | `#FBF8F2` | Page background |
| cream.100 | `#F3EEE4` | Cards, bands |
| pine.950 | `#071610` | Footer, near-black |
| pine.900 | `#0C2E24` | Brand sections, primary dark buttons |
| pine.800 | `#12392C` | Product stages |
| lime | `#D6F25C` | Primary buttons on light or dark. Text on lime is pine.950 |
| mango | `#E39B2B` | Notices, not decoration |
| ink | `#141816` | Body text |
| berry | `#9E3B3A` | Errors |

Flavour art uses cocoa, nut, fruit, grain, and seed palettes inside `ProductArt`. Those illustrations are labelled concept work, not final packs.

## Type

- Headings and numbers: Space Grotesk
- Body: Inter
- Labels: Space Grotesk, 11px, wide tracking, uppercase (`.spec`)

Hero type is set large and tight. The second line is indented. Do not shrink the brand down to a template hero.

## Components

- `Button` / text CTAs: pill, 44px tall, one primary (lime), one outline, one text link.
- Product card: art, flavour, three spec cells (protein, serving, energy), price or “Price pending”, review line or “No reviews yet”, quick add, view.
- Transparency list: label on the left, value or “Pending verification” on the right.
- Notices: mango tint, used for drafts and for “selling is off”.

## Motion

Framer Motion runs the hero word reveal, the hero float, the scroll assembly, page fade, and the cart drawer. Lenis smooths wheel scrolling and is not started when `prefers-reduced-motion` is set. GSAP and Three.js are not loaded. The assembly section is the signature: ingredient chips converge, then the headline and the shop link appear. It is captioned as an illustration, not a recipe.

## Layout

Max width `72rem`. Mobile has its own bottom bar (Shop, Search, Box, Account, Cart) and a sticky add-to-cart on the product page. Desktop pins the product visual while the story scrolls.

## What not to add

Glass panels, generic purple gradients, gym-only photography, fake 3D packs, countdown timers, or star ratings with no reviews.
