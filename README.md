# ASHA CHESS

A chess variant that adds one idea to chess: pieces gain extra freedom of movement, while every capture stays classical.

## ASHA CHESS: A Manifesto for a New Era

Today, the grand game of chess is suffocating. Its infinite possibilities are chained by rote memorization, its soul traded for the cold precision of scripted openings. We watch the world's greatest players, and too often, we see not human creativity, but the ghost of an AI, their moves echoing the predictability of a machine. The very essence of chess—the clash of unique minds—is fading.

It has been said that "chess is a mirror to life," and traditional chess was a perfect reflection of its time: a world of rigid hierarchies, where each piece had a strictly defined role. But our world has changed.

The modern era, born from the fires of revolution and built on the ideals of democracy and universal rights, presents us with a new paradigm. It suggests, even if only as a beautiful illusion, that all individuals possess a fundamental freedom of movement. ASHA CHESS embraces this with a postmodern touch, asking a simple yet profound question: What if every piece on the board was granted the right to move like a king?

In ASHA CHESS, we do not erase tradition; we build upon it. The "King's Step"—a single-square move in any direction—is now bestowed upon Knights, Bishops, and Rooks, while the Pawn gains a single step sideways or diagonally forward. However, their methods of capture remain classic, tied to their unique histories. This creates a breathtaking new dynamic. A Bishop, no longer confined to a single color, can now step onto a neighboring square, reflecting a world where even the most rigid dogmas can evolve. The Pawn, once a fated foot soldier, becomes an unpredictable force, capable of both subtle repositioning and sudden threats.

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
| Pawn   | unchanged (incl. double step, en passant, promotion) | one square sideways or diagonally forward |

### King's Step (Knight, Bishop, Rook)

The piece may move one square in any direction (horizontal, vertical or diagonal) onto an **empty** square. It can never capture with this move.

- A knight on d4 of an empty board has its 8 L-jumps plus 8 King's Steps (c3, c4, c5, d3, d5, e3, e4, e5).
- A bishop on d4 can step to d3, d5, c4 or e4, so bishops can change square colour.
- A rook on d4 can step to c3, c5, e3 or e5.
- An enemy piece on an adjacent square cannot be taken by the step; it can only be captured with the piece's classical movement (e.g. a rook takes an orthogonally adjacent piece, a bishop a diagonally adjacent one, a knight never an adjacent one).

### Pawn

The pawn does **not** get the King's Step. Instead:

- It moves forward exactly as in classical chess: one square, or two squares if it has **never moved** and both squares are empty.
- It may additionally move **one square left or right on the same rank**, or **one square diagonally forward (left or right)**, onto an **empty** square. These steps never capture.
- Sideways and diagonal steps are real pawn moves: the pawn loses its two-square move for good, even if it later returns to its original square. A pawn that played e2~d2 may play d3 but never d4, and after d2~e2 it cannot play e4 either.
- It captures exactly as in classical chess: only one square diagonally forward, including en passant, never straight ahead or sideways. A diagonal move onto an enemy piece is a capture; onto the en passant square it is the en passant capture. It promotes on the last rank — by a straight move, a capture or a diagonal step — to a queen, rook, bishop or knight of the player's choice.
- It never moves backward (straight or diagonally) and never moves more than one square sideways or diagonally.

Examples: a white pawn on e4 with d5, e5, f5, d4 and f4 empty may move to any of them — never to e3, d3 or f3. With black pieces on d5 and f5 it captures them classically. With a black pawn on d4 and a white knight on f4 it may play e5, e4~d5 or e4~f5. Black moves the same way towards rank 1.

Because of the diagonal steps the start position has **34** legal moves instead of classical chess's 20: the 20 classical moves plus 14 diagonal pawn steps onto the third rank (and likewise for Black).

### Everything else

- Check, checkmate, stalemate, castling, en passant and promotion work as in classical chess.
- Only classical captures attack squares. Check, pins and castling safety are therefore decided by classical attack geometry — but a King's Step or a sideways or diagonal pawn step may block a check or give (discovered) check. For example, the classical Fool's Mate (1. f3 e5 2. g4 Qh4) is not mate: White can block with Ng1~f2, Bf1~f2, e2~f2, f3~g3 or h2~g3.

