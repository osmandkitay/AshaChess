# Asha Lab: hypotheses, fixed before the main run

This file is committed before the main run starts, so the questions, the
predictions and the rules for what we may claim cannot be adjusted to fit the
results. If they change later, the change is a new commit with the reason.

The Asha manifesto makes three promises: memorisation matters less, the game
is really different (not only in the opening), and it gives dynamic, fighting
games. Each hypothesis below turns one of them into a number the engine
self-play can measure, with classical chess, played by the same engine under
the same procedure, as the control.

## Runs

| Run | Games per variant | Nodes per move | Seed | Purpose |
|---|---|---|---|---|
| pilot | 20 | 20,000 | 1 | timing and bug hunting only; excluded from every claim |
| `main` | 400 | 20,000 | 2 | the numbers we report |
| `deep` | 100 | 100,000 | 3 | robustness: does the picture hold for a stronger engine? |

All other settings are the defaults in `lab/selfplay.py`: 8 sampled opening
half-moves, depth-10 MultiPV, 30 cp margin, 600-half-move cap, 16 MB hash.

## Hypotheses

Primary (the claims we want to be able to make):

- **H1: more good choices in the opening.** Over the sampled opening plies 2–8,
  the average number of playable moves (within 30 cp of the best) is higher in
  Asha than in classical chess. The same holds at 15 cp and 50 cp.
  *Prediction:* yes, at least twice as many.
- **H2: different in every phase.** Asha moves (King's Step, pawn sideways
  or diagonal step) are at least 10 % of the moves played in the middlegame
  and at least 10 % in the endgame.
  *Prediction:* yes in both; the endgame share is higher than the middlegame
  share.
- **H3: moments only Asha allows.** At least 1 in 100 engine moves is an
  *Asha moment* (the best classical alternative is at least 200 cp worse in a
  position not yet decided; see `lab/report.py`), and at least a quarter of
  the games contain one.
  *Prediction:* yes for the rate; unsure about the quarter.

Secondary (no direction is assumed; we report whatever comes out):

- **H4: decisive games.** Is the share of decisive games different? The
  extra moves never capture but can block checks and escape threats, so
  they may help the defender more than the attacker.
  *Prediction:* slightly fewer decisive games in Asha than in classical
  chess (low confidence).
- **H5: balance.** White's score in Asha lies between 45 % and 60 %.
  *Prediction:* yes.
- **H6: game shape.** Differences in game length, checks per game, captures
  per game and the move of the first capture. No prediction.

## What we will and will not say

- A claim goes public only if the 95 % interval of the relevant number (or of
  the Asha-minus-classical difference) supports it in `main` **and** the
  estimate points the same way in `deep`.
- If a prediction fails, we say so. A failed H4 prediction in either
  direction is a finding, not a problem.
- We describe these as results of engine self-play at a stated strength, not
  as facts about human games.
- We do not report numbers from the pilot, and we do not add a metric after
  seeing the results without saying so explicitly in the report.
- Seven hypotheses are tested; one of them may look significant by chance.
  H1–H3 are the ones we base public claims on.

## Amendment 1 (2026-09-30, after the pilot, before any result of `main` was seen)

In the pilot, re-searching the flagged Asha moments with ten times the nodes
(`lab/moments.py`) kept only about half of them; the rest were noise of the
small first-pass searches. So:

- H3 is checked twice: as written above (first pass), and with the moments
  confirmed by `lab/moments.py` at ten times the run's nodes.
- Public claims about Asha moments use only the confirmed numbers, which are
  the lower of the two. The same thresholds apply (1 per 100 engine moves,
  a quarter of the games).
