"""One interface over the two referees: the ``asha`` package and python-chess.

Both follow the same game-end policy, the one the Asha web game uses: the
automatic FIDE endings end the game, and a draw is claimed as soon as the side
to move may claim it (threefold repetition: the current position has occurred
three times; 50-move rule: 100 half-moves without a pawn move or capture).
"""

from __future__ import annotations

from dataclasses import dataclass

import chess

from app import engine_position
from asha import Game
from asha.board import ASHA_KINDS, CASTLING, EN_PASSANT, QUIET
from asha.board import CAPTURE as CAPTURE_KIND

# Phase boundaries follow lichess's Divider: the endgame begins when at most 6
# queens, rooks, bishops and knights (both sides together) are left; the
# middlegame when at most 10 are left. Lichess also starts the middlegame on a
# sparse back rank or mixed pawn structure; we use "after ply 20" instead.
ENDGAME_PIECES = 6
MIDDLEGAME_PIECES = 10
OPENING_PLIES = 20


def phase(pieces: int, ply: int) -> str:
    """'o', 'm' or 'e' for a position with this many Q/R/B/N after ply half-moves."""
    if pieces <= ENDGAME_PIECES:
        return "e"
    if pieces <= MIDDLEGAME_PIECES or ply >= OPENING_PLIES:
        return "m"
    return "o"


@dataclass(frozen=True)
class Ply:
    uci: str
    kind: str
    piece: str  # uppercase letter of the moving piece
    capture: bool
    check: bool
    notation: str


@dataclass(frozen=True)
class Result:
    termination: str
    winner: str | None  # "white", "black" or None

    @property
    def score(self) -> str:
        return {"white": "1-0", "black": "0-1", None: "1/2-1/2"}[self.winner]


class AshaRules:
    variant = "asha"
    classical_referee = False

    def __init__(self) -> None:
        self.game = Game()

    def legal(self) -> dict[str, str]:
        """Legal moves (UCI) and their kind."""
        return {m.uci(): m.kind for m in self.game.legal_moves()}

    def play(self, uci: str) -> Ply:
        played = self.game.play(uci)
        return Ply(uci, played.move.kind, played.piece, played.captured is not None, played.check, played.notation)

    def result(self) -> Result | None:
        """The result once the game has ended, claiming a draw when one is claimable."""
        if not self.game.is_over and self.game.claimable_draws():
            self.game.claim_draw()
        outcome = self.game.outcome()
        return None if outcome is None else Result(outcome.termination, outcome.winner)

    def engine_input(self) -> tuple[str, list[str]]:
        position = engine_position(self.game)
        return position["fen"], position["moves"]

    def pieces(self) -> int:
        return sum(1 for p in self.game.board.squares if p and p.upper() in "QRBN")

    def fen(self) -> str:
        """Asha FEN, including the optional double-step field."""
        return self.game.board.fen()

    @property
    def white_to_move(self) -> bool:
        return self.game.board.turn == "w"


class ChessRules:
    variant = "chess"
    classical_referee = True

    def __init__(self) -> None:
        self.board = chess.Board()
        self._claimed: Result | None = None

    def legal(self) -> dict[str, str]:
        return {move.uci(): self._kind(move) for move in self.board.legal_moves}

    def _kind(self, move: chess.Move) -> str:
        if self.board.is_castling(move):
            return CASTLING
        if self.board.is_en_passant(move):
            return EN_PASSANT
        if self.board.is_capture(move):
            return CAPTURE_KIND
        return QUIET

    def play(self, uci: str) -> Ply:
        move = chess.Move.from_uci(uci)
        if move not in self.board.legal_moves:
            raise ValueError(f"illegal move: {uci}")
        kind = self._kind(move)
        piece = chess.piece_symbol(self.board.piece_type_at(move.from_square) or chess.PAWN).upper()
        capture = self.board.is_capture(move)
        notation = self.board.san(move)
        self.board.push(move)
        return Ply(uci, kind, piece, capture, self.board.is_check(), notation)

    def result(self) -> Result | None:
        if self._claimed:
            return self._claimed
        outcome = self.board.outcome(claim_draw=False)
        if outcome is not None:
            return Result(_TERMINATIONS[outcome.termination], _winner(outcome.winner))
        if self.board.is_repetition(3):
            self._claimed = Result("threefold_repetition", None)
        elif self.board.halfmove_clock >= 100:
            self._claimed = Result("fifty_moves", None)
        return self._claimed

    def engine_input(self) -> tuple[str, list[str]]:
        return chess.STARTING_FEN, [m.uci() for m in self.board.move_stack]

    def pieces(self) -> int:
        return sum(len(self.board.pieces(t, c)) for t in _MAJORS_AND_MINORS for c in chess.COLORS)

    def fen(self) -> str:
        return self.board.fen()

    @property
    def white_to_move(self) -> bool:
        return self.board.turn == chess.WHITE


_MAJORS_AND_MINORS = (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)

_TERMINATIONS = {
    chess.Termination.CHECKMATE: "checkmate",
    chess.Termination.STALEMATE: "stalemate",
    chess.Termination.INSUFFICIENT_MATERIAL: "insufficient_material",
    chess.Termination.FIVEFOLD_REPETITION: "fivefold_repetition",
    chess.Termination.SEVENTYFIVE_MOVES: "seventyfive_moves",
}


def _winner(color: chess.Color | None) -> str | None:
    return None if color is None else ("white" if color == chess.WHITE else "black")


RULES = {"asha": AshaRules, "chess": ChessRules}


def is_asha_kind(kind: str) -> bool:
    return kind in ASHA_KINDS
