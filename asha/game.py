"""A game of Asha Chess: a board plus history, repetition and termination.

Termination follows the current FIDE Laws:

* automatic: checkmate, stalemate, dead position (insufficient material),
  fivefold repetition, 75-move rule;
* on claim by the side to move: threefold repetition, 50-move rule.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from .board import EN_PASSANT, STARTING_FEN, Board, Move

CHECKMATE = "checkmate"
STALEMATE = "stalemate"
INSUFFICIENT_MATERIAL = "insufficient_material"
FIVEFOLD_REPETITION = "fivefold_repetition"
SEVENTYFIVE_MOVES = "seventyfive_moves"
THREEFOLD_REPETITION = "threefold_repetition"
FIFTY_MOVES = "fifty_moves"

CLAIMABLE = (THREEFOLD_REPETITION, FIFTY_MOVES)


class IllegalMoveError(ValueError):
    pass


class GameOverError(ValueError):
    pass


@dataclass(frozen=True)
class Outcome:
    termination: str
    winner: str | None  # "white", "black" or None for a draw


@dataclass(frozen=True)
class PlayedMove:
    move: Move
    color: str  # "white" or "black"
    piece: str  # uppercase piece letter of the moving piece
    captured: str | None  # uppercase piece letter, if any
    notation: str  # SAN for classical moves, ``~`` form for Asha moves
    check: bool
    checkmate: bool


def _color(turn: str) -> str:
    return "white" if turn == "w" else "black"


class Game:
    def __init__(self, fen: str = STARTING_FEN):
        self.board = Board(fen)
        self.start_fen = self.board.fen()
        self.history: list[PlayedMove] = []
        self._repetitions = Counter([self.board.position_key()])
        self._claimed: Outcome | None = None
        self._legal: list[Move] | None = None
        self._outcome: Outcome | None = None
        self._outcome_known = False

    @classmethod
    def replay(cls, moves: Iterable[str], claim: str | None = None, fen: str = STARTING_FEN) -> Game:
        """Rebuild a game from UCI moves, validating every move."""
        game = cls(fen)
        for uci in moves:
            game.play(uci)
        if claim is not None:
            game.claim_draw(claim)
        return game

    # --------------------------------------------------------------- state

    def legal_moves(self) -> list[Move]:
        """Legal moves in the current position; empty once the game is over."""
        if self.is_over:
            return []
        return self._position_moves()

    def _position_moves(self) -> list[Move]:
        if self._legal is None:
            self._legal = self.board.legal_moves()
        return self._legal

    def outcome(self) -> Outcome | None:
        if self._claimed is not None:
            return self._claimed
        if not self._outcome_known:
            self._outcome = self._automatic_outcome()
            self._outcome_known = True
        return self._outcome

    def _automatic_outcome(self) -> Outcome | None:
        board = self.board
        if not self._position_moves():
            if board.is_check():
                return Outcome(CHECKMATE, _color("b" if board.turn == "w" else "w"))
            return Outcome(STALEMATE, None)
        if board.is_insufficient_material():
            return Outcome(INSUFFICIENT_MATERIAL, None)
        if board.halfmove_clock >= 150:
            return Outcome(SEVENTYFIVE_MOVES, None)
        if self._repetitions[board.position_key()] >= 5:
            return Outcome(FIVEFOLD_REPETITION, None)
        return None

    @property
    def is_over(self) -> bool:
        return self.outcome() is not None

    def claimable_draws(self) -> list[str]:
        """Draws the side to move may claim in the current position."""
        if self.is_over:
            return []
        claims = []
        if self._repetitions[self.board.position_key()] >= 3:
            claims.append(THREEFOLD_REPETITION)
        if self.board.halfmove_clock >= 100:
            claims.append(FIFTY_MOVES)
        return claims

    # ------------------------------------------------------------- actions

    def play(self, uci: str) -> PlayedMove:
        if self.is_over:
            raise GameOverError("the game is over")
        wanted = None
        try:
            wanted = Move.from_uci(uci)
        except ValueError:
            pass
        move = next((m for m in self._position_moves() if m == wanted), None)
        if move is None:
            raise IllegalMoveError(f"illegal move: {uci}")

        board = self.board
        color = _color(board.turn)
        piece = board.piece_type(move.from_sq)
        notation = board.notation(move, self._position_moves())
        captured = None
        if move.is_capture:
            captured = "P" if move.kind == EN_PASSANT else board.piece_type(move.to_sq)

        board.push(move)
        self._legal = None
        self._outcome_known = False
        self._repetitions[board.position_key()] += 1

        check = board.is_check()
        checkmate = check and not self._position_moves()
        played = PlayedMove(
            move, color, piece, captured, notation + ("#" if checkmate else "+" if check else ""), check, checkmate
        )
        self.history.append(played)
        return played

    def claim_draw(self, reason: str | None = None) -> Outcome:
        claims = self.claimable_draws()
        if reason is None and claims:
            reason = claims[0]
        if reason not in claims:
            raise IllegalMoveError(f"no draw claim available: {reason}")
        self._claimed = Outcome(reason, None)
        return self._claimed

    @property
    def claimed(self) -> str | None:
        return self._claimed.termination if self._claimed else None
