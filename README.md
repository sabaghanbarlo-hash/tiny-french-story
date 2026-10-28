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

## Choosing when a Reel posts
Studio page → **When to post to Instagram** → *Queue: post at a time I choose*, then pick the date and time (your device's time zone). Without a chosen time a Reel takes the next best slot from `queue/schedule.json`.
- Already queued? Open the **queue** page and use **Change time** on any waiting Reel (it also clears a "failed" status so it tries again).
- From GitHub Actions: run *Generate lesson video* with `post: queue` and `post_at: 2026-10-30T18:30Z` (UTC; `+03:30`-style offsets also work).
- Your own times ignore the 2-a-day limit, so you can stack posts closer together if you want. A time that has already passed posts at the next check.
- Posts go out within about 15-30 minutes after the chosen time (GitHub's scheduler is not exact).
- Command line: `python queue_tool.py add ... --post-at 2026-10-30T18:30Z` or `python queue_tool.py reschedule --stem NAME --post-at "2026-10-31 09:00"`.

## Thumbnails (Small videos)
Every Small video now gets its own designed cover (`<name>.cover.png`, and the `.jpg` Instagram uses): the two friends at the table, a *Learn French* tag with the episode number, the title in large type, and chips with today's words. Nothing important sits in the top 240 px or bottom 400 px, so it survives Instagram's grid crop and Reel buttons.
- Want a shorter title on the thumbnail? Add a line `cover: Meet Adrien` to the script (the real title is still used everywhere else).
- Preview only the cover in a second, no voices or video needed: `python small.py lessons/small/01-meeting-for-the-first-time.txt --cover cover.png`
- If the cover ever fails to draw, the video is still made and a frame from it is used instead (a warning shows in the job log).
