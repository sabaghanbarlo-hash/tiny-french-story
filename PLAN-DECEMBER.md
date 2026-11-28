# Tiny French - Instagram plan, Dec 7 2026 - Jan 5 2027

Written 28 Nov 2026 from @tiny.french insights (74 Reels, 27 Oct - 28 Nov). 90 new scripts keep all three daily Reels posting through the month.

## What the numbers say

| What | Result |
|---|---|
| Typical Reel | median **1,783 views**, very steady. 70 of 74 Reels sit between 0.7x and 2.1x. Only 4 got under 0.4x |
| The one outlier | *Count to three in French in 10 seconds* (15 Nov): **26,664 views (15x), 296 saves, 434 shares**. Eight Reels in the same "in 10 seconds" family (colors, days of the week, yes and no, I love it, I don't know...) all landed at 0.9-1.1x, so this is **not a repeatable formula**, most likely one big share |
| Best repeatable ones | *How French people actually say "hi, how are you?"* 2.1x (148 saves, 116 shares); *Bugaboo & Cat vs. the Croissant Thief* 1.8x; *Order a coffee in France like a local* 1.6x; *Taking a taxi in Paris?* 1.5x |
| Hook / format / hour | no visible effect. Main, Practice and Mistake Reels all sit around 1.0x and every posting hour is the same |
| Audience | only about 27% of reach comes from the US, UK, Canada, Australia, NZ and Ireland, so French-speaking markets matter. Keep the English on screen |

Confidence: medium for "steady and flat" (74 Reels), **low** for any formula (a single outlier). I did not build a competitor swipe file (needs browsing Instagram with you present).

## What is not working
1. Nothing is broken, but nothing compounds either: every Reel lands near 1,800 whatever the topic.
2. The Nov 15 hit has not repeated in eight tries, so do not copy it.
3. Hooks that are only a topic ("Say the colors in French") get about 1.0x. "How French people actually say..." and character stories did best.

## The plan
1. **Main Reel (14:00 UTC, 30 scripts, 7 Dec - 5 Jan):** keeps the weekly rhythm in `PLAN.md` (Mon travel, Tue "actually say", Wed conversation, Thu mistakes, Fri culture, Sat food and shopping, Sun Bugaboo & Cat), with Christmas, New Year, galette des rois and winter sales on their dates.
2. **Fill-in-the-blank on every caption:** a new "Your turn" line. `PLAN.md` found these were the only thing that produced comments.
3. **Practice (22:00 UTC, 30 scripts, 30 Nov - 29 Dec)** and **Mistake & fix (06:00 UTC, 30 scripts, 1 Dec - 30 Dec):** new banks `bank-practice/` and `bank-mistake/`. Mistakes are real beginner errors: AVOIR vs ETRE, missing articles, false friends (librairie, chair, sensible).
4. **Test, not assume:** repeat the "in 10 seconds" idea only with new topics; if one of them passes 3x, write a batch of that family in January.

## Checkpoints
- **13 Dec, 27 Dec, 3 Jan:** median views and top 3 Reels. Anything above 3x gets named and reused.
- Check which captions got comments: if the blank prompts work, move the prompt to the on-screen text.

## What is in this change
`story-bank/` main scripts (30 x script + caption), `bank-practice/` and `bank-mistake/`. File names carry the posting time in UTC (`YYYYMMDDHHMM-name`) so the existing refill workflows pick them up on their normal runs. No code or workflow is changed. All 90 pass `small.py` parsing and scene checks.

## Posting calendar (main Reels, 14:00 UTC)

| Date | Script | Hook |
|---|---|---|
| 2026-12-07 | train ticket | Buying a train ticket in France? 🚆🇫🇷 Say THIS |
| 2026-12-08 | 5 ways to say yes | Stop saying only "oui" 😎 5 ways to say yes in French 🇫🇷 |
| 2026-12-09 | weekend plans | What are you doing this weekend? Say it in French 🇫🇷 |
| 2026-12-10 | feelings with avoir | I'm hot, cold, thirsty… in French you HAVE it, not "are" it 😳🇫🇷 |
| 2026-12-11 | la bise | In France, saying hello can mean kissing on the cheek 😘🇫🇷 |
| 2026-12-12 | at the supermarket | Grocery shopping in France? 🛒🇫🇷 Ask for this |
| 2026-12-13 | the snowman | Bugaboo & Cat build a snowman ☃️ (and it melts!) |
| 2026-12-14 | museum tickets | Museum in France? 🖼️🇫🇷 Say THIS at the ticket desk |
| 2026-12-15 | 5 ways to say sorry | 5 ways to say sorry in French, from "pardon" to "navré" 🙏🇫🇷 |
| 2026-12-16 | your hobbies | What do you like to do? Say it in French 🎨🇫🇷 |
| 2026-12-17 | never say je suis plein | Never say "je suis plein" ❌ after a big meal 😳🇫🇷 |
| 2026-12-18 | christmas eve dinner | Christmas Eve in France = a LONG dinner 🎄🍽️🇫🇷 |
| 2026-12-19 | buche de noel | Order a bûche de Noël in France 🎂🎄 Say THIS |
| 2026-12-20 | the christmas tree | Bugaboo & Cat decorate the tree 🎄😹 (disaster!) |
| 2026-12-21 | at the airport | Flying through a French airport? ✈️🇫🇷 Say THIS |
| 2026-12-22 | holiday wishes | Merry Christmas isn't the only way to say it 🎅🇫🇷 5 holiday wishes |
| 2026-12-23 | christmas plans | What are you doing for Christmas? 🎄🇫🇷 Say it in French |
| 2026-12-24 | never say je suis accord | Never say "je suis accord" ❌ Say this instead ✅ |
| 2026-12-25 | opening presents | Opening gifts in French 🎁🇫🇷 Say this |
| 2026-12-26 | ordering dessert | Dessert in France? 🍮🇫🇷 Order like this |
| 2026-12-27 | the missing gift | Bugaboo & Cat vs. the missing Christmas gift 🎁🐕 |
| 2026-12-28 | which platform | Which platform? 🚉🇫🇷 Say THIS at the French train station |
| 2026-12-29 | 4 ways i dont know | Stop saying only "je ne sais pas" 🤷 4 ways to say it in French |
| 2026-12-30 | new years eve plans | New Year's Eve plans in French 🥂🇫🇷 |
| 2026-12-31 | midnight countdown | Countdown to midnight in French! 🎆🇫🇷 10 to 1 |
| 2027-01-01 | new year resolutions | Happy New Year in French + your resolution 🎉🇫🇷 |
| 2027-01-02 | galette des rois | Galette des rois time! 👑🇫🇷 Order like this |
| 2027-01-03 | the lucky charm | Bugaboo & Cat find the charm in the king cake 👑🐱 |
| 2027-01-04 | winter sales | Winter sales in France? 🛍️🇫🇷 Say THIS |
| 2027-01-05 | 5 ways good luck | Good luck in French: 5 ways to say it 🍀🇫🇷 |

## Checks
- **The French has not been checked by a native speaker.** Please skim before they go live. Things I would check first: informal "Quel film vous allez voir ?", "composter mon billet", "Chais pas", the notes on "je suis plein", "la toilette" and "je t'adore" for friends, and "assister à".
