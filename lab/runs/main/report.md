# Asha Lab report: `main`

Engine: Fairy-Stockfish [commit: b2e693ef, upstream: , emscripten: 2.0.26] LB, 1 thread, 16 MB hash, NNUE off (the build has no network). Each search starts from a cleared engine.

Opening: the first 8 half-moves are chosen at random among the *playable* moves (within 30 cp of the best at depth 10, MultiPV over all legal moves). Then 20,000 nodes per move. Seed 2. Commit `ca6cae9`.

Values are shown as estimate [95 % bootstrap interval over games].

## Games

| | asha | chess |
|---|---|---|
| Games analysed | 400 | 400 |
| Games with an error (excluded) | 0 | 0 |
| White wins | 39.8 % [35.0 %, 44.5 %] | 39.0 % [34.2 %, 43.8 %] |
| Draws | 13.0 % [9.8 %, 16.2 %] | 25.0 % [20.8 %, 29.2 %] |
| Black wins | 47.2 % [42.5 %, 52.0 %] | 36.0 % [31.5 %, 40.8 %] |
| White score | 46.2 % [41.8 %, 50.6 %] | 51.5 % [47.1 %, 55.6 %] |
| Decisive games | 87.0 % [83.8 %, 90.2 %] | 75.0 % [70.8 %, 79.2 %] |
| Game length (half-moves) | 122.82 [118.71, 127.17] | 151.56 [146.65, 156.72] |
| Captures per game | 23.52 [23.01, 24.00] | 26.10 [25.76, 26.43] |
| Checks per game | 15.16 [14.16, 16.33] | 14.02 [13.20, 14.91] |
| Move of the first capture | 8.35 [8.06, 8.65] | 6.11 [5.79, 6.41] |
| Median game length (half-moves) | 118 | 139 |
| Median search depth per engine move | 10 | 10 |

### Asha minus classical

| | difference |
|---|---|
| White wins | +0.8 pp [-6.0 pp, +7.8 pp] |
| Draws | -12.0 pp [-17.2 pp, -6.7 pp] |
| Black wins | +11.2 pp [+4.5 pp, +17.8 pp] |
| White score | -5.2 pp [-11.4 pp, +0.9 pp] |
| Decisive games | +12.0 pp [+6.8 pp, +17.2 pp] |
| Game length (half-moves) | -28.74 [-35.24, -22.30] |
| Captures per game | -2.57 [-3.20, -1.98] |
| Checks per game | +1.14 [-0.18, +2.55] |
| Move of the first capture | +2.24 [+1.80, +2.67] |

### How games ended

| | asha | chess |
|---|---|---|
| checkmate | 348 | 300 |
| threefold_repetition | 40 | 23 |
| insufficient_material | 11 | 51 |
| fifty_moves | 1 | 23 |
| stalemate | 0 | 3 |

## Opening: how many good choices

A move is *playable* if its depth-10 score is within the margin of the best move's. Ply 1 is the start position, the same in every game.

**Margin 15 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 3 | 20.0 | 3 |
| 2 | 34.0 | 6.18 [5.92, 6.43] | 20.0 | 1.25 [1.21, 1.29] |
| 3 | 40.5 | 4.11 [3.88, 4.34] | 25.3 | 2.60 [2.48, 2.73] |
| 4 | 40.7 | 4.03 [3.77, 4.28] | 25.9 | 2.07 [1.98, 2.17] |
| 5 | 47.1 | 3.34 [3.12, 3.56] | 29.1 | 2.44 [2.33, 2.56] |
| 6 | 46.9 | 3.25 [3.02, 3.49] | 29.0 | 2.25 [2.10, 2.38] |
| 7 | 52.4 | 3.02 [2.79, 3.26] | 30.9 | 2.22 [2.08, 2.36] |
| 8 | 51.6 | 2.86 [2.65, 3.08] | 31.0 | 2.11 [1.98, 2.25] |

