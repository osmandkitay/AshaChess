# ASHA CHESS

A chess variant that adds one idea to chess: pieces gain extra freedom of movement, while every capture stays classical.

## ASHA CHESS: A Manifesto for a New Era

Today, the grand game of chess is suffocating. Its infinite possibilities are chained by rote memorization, its soul traded for the cold precision of scripted openings. We watch the world's greatest players, and too often, we see not human creativity, but the ghost of an AI, their moves echoing the predictability of a machine. The very essence of chess—the clash of unique minds—is fading.

It has been said that "chess is a mirror to life," and traditional chess was a perfect reflection of its time: a world of rigid hierarchies, where each piece had a strictly defined role. But our world has changed.

The modern era, born from the fires of revolution and built on the ideals of democracy and universal rights, presents us with a new paradigm. It suggests, even if only as a beautiful illusion, that all individuals possess a fundamental freedom of movement. ASHA CHESS embraces this with a postmodern touch, asking a simple yet profound question: What if every piece on the board was granted the right to move like a king?

In ASHA CHESS, we do not erase tradition; we build upon it. The "King's Step"—a single-square move in any direction—is now bestowed upon Knights, Bishops, and Rooks, while the Pawn gains a single sideways step. However, their methods of capture remain classic, tied to their unique histories. This creates a breathtaking new dynamic. A Bishop, no longer confined to a single color, can now step onto a neighboring square, reflecting a world where even the most rigid dogmas can evolve. The Pawn, once a fated foot soldier, becomes an unpredictable force, capable of both subtle repositioning and sudden threats.

Our goal is to resurrect the spirit of players like Mikhail Tal, Rashid Nezhmetdinov, and Joseph Blackburne—artists who played with character, whose moves were a signature of their very being. We should not see AI-approved lines when we look at Magnus Carlsen; we should see Magnus. Chess must be a canvas for grand strategies and profound, personal expression.

I am not a grandmaster, but a deep lover of the game, and I despise an opponent who merely recites from a book. ASHA CHESS is my proposal to restore the game's depth and dynamism. I do not claim to have uncovered its full potential; that is a journey we must take together. This is an invitation to experiment, to criticize, and to play.

For too long, the art of chess has resembled a Renaissance painting—a masterpiece, yes, but one forever bound by the fixed algorithms of perspective and form.

Together, let's usher in its next great movement.

