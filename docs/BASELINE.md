# Baseline: what exists and what the build needs

Source inspected: `sabaghanbarlo-hash/tiny-japanese-story` (read-only; not modified).

## Reference architecture (confirmed by reading the code)
| File | Role |
|---|---|
| `lesson.py` (~985 lines) | script parser, voice synthesis (edge-tts, gTTS fallback), slide cards, vocab/grammar/quiz, SRT, ffmpeg encode |
| `acting.py` (~963 lines) | stage directions -> keyframes, rigged character drawing (walk, arm, expressions, held items), scene drawing, landmarks |
| `thumb.py` | thumbnail from a template image |
| `.github/workflows/render.yml` | manual dispatch -> render -> commit outputs to `docs/videos` |
| `docs/index.html` | studio page that triggers the workflow with a GitHub token saved in the browser |

## Limits found in the reference (must change for Tiny French)
- Output is **hard-coded 1920x1080 @ 24 fps** (`W, H, FPS` in `lesson.py`). Reels need 1080x1920, so layout, scenes and character placement need a vertical redesign, not a flag.
- Characters Mika/Alex, 13+ Japan-flavoured scenes, items and rides are Japan-specific.
- Japanese coupling: kana regexes, `pykakasi` romaji, `ja-JP` voices, romaji/English split logic.
- The reference has **no Instagram posting**; that must be added (Composio).
- The workflow renders in a loop and publishes to `docs/videos`; `STRICT_VOICE=1` makes a missing natural voice a hard error.

## Confirmed for French
- Free neural voices exist and synthesize: `fr-FR-DeniseNeural` (female, planned for Marinette) and `fr-FR-HenriNeural` (male, planned for Adrien). Test synthesis of "Bonjour ! Tu veux un croissant ?" produced audio.

## Build plan
1. Vertical 1080x1920 pipeline + French parser (no romaji) + SRT with French/English.
2. Marinette and Adrien rigs; Paris scenes, objects, named spots (only what is truly drawn goes into the director prompt).
3. French director prompt and directing guide matching the implementation.
4. Thumbnail/cover, Instagram caption, Composio posting workflow, studio page.
5. Test render, inspect frames and audio, GitHub Actions run, Pages deploy.