**Margin 30 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 8 | 20.0 | 4 |
| 2 | 34.0 | 11.58 [11.27, 11.91] | 20.0 | 3.23 [3.12, 3.34] |
| 3 | 40.5 | 8.79 [8.32, 9.26] | 25.3 | 4.17 [3.98, 4.37] |
| 4 | 40.7 | 7.82 [7.42, 8.21] | 25.9 | 3.33 [3.18, 3.48] |
| 5 | 47.1 | 6.89 [6.46, 7.32] | 29.1 | 3.91 [3.73, 4.08] |
| 6 | 46.9 | 6.61 [6.19, 7.02] | 29.0 | 3.58 [3.35, 3.81] |
| 7 | 52.4 | 6.25 [5.80, 6.72] | 30.9 | 3.53 [3.29, 3.77] |
| 8 | 51.6 | 5.70 [5.25, 6.13] | 31.0 | 3.33 [3.10, 3.56] |

**Margin 50 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 20 | 20.0 | 6 |
| 2 | 34.0 | 18.35 [17.85, 18.84] | 20.0 | 5.17 [5.03, 5.33] |
| 3 | 40.5 | 15.56 [14.90, 16.21] | 25.3 | 6.20 [5.87, 6.54] |
| 4 | 40.7 | 14.09 [13.55, 14.62] | 25.9 | 5.21 [4.98, 5.45] |
| 5 | 47.1 | 13.43 [12.75, 14.10] | 29.1 | 6.34 [6.00, 6.71] |
| 6 | 46.9 | 12.11 [11.48, 12.74] | 29.0 | 5.56 [5.24, 5.89] |
| 7 | 52.4 | 12.14 [11.31, 12.92] | 30.9 | 5.67 [5.30, 6.02] |
| 8 | 51.6 | 10.49 [9.74, 11.17] | 31.0 | 5.38 [5.01, 5.75] |

**Playable moves per position, plies 2–8**

| Margin | asha | chess | Asha ÷ classical |
|---|---|---|---|
| 15 cp | 3.83 [3.72, 3.93] | 2.13 [2.08, 2.18] | 1.79 [1.73, 1.86] |
| 30 cp | 7.66 [7.46, 7.86] | 3.58 [3.50, 3.67] | 2.14 [2.06, 2.22] |
| 50 cp | 13.74 [13.39, 14.09] | 5.65 [5.50, 5.81] | 2.43 [2.34, 2.52] |

**Distinct openings** (margin 30 cp, the one used to choose moves)

| | asha | chess |
|---|---|---|
| Different openings among the games | 400 / 400 | 365 / 400 |
| Playable 8-half-move openings (Knuth estimate) | 2.26e+07 [1.52e+07, 3.11e+07] | 4.02e+04 [3.2e+04, 5.08e+04] |

The Knuth estimate is the average, over the sampled games, of the product of the number of playable moves at each opening ply. Because each move was drawn uniformly from the playable ones, it is an unbiased estimate of the number of distinct openings made only of playable moves (Knuth, 1975). Its interval is wide because the products are heavy-tailed.

Share of the playable opening moves that are Asha moves: 26.9 % [26.4 %, 27.4 %]

## Asha moves in play

