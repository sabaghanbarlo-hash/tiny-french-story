# Tiny French 🇫🇷

*French, one tiny story at a time. — Small steps. Big dreams.*

Paste a directed script, get an animated French-learning **Reel** (9:16) starring two original characters, **Camille** and **Julien**, then have it posted automatically to Instagram.

> **Status: work in progress (phase 1 done).** Nothing renders yet. See [docs/BASELINE.md](docs/BASELINE.md) for what has been inspected, what is confirmed, and the build plan.

## Direction
- **Reels first** (1080x1920, vertical, Instagram auto-post). The full-length 1920x1080 YouTube version comes later.
- Built on the architecture of `tiny-japanese-story` (script parser -> acting layer -> Pillow-drawn rigged characters -> ffmpeg), which stays untouched.
- Free stack only: edge-tts voices, Pillow, ffmpeg, GitHub Actions + Pages. Instagram posting goes through Composio.

## Instagram setup
Repo variables `IG_ACCOUNT` and `IG_EXPECT_USERNAME` are already set. A `COMPOSIO_API_KEY` repository secret is still needed before anything can post. No credentials are ever committed to this repo.
