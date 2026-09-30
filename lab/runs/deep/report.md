# Asha Lab report: `deep`

Engine: Fairy-Stockfish [commit: b2e693ef, upstream: , emscripten: 2.0.26] LB, 1 thread, 16 MB hash, NNUE off (the build has no network). Each search starts from a cleared engine.

Opening: the first 8 half-moves are chosen at random among the *playable* moves (within 30 cp of the best at depth 10, MultiPV over all legal moves). Then 100,000 nodes per move. Seed 3. Commit `aa51de4`.

Values are shown as estimate [95 % bootstrap interval over games].

## Games

| | asha | chess |
|---|---|---|
| Games analysed | 100 | 100 |
| Games with an error (excluded) | 0 | 0 |
| White wins | 43.0 % [33.0 %, 53.0 %] | 20.0 % [13.0 %, 28.0 %] |
| Draws | 15.0 % [8.0 %, 22.0 %] | 55.0 % [45.0 %, 65.0 %] |
| Black wins | 42.0 % [32.0 %, 51.0 %] | 25.0 % [17.0 %, 34.0 %] |
| White score | 50.5 % [42.0 %, 59.5 %] | 47.5 % [41.0 %, 54.0 %] |
| Decisive games | 85.0 % [78.0 %, 92.0 %] | 45.0 % [35.0 %, 55.0 %] |
| Game length (half-moves) | 120.63 [114.02, 127.21] | 172.72 [159.20, 185.86] |
| Captures per game | 24.50 [23.56, 25.30] | 26.56 [25.83, 27.24] |
| Checks per game | 13.46 [12.16, 14.82] | 14.40 [12.38, 16.47] |
| Move of the first capture | 8.50 [7.95, 9.07] | 5.73 [5.23, 6.27] |
| Median game length (half-moves) | 121 | 157.5 |
| Median search depth per engine move | 12 | 13 |

### Asha minus classical

| | difference |
|---|---|
| White wins | +23.0 pp [+10.0 pp, +36.0 pp] |
| Draws | -40.0 pp [-52.0 pp, -28.0 pp] |
| Black wins | +17.0 pp [+4.0 pp, +29.0 pp] |
| White score | +3.0 pp [-8.0 pp, +14.5 pp] |
| Decisive games | +40.0 pp [+28.0 pp, +52.0 pp] |
| Game length (half-moves) | -52.09 [-66.93, -37.41] |
| Captures per game | -2.06 [-3.15, -1.00] |
| Checks per game | -0.94 [-3.43, +1.51] |
| Move of the first capture | +2.77 [+2.02, +3.56] |

### How games ended

| | asha | chess |
|---|---|---|
| checkmate | 85 | 45 |
| insufficient_material | 3 | 27 |
| threefold_repetition | 12 | 17 |
| fifty_moves | 0 | 9 |
| stalemate | 0 | 2 |

## Opening: how many good choices

A move is *playable* if its depth-10 score is within the margin of the best move's. Ply 1 is the start position, the same in every game.

**Margin 15 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 3 | 20.0 | 3 |
| 2 | 34.0 | 6.23 [5.72, 6.78] | 20.0 | 1.17 [1.10, 1.24] |
| 3 | 40.4 | 3.86 [3.46, 4.28] | 24.3 | 2.42 [2.20, 2.65] |
| 4 | 41.4 | 3.41 [2.95, 3.94] | 26.6 | 2.06 [1.86, 2.26] |
| 5 | 47.0 | 3.33 [2.88, 3.81] | 28.2 | 2.65 [2.46, 2.85] |
| 6 | 47.3 | 3.48 [2.95, 4.05] | 29.6 | 2.38 [2.09, 2.71] |
| 7 | 52.4 | 2.93 [2.53, 3.37] | 30.6 | 1.96 [1.74, 2.19] |
| 8 | 51.8 | 3.06 [2.64, 3.51] | 31.7 | 2.07 [1.83, 2.34] |