### Game end and draws

Following the current FIDE Laws:

- **Automatic:** checkmate, stalemate, insufficient material, fivefold repetition, 75-move rule (checkmate on the 75th move still wins).
- **On claim by the side to move:** threefold repetition and the 50-move rule (the "Claim draw" button appears when available).
- A repeated position means the same placement, side to move, castling rights, legal en passant capture possibility and the same set of pawns that still have their two-square move.
- The 50/75-move counters are reset by every capture and every pawn move, sideways and diagonal steps included.
- Insufficient material is declared only for K v K, K+N v K and K+B v K. The classical "bishops on the same colour" rule does not apply, because Asha bishops change colour.

### Notation

Classical moves use standard algebraic notation (`e4`, `Nf3`, `exd5`, `e8=Q`, `O-O`, `+`, `#`). Asha moves always name their origin and use a tilde, so they can never be confused with SAN: King's Step `Nb1~b2`, pawn sideways step `e4~d4`, pawn diagonal step `e4~d5` (`e7~f8=Q` when it promotes). Moves are sent to the server in UCI form (`e2e4`, promotions as `e7e8q`).

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

Then open http://127.0.0.1:5000. `HOST`, `PORT` and `FLASK_DEBUG=1` environment variables are honoured. `run.py` is for local development only; without `SECRET_KEY` a development key is generated in `instance/secret_key`.

## Deployment (Render)

Web Service, Python runtime (version from `.python-version`):

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app` (binds to Render's `PORT` automatically)
- Environment: set `SECRET_KEY` to a long random value
- Health Check Path: `/`

## Implementation

```
asha/board.py      Rules engine: position, FEN, attack geometry, move generation, push/pop, notation, perft
asha/game.py       Game: history, repetition, termination and draw claims
app.py             Flask app: JSON API and session handling only
static/js/chess.js Renders server state; no rule logic
tests/             pytest suite (movement, legality, game, perft, differential, API)
```

- `asha` is a small dependency-free engine and the single source of truth. Attack geometry (`Board.is_attacked`) is kept separate from movement geometry (`Board.legal_moves`), which adds the non-capturing King's Step and the pawn's sideways and diagonal steps.
- Every legal move carries a `kind`: `quiet`, `capture`, `en_passant`, `castling`, `kings_step`, `pawn_lateral` or `pawn_diagonal`, plus an optional `promotion`. The UI only renders this metadata.
- Which pawns still have their two-square move (`Board.virgin`) is part of the position, used by move generation, repetition and FEN. FEN gets an optional seventh field listing those pawns' files (uppercase White, lowercase Black, `-` for none), e.g. `... w KQkq - 0 3 ABCFGHabcdefgh`. It is omitted when every pawn on its starting rank still has the right, so ordinary positions stay standard FEN.
- The session cookie stores just the list of played moves (and a draw claim); the server replays and re-validates them on each request. Known limit: a browser cookie holds roughly 4 KB, i.e. several hundred plies; longer games would need server-side storage.
- `Board` (`legal_moves`, `push`, `pop`, `fen`, `perft`) and `Game` are independent of Flask, so an engine or self-play loop can drive them directly.

### API

| Method & path          | Body                     | Returns |
|------------------------|--------------------------|---------|
| `GET /api/state`       |                          | game state |
| `POST /api/move`       | `{"move": "e7e8q"}`      | game state, or 400 `{error, state}` |
| `POST /api/claim-draw` | `{"reason": "threefold_repetition" \| "fifty_moves"}` (optional) | game state, or 400 |
| `POST /api/reset`      |                          | fresh game state |

The game state contains `fen` (with the optional seventh field above), `turn`, `pieces`, `legalMoves`, `check`, `checkSquare`, `lastMove`, `history` (with notation and metadata), `gameOver`, `result`, `claimableDraws`, `halfmoveClock` and `fullmoveNumber`.

## Development

```
pip install -r requirements-dev.txt
pytest
ruff check . && ruff format --check .
mypy
```

GitHub Actions runs the same four checks on every push and pull request.

The tests include perft regression counts for several positions (verified against an independent generator), and a differential test that compares the engine with a python-chess based Asha generator over random games. python-chess is a test-only dependency.

## License

This project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International Public License. See the LICENSE file for details.
