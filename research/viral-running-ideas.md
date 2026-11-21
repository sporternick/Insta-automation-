# Viral running ideas (Nov 2026)

**Source:** 134 public running / track Shorts on YouTube from 12 searches,
ranked by **outlier multiple** = views ÷ that channel's median Shorts views.
106 had enough channel history to rank; 32 relevant ones at 3x or more after
removing noise (vans named "Sprinter", shorts-the-clothing ads, music).
Raw data: `running_shorts.tsv`. Hook-formula pass: `swipe.md`.

**Caveats:** YouTube blocks caption downloads from cloud servers, so hooks are
the video *titles* (usually the on-screen text), not the spoken first line.
Instagram itself could not be read without a login. 32 videos is enough to
see patterns, not to prove them. Re-check after a month of posting.

## What over-performed (top outliers, read by hand)

| x over own median | video | pattern |
| --- | --- | --- |
| 1371x | FloTrack: "This 5-Year-Old 200m Is Everything Great About Track" | kids / wholesome |
| 657x | Telegraph: sprinter's 22-second 100m | absurd / fail |
| 604x | Van Niekerk 400m world record | iconic record moment |
| 396x | Fraser-Pryce "destroys other parents" at son's school race | **elite vs normal people** |
| 288x | HYROX: "What is HYROX?" | explainer for outsiders |
| 260x / 202x | UNI Athletics: gun going off / the starter | **raw POV of the start** |
| 245x | StrengthRunning: carioca drill demo | one drill, demonstrated |
| 230x | Olympics: "Julmis falls in hurdles and finishes the race" | **fall + resilience, hurdles** |
| 141x | "Hurdles (super slow motion)" | **slow-mo hurdle clearance** |
| 126x | London Marathon final finisher cheered | underdog emotion |
| 36x | British sprinter slows before the line, gets overtaken | celebrating too early |
| 14x / 7x | "KICKING vs BOUNCING", "heel vs forefoot" | **A vs B technique** |

**What the winners share:** short titles (top third 8.5 words vs 11.5),
one moment rather than a whole race, and a payoff you *see* (fall, finish,
clearance, a 5-year-old) rather than one you are told about.

## 8 reels for an Olympic 400m hurdler

Each has a hook, what to film and the edit command. `IN.mp4` is your upload.

1. **Elite vs normal people** (Fraser-Pryce 396x)
   Race club runners or your teammates' kids over 3 mini-hurdles; you give them a head start.
   Hook: `Olympian vs 5 club runners. 3 hurdles head start.`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --hook "Olympian vs 5 club runners" --card "3-6:they got 3 hurdles head start"`

2. **Super slow-mo hurdle clearance** (141x)
   Side-on, phone at hurdle height, 120/240fps if your phone has it.
   Hook: `What 0.3 seconds over a hurdle looks like`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --slowmo 2-3@0.25 --hook "0.3 seconds over a hurdle"`

3. **POV: the gun** (260x / 202x)
   Phone on the blocks or chest mount, last 5 seconds before the gun to hurdle 1.
   Hook: `POV: 400m hurdles, Olympic final heart rate`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --hook "POV: the 5 seconds before the gun"`

4. **The fall** (Julmis 230x, sprinter-slows 36x)
   Your own worst hurdle crash or a near-miss, with what you learned.
   Hook: `Hurdle 9. Olympic year. This happened.`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --slowmo 4-6@0.3 --hook "Hurdle 9. This happened." --card "7-11:what I changed after"`

5. **A vs B technique** (14x, 7x)
   Same drill twice: wrong trail leg vs right trail leg, split by a cut.
   Hook: `Trail leg: amateur vs Olympian`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --hook "Trail leg: amateur vs Olympian" --card "0-4:amateur" --card "4-8:Olympian"`

6. **One drill** (245x)
   One hurdle mobility drill, 3 reps, the cue on screen.
   Hook: `The hurdle drill I do every single day`

7. **Explainer for outsiders** (HYROX 288x)
   "What is the 400m hurdles?" in 30 seconds: 10 hurdles, 35m spacing, stride pattern, why lap 2 hurts.
   Hook: `Why the 400m hurdles is the hardest race in athletics`

8. **4x400 relay hand-off** (record / emotion pattern)
   Your Apeldoorn 4x400 squad, the exchange in slow motion.
   Hook: `The 0.5 seconds that decide a 4x400`
   `python3 scripts/edit_reel.py IN.mp4 out.mp4 --slowmo 3-4@0.3 --hook "The 0.5 seconds that decide a 4x400"`

Run any hook through `/ig-reel` to score it before you shoot.