**Margin 30 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 8 | 20.0 | 4 |
| 2 | 34.0 | 11.68 [11.05, 12.29] | 20.0 | 3.05 [2.86, 3.24] |
| 3 | 40.4 | 8.41 [7.63, 9.22] | 24.3 | 3.94 [3.55, 4.34] |
| 4 | 41.4 | 7.25 [6.52, 8.03] | 26.6 | 3.35 [3.06, 3.65] |
| 5 | 47.0 | 6.48 [5.70, 7.34] | 28.2 | 3.97 [3.60, 4.36] |
| 6 | 47.3 | 7.31 [6.33, 8.33] | 29.6 | 3.57 [3.13, 4.05] |
| 7 | 52.4 | 6.25 [5.44, 7.14] | 30.6 | 3.26 [2.86, 3.70] |
| 8 | 51.8 | 5.99 [5.17, 6.85] | 31.7 | 3.16 [2.76, 3.59] |

**Margin 50 cp**

| Ply | asha legal | asha playable | chess legal | chess playable |
|---|---|---|---|---|
| 1 | 34.0 | 20 | 20.0 | 6 |
| 2 | 34.0 | 18.49 [17.49, 19.53] | 20.0 | 5.31 [5.05, 5.56] |
| 3 | 40.4 | 14.55 [13.40, 15.72] | 24.3 | 5.93 [5.26, 6.63] |
| 4 | 41.4 | 12.96 [11.78, 14.13] | 26.6 | 5.14 [4.65, 5.68] |
| 5 | 47.0 | 12.23 [10.96, 13.59] | 28.2 | 6.23 [5.52, 6.98] |
| 6 | 47.3 | 12.81 [11.42, 14.27] | 29.6 | 5.52 [4.83, 6.23] |
| 7 | 52.4 | 11.58 [10.10, 13.12] | 30.6 | 5.22 [4.60, 5.87] |
| 8 | 51.8 | 10.83 [9.35, 12.35] | 31.7 | 4.92 [4.27, 5.61] |

**Playable moves per position, plies 2–8**

| Margin | asha | chess | Asha ÷ classical |
|---|---|---|---|
| 15 cp | 3.76 [3.57, 3.95] | 2.10 [2.01, 2.19] | 1.79 [1.68, 1.91] |
| 30 cp | 7.62 [7.21, 8.03] | 3.47 [3.30, 3.64] | 2.20 [2.05, 2.36] |
| 50 cp | 13.35 [12.63, 14.05] | 5.47 [5.15, 5.80] | 2.44 [2.27, 2.64] |

**Distinct openings** (margin 30 cp, the one used to choose moves)

| | asha | chess |
|---|---|---|
| Different openings among the games | 100 / 100 | 98 / 100 |
| Playable 8-half-move openings (Knuth estimate) | 1.82e+07 [1.13e+07, 2.66e+07] | 3.14e+04 [2.08e+04, 4.38e+04] |

The Knuth estimate is the average, over the sampled games, of the product of the number of playable moves at each opening ply. Because each move was drawn uniformly from the playable ones, it is an unbiased estimate of the number of distinct openings made only of playable moves (Knuth, 1975). Its interval is wide because the products are heavy-tailed.

Share of the playable opening moves that are Asha moves: 26.7 % [25.5 %, 27.8 %]

## Asha moves in play

