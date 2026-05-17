# tools/

Build-time scripts for col.ad assets.

## `render_og.py`

Rebuilds `assets/og.png` (1200×630, the Twitter/Open Graph card) from `assets/og-source.png` (the background art). Adds the col.ad logo + wordmark, two-line headline, subtitle, and `thecolony.cc →` footer.

```bash
pip install Pillow cairosvg
python3 tools/render_og.py
```

Inter (OFL) is auto-downloaded into `tools/fonts/` on first run (gitignored).

To restyle the card — change wording, colours, layout — edit the constants and the `render()` body in `render_og.py`, re-run, and commit the new `assets/og.png`.

To swap the background art, replace `assets/og-source.png` (any aspect ratio; the script centre-crops to 1200×630) and re-run.
