# Tiny French 🇫🇷

*French, one tiny story at a time. — Small steps. Big dreams.*

Paste a directed script, get an animated French-learning **Reel** (9:16, 1080x1920) starring two original characters, **Camille** and **Julien**; Instagram auto-posting comes with the workflow stage.

## Status (stage 2 of 5 done)
| Works now (tested) | Not built yet |
|---|---|
| French script parser with accents, translations, vocab/grammar/quiz, clear errors (6 unit tests) | Stage-direction animation (directions are parsed but **not acted out yet**) |
| French voices (Camille = `fr-FR-DeniseNeural`, Julien = `fr-FR-HenriNeural`), hard error if a voice is unavailable | Real Camille/Julien rigs (current figures are simple placeholders) and the Paris scene library |
| 1080x1920 H.264 + AAC render, 24 fps, mouth moves with the voice | Thumbnail/cover, Instagram caption file, Composio posting, studio web page, GitHub Actions workflow |
| UTF-8 SRT (French line over English line) | Director prompt and directing guide |

Sample output (placeholder look): [docs/samples/01-bakery.mp4](docs/samples/01-bakery.mp4), still frames in `docs/samples/`.

## Run locally
```
pip install -r requirements.txt   # plus ffmpeg and fonts-dejavu-core
python lesson.py lessons/01-bakery.txt -o output --preview output/frames
python test_parser.py
```
`--dummy-audio` gives test tones instead of voices (never use it for real videos). On a tiny machine set `TF_LOWMEM=1` for a lighter x264 encode.

## Instagram setup
Repo variables `IG_ACCOUNT` and `IG_EXPECT_USERNAME` are set. A `COMPOSIO_API_KEY` repository secret is still needed before anything can post. No credentials are ever committed.
