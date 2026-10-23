# Tiny French 🇫🇷

*French, one tiny story at a time. — Small steps. Big dreams.*

Paste a directed script, get an animated French-learning **Reel** (9:16, 1080x1920) starring two original characters, **Camille** and **Julien**. Run it from the command line or from the local studio page.

## Studio (the easy way)
```
pip install -r requirements.txt   # plus ffmpeg and fonts-dejavu-core
python studio.py                  # opens http://127.0.0.1:8765
```
Paste or load a lesson, press **Check script** (errors point to the line), then **Create video**. You get an in-page preview and downloads for the MP4, SRT subtitles, cover image and Instagram caption. It runs the same `lesson.py` pipeline on **your own computer**, one video at a time. It cannot run on GitHub Pages, which has no Python or FFmpeg. The page only answers on `127.0.0.1`.

**Try it in the browser without installing anything:** on GitHub press **Code → Codespaces → Create codespace**. The `.devcontainer` setup installs FFmpeg and fonts and starts the studio; open the forwarded port 8765 (the first set-up takes a few minutes). Free personal accounts get a monthly Codespaces allowance (see GitHub's billing page), and the port stays private to your login. By hand: `python studio.py --host 0.0.0.0 --allow-any-host --no-browser`. Use those two flags only on a private forwarded port.

## Hosted studio (GitHub Pages + GitHub Actions)
Same idea as the other studios: open the page, paste a script, press **Create video**, and the Reel plays in the same page when it is done. Rendering runs on GitHub's servers (free Actions minutes), not on your computer. **Nothing is posted anywhere.**

One-time setup (the repo owner):
1. Merge to `main` (workflows only run from the default branch).
2. Repo **Settings → Pages → Deploy from a branch → `main` / `/docs`**. The page is then at `https://<your-user>.github.io/tiny-french-story/`.
3. Create a [fine-grained token](https://github.com/settings/personal-access-tokens/new) for this repo only with **Actions: Read and write** and **Contents: Read**, and paste it into the page once. It is kept in your browser only.

How it works: the page starts the **Make Tiny French reel** workflow (`.github/workflows/make-reel.yml`) with your script. `scripts/ci_render.py` checks the script (errors name the line), renders it with `lesson.py`, and copies the MP4, SRT, cover and caption into `docs/previews/` (newest 6 kept; older ones are deleted). The page waits for the site to publish them and plays the video. Every run's files are also kept 14 days as a workflow artifact. Preview videos are committed to the repo by a bot, so the repo grows a little with each render.

## Status
| Works now (tested) | Not built yet |
|---|---|
| French parser: accents, translations, vocab/grammar/quiz, line-numbered errors | Instagram auto-posting (needs the `COMPOSIO_API_KEY` secret) |
| Stage directions acted out: enter/exit, walk/run to named spots, expressions, gestures, hold/buy/pick up/eat/drink/give/put away | GitHub Actions workflow |
| Camille and Julien rigs (fixed outfit/hair/proportions, 9 expressions, walk cycle, mouth follows the voice) | YouTube title/description and lesson-JSON export |
| 18 scenes with named walkable spots, 15 objects | Bicycle object, more gestures |
| French voices (Denise / Henri), hard error if unavailable; UTF-8 SRT; cover image; Instagram caption | Side-view character turns (characters are mirrored front views) |
| Local studio web page (`studio.py`) with validation, rendering, preview and downloads | |
| Directing guide ([DIRECTING.md](DIRECTING.md)), generated from the code so it only lists what exists | |
| Automated tests: parser, directions, collisions, items, scenes, docs, studio | |

**Characters:** *Camille* (blue-black hair in a high bun with a red ribbon, rose cardigan) and *Julien* (blond swept hair, navy-and-white breton shirt, red neckerchief). Both are original designs.
**Scenes:** street (lamp, bench, shop window) · bakery (entrance, window, counter, display) · cafe (entrance, table, counter) · park (bench, fountain) · classroom (door, board, desk) · metro (entrance, ticket machine, platform) · supermarket (entrance, fruit stand, shelves, checkout) · bookstore (entrance, shelves, reading corner, counter) · restaurant (entrance, table, window table, counter) · train station (entrance, ticket window, departures board, platform) · museum (entrance, painting, statue, bench) · eiffel (steps, viewpoint, bench) · airport (entrance, check-in, seats, gate) · market (entrance, fruit stall, cheese stall, flower stall) · library (entrance, shelves, reading table, desk) · beach (umbrella, sandcastle, shore) · courtyard (archway, tree, fountain, bench) · apartment (door, sofa, window, bookshelf)
**Objects:** croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream
**Feelings:** happy, sad, confused, surprised, embarrassed, worried, excited, shy, neutral

Samples (real French voices): [docs/samples/02-journee-a-paris.mp4](docs/samples/02-journee-a-paris.mp4) (4 scenes), still frames beside it.

## Run locally
```
pip install -r requirements.txt   # plus ffmpeg and fonts-dejavu-core
python lesson.py lessons/04-au-supermarche.txt -o output --preview output/frames
python test_parser.py && python test_acting.py && python test_docs_meta.py && python test_scenes.py && python test_studio.py
```
`--dummy-audio` gives test tones instead of voices (tests only). On a tiny machine set `TF_LOWMEM=1` for a lighter x264 encode.

## Known limits
Characters are drawn front-facing (mirrored left/right), not true side views. A full lesson with vocab, grammar and a quiz is about 2 minutes; Reels-length trimming comes later. Renders were checked by code (sizes, audio streams, directions animated, scene spacing) plus unit tests; the redesigned characters and the newer scenes have not yet been reviewed by eye, so please look at a few frames before publishing.

## Instagram setup
Repo variables `IG_ACCOUNT` and `IG_EXPECT_USERNAME` are set. A `COMPOSIO_API_KEY` repository secret is still needed before anything can post. No credentials are ever committed.
