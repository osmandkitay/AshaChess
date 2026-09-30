# Asha Lab

Engine self-play experiments that test what the Asha manifesto promises, with
classical chess as the control. The questions and the rules for what may be
claimed are fixed in [HYPOTHESES.md](HYPOTHESES.md) before the runs.

Nothing here changes the game: the lab only reads `asha`, `app.py`,
`static/js/asha-ai.js` and the Fairy-Stockfish files in `static/vendor`.

## What it does

`selfplay.py` makes the same engine play both games under the same procedure:

1. **Opening.** For the first 8 half-moves every legal move is scored
   (MultiPV, depth 10). Moves within 30 cp of the best are *playable*; one of
   them is picked at random with a fixed seed. This makes every game
   different and measures how many good choices there are.
2. **Rest of the game.** The engine plays its best move at a fixed number of
   nodes. When that move is an Asha move, a second search restricted to the
   classical moves scores the best classical alternative.
3. **Referees.** The `asha` package referees Asha (the engine only ever
   searches the moves it allows), python-chess referees classical chess.
   Both end games the same way (lab/rules.py).

`report.py` turns a run into `report.md` and `summary.json`: results, game
shape, playable opening moves, how often Asha moves are played and how often
only an Asha move holds the position, each with a 95 % bootstrap interval, and
the pre-registered checks.

## Engine

The Fairy-Stockfish WebAssembly build the game ships (`static/vendor`), run in
Node by `engine.cjs` with the variant definition read from
`static/js/asha-ai.js`, so the lab tests the engine players meet. One thread,
16 MB hash, NNUE off (the build has no network), cleared before every search.
That makes every search, and so every game, reproducible from its seed:
rerunning a run gives the same games move for move, with any number of
workers.

## Running it

Needs Python 3.10+ with `requirements-dev.txt` installed, and Node.js.

```
python -m lab.selfplay --games 400 --nodes 20000 --seed 2 --out lab/runs/main
python -m lab.report lab/runs/main
pytest lab/tests
```

A run can be stopped and restarted with the same command; finished games are
kept in `games.jsonl`. `run.json` records the settings, engine, variant,
commit and platform.

One game per line in `games.jsonl`: the moves (UCI and notation), their kind,
moving piece, capture and check flags, game phase, engine score and depth, the
opening MultiPV scores, the classical alternatives to Asha moves, and the
result.

## Limits

Read the *Limitations* section of every report. In short: these are engine
games at one stated strength, not human games; the engine's centipawns are
its own estimate in each game; and Fairy-Stockfish's model of Asha has two
known gaps below the root (the double step and en passant, see
`static/js/asha-ai.js`).
