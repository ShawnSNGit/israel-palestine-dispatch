# Dispatch — Israel/Palestine, side by side

A single-page news aggregator that puts Israeli, Palestinian/Arab, and international
coverage of Israel-Palestine next to each other, with no editorializing.

**[View live demo](#)** — replace with your GitHub Pages URL once deployed (see below).

## What it does

- Three columns, grouped by where each outlet is based (not by any judgment of accuracy):
  - **Israeli press** — Haaretz, The Times of Israel
  - **Palestinian & Arab press** — Al Jazeera, Al Arabiya
  - **International wire & broadcast** — CNN
- An "At a glance" summary panel synthesizing the throughlines across all three columns.
- A source-ratings table pulled from [Media Bias/Fact Check](https://mediabiasfactcheck.com/),
  with a note that it's one reviewer among several (AllSides, Ad Fontes) and shouldn't be
  read as ground truth.
- A best-effort **live refresh**: on load and on demand, it pulls public RSS feeds for
  The Times of Israel, Al Jazeera, and CNN through a third-party feed-reader proxy
  (rss2json.com), since browsers can't fetch most news sites directly (CORS).
  Haaretz and Al Arabiya don't expose usable public feeds, so those halves of their
  columns always show the built-in snapshot — a status dot per column shows live
  (green) vs. snapshot (amber/red) plainly, it never fakes freshness.

## Running it

It's a single static HTML file with no build step and no backend.

```bash
# just open it
open index.html

# or serve it locally
python3 -m http.server 8000
```

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. Repo **Settings → Pages → Source**: select the `main` branch, root folder.
3. Save — GitHub gives you a URL like `https://<username>.github.io/<repo>/` within
   a minute or two.
4. Swap that URL into the "View live demo" link above.

## Known limitations

- Live refresh depends on a free third-party proxy (rss2json.com); it can rate-limit
  or go down, in which case columns fall back to the snapshot automatically.
- Haaretz and Al Arabiya are snapshot-only — no live refresh — because neither
  publishes a public RSS feed suitable for this.
- The MBFC ratings table reflects one point-in-time pull and one organization's
  methodology; it's meant as a starting point for the reader's own judgment, not a
  verdict.

## License

MIT — see [LICENSE](LICENSE).
