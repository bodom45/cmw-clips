# Handoff — Frequency Sessions neighbor landing page

**Branch:** `claude/frequency-sessions-voting-page-lpozze` (repo `bodom45/cmw-clips`)
**Status:** Built, never deployed. The event (Wed Sept 30, 2026) has passed, so this page as written is stale.

## What the ask was
The resident/neighbor flyers for Frequency Sessions had a QR code. Brandon wanted the QR to land on a page that:
1. Explains what the event is (so neighbors know who/what they're voting for)
2. Shows photos of Gallery DeFi
3. Has a checkout button to Stripe with the neighbor buy-one-get-one code applied

## What exists
- `frequency/index.html`: a single static mobile-first page with no build step. It includes:
  - A hero, a "What is this?" section, 4 how-it-works steps, a judges 70% / crowd 30% bar, the prizes, a gallery grid, the details and a final CTA, plus a ticket button that stays pinned while scrolling.
  - **Config is at the bottom of the file** (`CONFIG.checkoutUrl`, `CONFIG.promoCode`). Every ticket button goes to `checkoutUrl?prefilled_promo_code=<CODE>`, which is Stripe Payment Link's built-in promo prefill. A `?code=XYZ` on the page URL overrides the default code. This is the same pattern as the World Cup `?code=MAPLEBOGO` flyers.
- `frequency/img/`: 4 stills pulled from `DJ_173.mp4`, the Frequency Sessions × Gallery DeFi promo clip. They are 720px wide and somewhat soft, so swap in real photos if you have them.

## Open blockers (never received from Brandon)
1. **The Stripe ticket link.** It's still a placeholder (`REPLACE_WITH_TICKET_LINK`). `buy.stripe.com/8x214o7TWbfPbdm4X573G0E` is the **$25 performer lock-in** link, NOT the ticket link.
2. **The neighbor code.** `NEIGHBOR` is a guess and has to exist as a promotion code on that Stripe link. The deal was described as both "buy 1 get 1" and "buy 1 get 2", which was never confirmed.
3. **The URL the printed QR points to.** The flyer and QR came from an earlier session and nothing found records the URL. If the flyers are printed, the page has to live at that exact URL.
4. **Hosting.** The page hasn't been deployed anywhere.

## Important context found along the way
- **ctv-showcase.vercel.app is the real Frequency Sessions ticket and voting site** (Vercel project `prj_14Jhs3VFfJr3zwQAT0NKzGHHbZQ9`, Next.js app).
  - Its tagline is "Every ticket is a vote." Each artist has a page at `/a/<slug>` with a Stripe ticket link. The sale is tagged to the artist via `client_reference_id`, and a webhook writes it to Supabase. There's a `/leaderboard` page.
  - Config lives in `src/lib/event.ts` (`EVENT`, `PRICES`, `ARTISTS`, `ticketLinkFor`).
  - Its source isn't in any GitHub repo this session could reach. The live site is blocked by the sandbox egress proxy, and Vercel's file API truncates long files, so the ticket price and links were never read.
  - The QR on the neighbor flyer most likely points somewhere on this site.
- **The voting rules contradict each other:**
  - The site says "Biggest crowd advances", meaning ticket sales decide.
  - The artist acceptance emails say judges 70% plus live crowd vote 30%, top 4 to the Finale, announced the next day at noon.
  - The landing page uses the 70/30 version. Its ticket button does **not** credit an artist, so a neighbor buying through it wouldn't count as a vote for anyone.
- **There are no "five stages".** Brandon said this is wrong and it's been removed from the page. The artist acceptance emails still say "five stages", so the artists were told that.
- **Event facts (from the acceptance emails):** Wed Sept 30, doors 7:00 PM, show 7:30–11:00 PM. Gallery DeFi, 2200 Evanston Ave, Dallas TX 75208. 20 acts, one song / 4 minutes each, live house band, Tiny Desk style. Prize: $1,000, a directed music video and a marketing package.

## If this gets picked up again
- **For a future event:** update the date, copy and prize, get the real ticket link and promo code, and decide which voting rules are true. Then either deploy `frequency/` as a static Vercel project, or route the ticket buttons into the artist picker on ctv-showcase so each ticket counts as a vote.
- **For a recap of this event:** reuse the page shell and gallery images, and swap the ticket CTA for results and video links.
