# Branding

Source art for the To Do fork, and the script that turns it into what the app
ships.

- `luna-portrait.svg`, `luna-full-body.svg` — Luna the sheepadoodle, kept
  verbatim. They are traced vectors (0.7–0.9 MB each), too heavy to ship
  as-is.
- `build.py` — regenerates, from those two files:
  - `frontend/src/assets/logo.svg`, `logo-full.svg`, `logo-full-pride.svg`:
    vector circle + Luna as an embedded 320px WebP. The "To Do" wordmark stays
    vector, so it follows light/dark mode.
  - `frontend/src/assets/luna-portrait.webp` (login page) and
    `luna-full-body.webp` (empty task list), at 2x.
  - `frontend/public/favicon.ico` and every PNG in `frontend/public/images/icons/`.

## Regenerate

```sh
python3 -m venv /tmp/branding-venv
/tmp/branding-venv/bin/pip install resvg-py pillow
/tmp/branding-venv/bin/python branding/build.py
```

Then bump the `?v=` on the icon URLs (`frontend/index.html`, the manifest
icons in `frontend/vite.config.ts`, `frontend/src/composables/useTimeTrackingFavicon.ts`)
and `VERSION` in `.github/workflows/todo-image.yml`. Vikunja serves images
with a 1-year `immutable` Cache-Control, so Cloudflare and browsers keep the
old icons until their URLs change.
