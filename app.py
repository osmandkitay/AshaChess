"""Flask front end for Asha Chess.

All rules live in the ``asha`` package. The session stores only the list of
played moves (and a draw claim, if any); the game is rebuilt and re-validated
from it on every request.
"""

from __future__ import annotations

import os
import secrets

from flask import Flask, jsonify, render_template, request, session

from asha import Game, GameOverError, IllegalMoveError, Move, PlayedMove, square_name


def _secret_key(app: Flask) -> str:
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    # Development fallback: a random key persisted in the instance folder so
    # sessions survive restarts and are shared by all worker processes.
    path = os.path.join(app.instance_path, "secret_key")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        os.makedirs(app.instance_path, exist_ok=True)
        key = secrets.token_hex(32)
        with open(path, "w", encoding="utf-8") as f:
            f.write(key)
        return key


def _move_json(move: Move) -> dict:
    return {
        "uci": move.uci(),
        "from": square_name(move.from_sq),
        "to": square_name(move.to_sq),
        "kind": move.kind,
        "capture": move.is_capture,
        "promotion": move.promotion,
    }


def _played_json(ply: int, played: PlayedMove) -> dict:
    return {
        **_move_json(played.move),
        "ply": ply,
        "color": played.color,
        "piece": played.piece,
        "captured": played.captured,
        "notation": played.notation,
        "check": played.check,
        "checkmate": played.checkmate,
    }


def engine_position(game: Game) -> dict:
    """Where a browser engine should start: the position after the last pawn
    move or capture, plus the piece moves since.

    Fairy-Stockfish cannot replay every Asha move faithfully (it reads a pawn's
    diagonal step onto the en passant square as a non-capture), but it does
    replay piece moves, and those still let it see repetitions. The FEN is the
    standard six fields: the engine cannot read the double-step field.
    """
    board = game.board
    undone = [board.pop() for _ in range(min(board.halfmove_clock, len(game.history)))]
    fen = board.fen()
    for move in reversed(undone):
        board.push(move)
    return {"fen": " ".join(fen.split()[:6]), "moves": [move.uci() for move in reversed(undone)]}


def game_state(game: Game) -> dict:
    board = game.board
    outcome = game.outcome()
    history = [_played_json(i + 1, played) for i, played in enumerate(game.history)]
    checked = board.checked_king()
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == "w" else "black",
        "pieces": {square_name(sq): p for sq, p in enumerate(board.squares) if p},
        "legalMoves": [_move_json(m) for m in game.legal_moves()],
        "check": checked is not None,
        "checkSquare": None if checked is None else square_name(checked),
        "lastMove": history[-1] if history else None,
        "history": history,
        "gameOver": outcome is not None,
        "result": None if outcome is None else {"termination": outcome.termination, "winner": outcome.winner},
        "claimableDraws": game.claimable_draws(),
        "halfmoveClock": board.halfmove_clock,
        "fullmoveNumber": board.fullmove_number,
        "enginePosition": None if outcome is not None else engine_position(game),
    }


def _load_game() -> Game:
    try:
        return Game.replay(session.get("moves", "").split(), session.get("claim"))
    except (IllegalMoveError, GameOverError, ValueError):
        session.clear()
        return Game()


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _save_game(game: Game) -> None:
    session["moves"] = " ".join(played.move.uci() for played in game.history)
    session["claim"] = game.claimed


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(config or {})
    if not app.secret_key:
        app.secret_key = _secret_key(app)

    @app.after_request
    def cross_origin_isolate(response):
        # The browser engine runs threaded WebAssembly, which needs SharedArrayBuffer,
        # which browsers only enable on cross-origin isolated pages.
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def get_state():
        return jsonify(game_state(_load_game()))

    @app.post("/api/move")
    def make_move():
        game = _load_game()
        data = _json_body()
        uci = data.get("move")
        if not isinstance(uci, str):
            return jsonify({"error": "Request body must be JSON with a 'move' string.", "state": game_state(game)}), 400
        try:
            game.play(uci)
        except (IllegalMoveError, GameOverError) as e:
            return jsonify({"error": str(e), "state": game_state(game)}), 400
        _save_game(game)
        return jsonify(game_state(game))

    @app.post("/api/claim-draw")
    def claim_draw():
        game = _load_game()
        data = _json_body()
        try:
            game.claim_draw(data.get("reason"))
        except IllegalMoveError as e:
            return jsonify({"error": str(e), "state": game_state(game)}), 400
        _save_game(game)
        return jsonify(game_state(game))

    @app.post("/api/reset")
    def reset_game():
        session.clear()
        return jsonify(game_state(Game()))

    return app


app = create_app()
