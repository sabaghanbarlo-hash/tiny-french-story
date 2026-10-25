# Tiny French 🇫🇷

*French, one tiny story at a time. — Small steps. Big dreams.*

Paste a directed script, get an animated French-learning **Reel** (9:16, 1080x1920) starring two original characters, **Marinette** and **Adrien**. Instagram auto-posting arrives with the workflow stage.

## Status (stage 3 of 5 done)
| Works now (tested) | Not built yet |
|---|---|
| French parser: accents, translations, vocab/grammar/quiz, line-numbered errors | Thumbnail/cover and Instagram caption file |
| Stage directions acted out: enter/exit, walk/run to named spots, expressions, gestures, hold/buy/pick up/eat/drink/give/put away | Composio Instagram posting, GitHub Actions workflow, studio web page |
| Marinette and Adrien rigs (fixed outfit/hair/proportions, 9 expressions, walk cycle, mouth follows the voice) | Director prompt and directing guide (DIRECTING.md) |
| 6 Paris scenes with named spots, 15 objects | 12 more scenes (supermarket, bookstore, restaurant, train station, museum, Eiffel viewpoint, airport, market, library, beach, courtyard, apartment) |
| French voices (Denise / Henri), hard error if unavailable; UTF-8 SRT | Bicycle object, more gestures |
| 17 automated tests (parser, directions, collisions, items, no teleporting) | |

**Scenes:** street (lamp, bench, shop window) · bakery (entrance, window, counter, display) · cafe (entrance, table, counter) · park (bench, fountain) · classroom (door, board, desk) · metro (entrance, ticket machine, platform)
**Objects:** croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream
**Feelings:** happy, sad, confused, surprised, embarrassed, worried, excited, shy, neutral

Samples (real French voices): [docs/samples/02-journee-a-paris.mp4](docs/samples/02-journee-a-paris.mp4) (4 scenes), still frames beside it.

## Run locally
```
pip install -r requirements.txt   # plus ffmpeg and fonts-dejavu-core
python lesson.py lessons/02-journee-a-paris.txt -o output --preview output/frames
python test_parser.py && python test_acting.py
```
`--dummy-audio` gives test tones instead of voices (tests only). On a tiny machine set `TF_LOWMEM=1` for a lighter x264 encode.

## Known limits
Characters are drawn front-facing (mirrored left/right), not true side views. A full lesson with vocab, grammar and a quiz is about 2 minutes; Reels-length trimming comes later. The sample was checked by code (sizes, motion, audio, text bounds) plus unit tests, and has not yet been reviewed by eye.

## Instagram setup
Repo variables `IG_ACCOUNT` and `IG_EXPECT_USERNAME` are set. A `COMPOSIO_API_KEY` repository secret is still needed before anything can post. No credentials are ever committed.
