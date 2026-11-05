# Tiny French - Instagram plan, Nov 7 - Dec 6, 2026

*Small steps. Big dreams.* One Reel a day at 14:00 UTC (17:30 Tehran, 15:00 Paris), 30 scripts in `story-bank/`, rendered and posted automatically.

## What the numbers say (12 Reels, Oct 27 - Nov 4, via @tiny.french insights)

Account: 341 followers, 12 Reels, 19,119 views, 1,050 likes, 518 saves, 294 shares, 19 comments in total.

| What | Result |
|---|---|
| Typical Reel | about 1,300-1,800 views (median 1,519), reach 1,150-1,550. Very steady day to day |
| Best Reel | **"How French people actually say hi, how are you?"** (Oct 27): 3,376 views, 5.2% saves, 3.5% shares, 12.7 s average watch. About 2x a normal Reel, and the only breakout |
| Next best | "Meeting someone French? Say these 5 phrases" 1,838 · "What do you like to do?" 1,742 · "Saving Paris" (Bugaboo & Cat) 1,621, with the 2nd-best share rate (3.0%) |
| Weakest | The Tiny French promo Reel (Nov 3): 1,407 views but only 4.6 s average watch and 0.9% shares. Generic "learn French with…" intros hold nobody |
| Comments | 18 of 19 comments came from just two Reels, and both asked for a **fill-in-the-blank or an emoji** ("Moi, c'est ___, j'ai ___ ans", "comment 🥖"). A plain "reply with…" got 0 |
| Posting time | No visible effect: 14:00-19:30 UTC all landed in the same range. The hook matters far more than the hour |

**What works**
1. A "how people *actually* talk" hook ("How French people actually say…") beats a "learn these phrases" hook.
2. Save and share asks work: the best Reels have 3-5% save rates.
3. Bugaboo & Cat stories get shared more than standard dialogues.
4. Fill-in-the-blank comment prompts are the only thing that creates comments.

**What does not**
1. Generic or channel-promo Reels ("Learn French with Marinette & Adrien, one tiny story at a time").
2. Repeating a hook: "Lost in France? These 5 phrases…" went out twice.
3. A caption that doesn't match the video: the Nov 1 Reel (shopping for clothes) went out with the Oct 31 directions caption.
4. Questions without a blank to fill ("reply with…"): 0 comments.

## The plan

Weekly rhythm, so people know what to expect:

| Day | Pillar | Why |
|---|---|---|
| Mon | Travel survival | Highest-intent searchers, very saveable |
| Tue | "How French people actually say…" | The proven breakout format |
| Wed | Conversation | Fill-in-the-blank comment prompts |
| Thu | Mistakes and false friends | Shareable ("send this to a friend learning French") |
| Fri | Culture | Friday the 13th, Black Friday, Christmas |
| Sat | Food and shopping | Easy to relate to, easy to save |
| Sun | Bugaboo & Cat story | Weekly series, best share rate |

(The first week starts on Saturday Nov 7, so the pillars shift by a day for the first few Reels; after that the rhythm above holds on the calendar in `story-bank/SCHEDULE.md`.)

Every Reel has: a curiosity hook line, 5 phrases, one comment prompt with a blank to fill, a save ask and a send ask. Every 5th Reel adds the YouTube link (@tinyfrench9).

## How it runs (same idea as Tiny Japanese)

1. `story-bank/` holds the scripts, named `YYYYMMDD1400-name.txt` + `.caption`. The prefix is the posting time (UTC).
2. **Daily refill** (`.github/workflows/daily-refill.yml`) runs every day at 05:30 UTC. It picks every script that posts within the next 4 days, checks it, renders the video with the French voices, and adds it to the queue at its exact time. It then refreshes the website so the video link exists.
3. **Post queued Reels** (the existing workflow, every 15 minutes) posts whatever is due.
4. If a render fails, the script stays in `story-bank/` and is retried on the next run. If the bank is nearly empty the workflow warns in its log.

Change a day: rename the two files with the new date. Skip a Reel: delete both files (before its render). Add a Reel: drop in a new `.txt` + `.caption`. Stop everything: disable **Daily refill** in the Actions tab.

## Checks

- All 30 scripts pass the repo's own script checker, and the refill was tested end to end (pick, render, queue, re-run does not duplicate).
- **The French has not been checked by a native speaker.** It is written at A1 level in simple, common phrases, but please skim the scripts, especially the "Mistakes" Reels (Thu), before they go live.
- Instagram numbers are a snapshot from Nov 5; the newest Reels may still grow.