*By Osman Derviş Kıtay [@AiDervish](https://x.com/AiDervish)*

## Game Rules

The game starts from the standard chess position. Every piece keeps all of its classical moves and captures. Some pieces gain extra moves, and **none of the extra moves can ever capture**.

| Piece  | Classical moves & captures | Extra non-capturing move |
|--------|----------------------------|--------------------------|
| King   | unchanged                  | none                     |
| Queen  | unchanged                  | none                     |
| Rook   | unchanged                  | King's Step              |
| Bishop | unchanged                  | King's Step              |
| Knight | unchanged                  | King's Step              |
| Pawn   | unchanged (incl. en passant, promotion) | one square sideways |

### King's Step (Knight, Bishop, Rook)

The piece may move one square in any direction (horizontal, vertical or diagonal) onto an **empty** square. It can never capture with this move.

- A knight on d4 of an empty board has its 8 L-jumps plus 8 King's Steps (c3, c4, c5, d3, d5, e3, e4, e5).
- A bishop on d4 can step to d3, d5, c4 or e4, so bishops can change square colour.
- A rook on d4 can step to c3, c5, e3 or e5.
- An enemy piece on an adjacent square cannot be taken by the step; it can only be captured with the piece's classical movement (e.g. a rook takes an orthogonally adjacent piece, a bishop a diagonally adjacent one, a knight never an adjacent one).

### Pawn

The pawn does **not** get the King's Step. Instead:

- It moves forward exactly as in classical chess: one square, or two squares from its starting rank when both squares are empty.
- It may additionally move **one square left or right on the same rank onto an empty square**. This sideways step never captures.
- It captures only one square diagonally forward, including en passant, and promotes on the last rank to a queen, rook, bishop or knight of the player's choice.
- It never moves backward (straight or diagonally), never moves diagonally forward without capturing, and never moves two squares sideways.

Examples: a white pawn on e4 with empty surroundings may play e5, d4 or f4 — never e3, d3, f3, d5 or f5. With a black pawn on d4 and a white knight on f4, it may only play e5.

### Everything else

- Check, checkmate, stalemate, castling, en passant and promotion work as in classical chess.
- Only classical captures attack squares. Check, pins and castling safety are therefore decided by classical attack geometry — but a King's Step or sideways pawn step may block a check or give (discovered) check. For example, the classical Fool's Mate (1. f3 e5 2. g4 Qh4) is not mate: White can block with Ng1~f2, Bf1~f2, e2~f2 or f3~g3.
- A pawn standing on its own second rank may make a two-square move, also after it stepped sideways along that rank.

### Game end and draws

Following the current FIDE Laws:

- **Automatic:** checkmate, stalemate, insufficient material, fivefold repetition, 75-move rule (checkmate on the 75th move still wins).
- **On claim by the side to move:** threefold repetition and the 50-move rule (the "Claim draw" button appears when available).
- A repeated position means the same placement, side to move, castling rights and a legal en passant capture possibility.
- The 50/75-move counters are reset by captures and forward pawn moves. A sideways pawn step is reversible, so it does **not** reset them.
- Insufficient material is declared only for K v K, K+N v K and K+B v K. The classical "bishops on the same colour" rule does not apply, because Asha bishops change colour.

### Notation

Classical moves use standard algebraic notation (`e4`, `Nf3`, `exd5`, `e8=Q`, `O-O`, `+`, `#`). Asha moves always name their origin and use a tilde, so they can never be confused with SAN: King's Step `Nb1~b2`, pawn sideways step `e4~d4`. Moves are sent to the server in UCI form (`e2e4`, promotions as `e7e8q`).

## Running the game

Requires Python 3.10+.

```
git clone https://github.com/osmandkitay/ASHA-CHESS.git
cd ASHA-CHESS
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000. `HOST`, `PORT` and `FLASK_DEBUG=1` environment variables are honoured. For deployment set `SECRET_KEY` and serve `app:app` with any WSGI server; without `SECRET_KEY` a development key is generated in `instance/secret_key`.

## Implementation

```
asha/board.py      Rules engine: position, FEN, attack geometry, move generation, push/pop, notation, perft
asha/game.py       Game: history, repetition, termination and draw claims
app.py             Flask app: JSON API and session handling only
static/js/chess.js Renders server state; no rule logic
tests/             pytest suite (movement, legality, game, perft, differential, API)
```

- `asha` is a small dependency-free engine and the single source of truth. Attack geometry (`Board.is_attacked`) is kept separate from movement geometry (`Board.legal_moves`), which adds the non-capturing King's Step and pawn sideways step.
- Every legal move carries a `kind`: `quiet`, `capture`, `en_passant`, `castling`, `kings_step` or `pawn_lateral`, plus an optional `promotion`. The UI only renders this metadata.
- The session cookie stores just the list of played moves (and a draw claim); the server replays and re-validates them on each request.
- `Board` (`legal_moves`, `push`, `pop`, `fen`, `perft`) and `Game` are independent of Flask, so an engine or self-play loop can drive them directly.

### API

| Method & path          | Body                     | Returns |
|------------------------|--------------------------|---------|
| `GET /api/state`       |                          | game state |
| `POST /api/move`       | `{"move": "e7e8q"}`      | game state, or 400 `{error, state}` |
| `POST /api/claim-draw` | `{"reason": "threefold_repetition" \| "fifty_moves"}` (optional) | game state, or 400 |
| `POST /api/reset`      |                          | fresh game state |

The game state contains `fen`, `turn`, `pieces`, `legalMoves`, `check`, `checkSquare`, `lastMove`, `history` (with notation and metadata), `gameOver`, `result`, `claimableDraws`, `halfmoveClock` and `fullmoveNumber`.

## Development

```
pip install -r requirements-dev.txt
pytest
ruff check . && ruff format --check .
mypy
```

The tests include perft regression counts for several positions (verified against an independent generator), and a differential test that compares the engine with a python-chess based Asha generator over random games. python-chess is a test-only dependency.

## License

This project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International Public License. See the LICENSE file for details.