Share of all moves played that are Asha moves (King's Step, pawn sideways or diagonal step):

| Phase | share |
|---|---|
| All moves | 28.1 % [27.0 %, 29.2 %] |
| Engine moves (after the sampled opening) | 28.0 % [26.9 %, 29.2 %] |
| Opening | 29.0 % [26.8 %, 31.2 %] |
| Middlegame | 28.0 % [26.5 %, 29.6 %] |
| Endgame | 27.8 % [26.1 %, 29.5 %] |
| Replies to check | 8.7 % [7.1 %, 10.5 %] |

| Asha move type | share of all moves |
|---|---|
| Knight King's Step | 4.8 % [4.2 %, 5.5 %] |
| Bishop King's Step | 3.4 % [3.0 %, 3.9 %] |
| Rook King's Step | 2.0 % [1.6 %, 2.4 %] |
| Pawn sideways step | 5.7 % [5.2 %, 6.2 %] |
| Pawn diagonal step | 12.1 % [11.4 %, 12.8 %] |

### When only an Asha move will do

For every engine move that was an Asha move, a second search of the same size, restricted to the classical moves, scored the best classical alternative. Both scores come from separate searches at 100,000 nodes, so small gaps are noise; the thresholds are deliberately large.

| | per 100 engine moves | games with at least one |
|---|---|---|
| Best classical move ≥ 100 cp worse | 4.95 [4.48, 5.44] | |
| Best classical move ≥ 200 cp worse | 2.56 [2.25, 2.89] | |
| Asha moment (≥ 200 cp, position not already decided) | 1.20 [0.98, 1.46] | 73.0 % [64.0 %, 81.0 %] |

**Re-checked at 1,000,000 nodes** (lab/moments.py)

Of 135 flagged moments, 82 (61 %) were confirmed by the bigger search; 51 of those have a single best move (at least 150 cp ahead of the second best) and make puzzles. Unflagged positions were not re-searched, so these counts can only undercount.

| | per 100 engine moves | games with at least one |
|---|---|---|
| Confirmed Asha moment | 0.73 [0.53, 0.99] | 48.0 % [38.0 %, 58.0 %] |

| Confirmed moments by theme | count |
|---|---|
| saves | 42 |
| gives check | 26 |
| wins | 20 |
| keeps the balance | 20 |
| answers check | 13 |
| move: kings_step (N) | 23 |
| move: pawn_diagonal | 19 |
| move: kings_step (B) | 17 |
| move: pawn_lateral | 13 |
| move: kings_step (R) | 10 |

## Pre-registered checks

The hypotheses and rules are in lab/HYPOTHESES.md. *Supported* means the 95 % interval meets the condition in this run; a public claim also needs the other run to point the same way.

| | condition | this run | verdict |
|---|---|---|---|
| H1 (15 cp) | Asha ÷ classical playable moves > 1 | 1.79 [1.68, 1.91] | supported |
| H1 (30 cp) | Asha ÷ classical playable moves > 1 | 2.20 [2.05, 2.36] | supported |
| H1 (50 cp) | Asha ÷ classical playable moves > 1 | 2.44 [2.27, 2.64] | supported |
| H2 (middlegame) | Asha share of moves ≥ 10 % | 28.0 % [26.5 %, 29.6 %] | supported |
| H2 (endgame) | Asha share of moves ≥ 10 % | 27.8 % [26.1 %, 29.5 %] | supported |
| H3 (rate) | Asha moments ≥ 1 per 100 engine moves | 1.20 [0.98, 1.46] | not supported |
| H3 (games) | games with an Asha moment ≥ 25 % | 73.0 % [64.0 %, 81.0 %] | supported |
| H3 (rate, confirmed) | confirmed moments ≥ 1 per 100 engine moves | 0.73 [0.53, 0.99] | contradicted |
| H3 (games, confirmed) | games with a confirmed moment ≥ 25 % | 48.0 % [38.0 %, 58.0 %] | supported |
| H4 | decisive games, Asha − classical (two-sided) | +40.0 pp [+28.0 pp, +52.0 pp] | more decisive |
| H5 | White score in Asha within 45–60 % | 50.5 % [42.0 %, 59.5 %] | not supported |

## Limitations

- These are engine games. They show what the rules allow and reward at one engine strength, not what people will enjoy.
- The engine uses its classical evaluation in both games. That evaluation was tuned for classical chess and its piece values for Asha's pieces are its own estimates, so a centipawn is not necessarily worth the same in both games (the opening tables therefore show three margins), and how often the engine chooses a kind of Asha move partly reflects its evaluation, not only the position.
- Fairy-Stockfish's Asha model differs from the rules in two known ways (it grants the double step by square rather than by whether the pawn has moved, and it does not see en passant); the root is restricted to Asha's legal moves, but the search below the root can be slightly off.
- Both games get the same number of nodes per move, not the same depth: Asha has more moves per position, and the median depth row shows what the budget reached in each game.
- Insufficient material is judged by each game's own rules: python-chess also recognises classical dead positions such as bishops of the same colour, which Asha does not have.

