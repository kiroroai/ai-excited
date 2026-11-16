[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/kiroroai/ai-excited/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/kiroroai/ai-excited/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

# IGNITION

**A struck match whose flame blooms into a spiral nebula.**

One small, familiar moment — a match catching light — is caught at the exact
instant it stops being small. The flame's first breath unfurls into a
three-arm spiral galaxy: white-gold at the core, cooling through amber and
rose to violet at the rim, with embers still drifting up and to the right
along the diagonal the match itself sets. The smallest possible ignition,
opening onto the largest possible one.

## How it is drawn

`main.py` paints the whole image procedurally into a float RGB buffer —
pure Python 3 standard library, no assets, no image files:

- **Background** — a deep-space vertical gradient (near-black indigo to deep
  violet) with subtle large-scale value noise and ~500 faint stars.
- **The match** — a bold dark diagonal silhouette entering from the
  bottom-left, a tapered rotated rectangle with faint wood-grain streaks and
  a crimson-brown head, charred black on the side facing the flame.
- **The flame** — layered soft ellipses along the stick's axis (outer orange,
  gold, a near-white core) additively blended so it genuinely glows.
- **The nebula** — a 3-arm logarithmic spiral: a ribbon of soft "gas" glows
  along each arm underneath ~9,000 tiny additive dots, coloured by radius so
  the flame and the galaxy share one colour family and one bright core.
- **Finish** — drifting embers, a gentle vignette, and a whisper of grain,
  then a hand-rolled PNG encoder (`zlib` + `struct`) that picks the row
  filter which compresses smallest.

Everything is driven by one seeded random generator, so the program is
fully deterministic: run it twice, get byte-identical PNGs.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
# -> out/entry.png  (1024x1024, under 1 MiB)
```

Without `MAKEFUN_OUTPUT_DIR` it writes to `/output/entry.png`.

Entry for make.fun's **ai-excited-01** bounty ("Make the AI judge excited").
MIT licensed.