Share of all moves played that are Asha moves (King's Step, pawn sideways or diagonal step):

| Phase | share |
|---|---|
| All moves | 28.1 % [27.4 %, 28.7 %] |
| Engine moves (after the sampled opening) | 28.2 % [27.5 %, 28.8 %] |
| Opening | 30.8 % [29.8 %, 31.9 %] |
| Middlegame | 29.0 % [28.2 %, 29.8 %] |
| Endgame | 26.6 % [25.6 %, 27.6 %] |
| Replies to check | 7.5 % [6.8 %, 8.3 %] |

| Asha move type | share of all moves |
|---|---|
| Knight King's Step | 5.4 % [5.0 %, 5.8 %] |
| Bishop King's Step | 3.2 % [3.0 %, 3.4 %] |
| Rook King's Step | 2.5 % [2.2 %, 2.7 %] |
| Pawn sideways step | 5.9 % [5.6 %, 6.1 %] |
| Pawn diagonal step | 11.2 % [10.8 %, 11.6 %] |

### When only an Asha move will do

For every engine move that was an Asha move, a second search of the same size, restricted to the classical moves, scored the best classical alternative. Both scores come from separate searches at 20,000 nodes, so small gaps are noise; the thresholds are deliberately large.

| | per 100 engine moves | games with at least one |
|---|---|---|
| Best classical move ≥ 100 cp worse | 6.58 [6.25, 6.90] | |
| Best classical move ≥ 200 cp worse | 3.34 [3.13, 3.55] | |
| Asha moment (≥ 200 cp, position not already decided) | 1.57 [1.42, 1.72] | 74.2 % [69.8 %, 78.5 %] |

**Re-checked at 200,000 nodes** (lab/moments.py)

Of 720 flagged moments, 337 (47 %) were confirmed by the bigger search; 206 of those have a single best move (at least 150 cp ahead of the second best) and make puzzles. Unflagged positions were not re-searched, so these counts can only undercount.

| | per 100 engine moves | games with at least one |
|---|---|---|
| Confirmed Asha moment | 0.73 [0.64, 0.84] | 50.7 % [45.8 %, 55.8 %] |

| Confirmed moments by theme | count |
|---|---|
| saves | 151 |
| wins | 96 |
| keeps the balance | 85 |
| gives check | 83 |
| answers check | 36 |
| mates | 5 |
| move: kings_step (N) | 99 |
| move: pawn_diagonal | 96 |
| move: pawn_lateral | 50 |
| move: kings_step (B) | 49 |
| move: kings_step (R) | 43 |

## Pre-registered checks

The hypotheses and rules are in lab/HYPOTHESES.md. *Supported* means the 95 % interval meets the condition in this run; a public claim also needs the other run to point the same way.

| | condition | this run | verdict |
|---|---|---|---|
| H1 (15 cp) | Asha ÷ classical playable moves > 1 | 1.79 [1.73, 1.86] | supported |
| H1 (30 cp) | Asha ÷ classical playable moves > 1 | 2.14 [2.06, 2.22] | supported |
| H1 (50 cp) | Asha ÷ classical playable moves > 1 | 2.43 [2.34, 2.52] | supported |
| H2 (middlegame) | Asha share of moves ≥ 10 % | 29.0 % [28.2 %, 29.8 %] | supported |
| H2 (endgame) | Asha share of moves ≥ 10 % | 26.6 % [25.6 %, 27.6 %] | supported |
| H3 (rate) | Asha moments ≥ 1 per 100 engine moves | 1.57 [1.42, 1.72] | supported |
| H3 (games) | games with an Asha moment ≥ 25 % | 74.2 % [69.8 %, 78.5 %] | supported |
| H3 (rate, confirmed) | confirmed moments ≥ 1 per 100 engine moves | 0.73 [0.64, 0.84] | contradicted |
| H3 (games, confirmed) | games with a confirmed moment ≥ 25 % | 50.7 % [45.8 %, 55.8 %] | supported |
| H4 | decisive games, Asha − classical (two-sided) | +12.0 pp [+6.8 pp, +17.2 pp] | more decisive |
| H5 | White score in Asha within 45–60 % | 46.2 % [41.8 %, 50.6 %] | not supported |

## Limitations

- These are engine games. They show what the rules allow and reward at one engine strength, not what people will enjoy.
- The engine uses its classical evaluation in both games. That evaluation was tuned for classical chess and its piece values for Asha's pieces are its own estimates, so a centipawn is not necessarily worth the same in both games (the opening tables therefore show three margins), and how often the engine chooses a kind of Asha move partly reflects its evaluation, not only the position.
- Fairy-Stockfish's Asha model differs from the rules in two known ways (it grants the double step by square rather than by whether the pawn has moved, and it does not see en passant); the root is restricted to Asha's legal moves, but the search below the root can be slightly off.
- Both games get the same number of nodes per move, not the same depth: Asha has more moves per position, and the median depth row shows what the budget reached in each game.
- Insufficient material is judged by each game's own rules: python-chess also recognises classical dead positions such as bishops of the same colour, which Asha does not have.

