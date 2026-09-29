"""Asha Chess position, move generation and move execution.

Two geometries are kept deliberately separate:

* **Attack geometry** is exactly classical chess. It is the only thing used for
  captures, check, pins and castling safety (``is_attacked``).
* **Movement geometry** is the attack geometry plus Asha's non-capturing extras:
  the King's Step (one square in any direction onto an empty square) for
  knights, bishops and rooks, and the pawn's one-square sideways or
  diagonally-forward step onto an empty square. None of these extras can
  capture, so none of them ever attacks a square.

Squares are integers 0..63 (a1 = 0, h1 = 7, a8 = 56). Pieces are FEN letters,
uppercase for White.

A pawn's two-square move is a right, not a matter of rank: a pawn that stepped
sideways along its starting rank has moved and never double-steps again. The
set of pawns that still have the right (``Board.virgin``) is therefore part of
the position. FEN carries it as an optional seventh field listing their files
(uppercase White, lowercase Black, e.g. ``ABCEFGHabcdefgh``, ``-`` for none).
The field is omitted when every pawn on its starting rank still has the right,
so ordinary positions keep standard six-field FEN.
"""

from __future__ import annotations

from dataclasses import dataclass, field

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

FILES = "abcdefgh"

# Move kinds. Every legal move has exactly one kind; promotion is orthogonal.
QUIET = "quiet"  # classical non-capturing move (incl. pawn pushes)
CAPTURE = "capture"  # classical capture
EN_PASSANT = "en_passant"
CASTLING = "castling"
KINGS_STEP = "kings_step"  # Asha: non-capturing one-square step (N, B, R)
PAWN_LATERAL = "pawn_lateral"  # Asha: non-capturing sideways pawn step
PAWN_DIAGONAL = "pawn_diagonal"  # Asha: non-capturing diagonally-forward pawn step

CAPTURE_KINDS = frozenset({CAPTURE, EN_PASSANT})
ASHA_KINDS = frozenset({KINGS_STEP, PAWN_LATERAL, PAWN_DIAGONAL})

PROMOTION_PIECES = ("q", "r", "b", "n")


def square_name(sq: int) -> str:
    return FILES[sq & 7] + str((sq >> 3) + 1)


def parse_square(name: str) -> int:
    if len(name) != 2 or name[0] not in FILES or name[1] not in "12345678":
        raise ValueError(f"invalid square: {name!r}")
    return FILES.index(name[0]) + 8 * (int(name[1]) - 1)


ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAL = ((1, 1), (1, -1), (-1, 1), (-1, -1))
KNIGHT_JUMPS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))


def _offsets(sq: int, deltas) -> tuple[int, ...]:
    f, r = sq & 7, sq >> 3
    return tuple((r + dr) * 8 + f + df for df, dr in deltas if 0 <= f + df < 8 and 0 <= r + dr < 8)


def _rays(sq: int, directions) -> tuple[tuple[int, ...], ...]:
    rays = []
    for df, dr in directions:
        f, r, ray = (sq & 7) + df, (sq >> 3) + dr, []
        while 0 <= f < 8 and 0 <= r < 8:
            ray.append(r * 8 + f)
            f, r = f + df, r + dr
        if ray:
            rays.append(tuple(ray))
    return tuple(rays)


KNIGHT_TARGETS = tuple(_offsets(sq, KNIGHT_JUMPS) for sq in range(64))
KING_TARGETS = tuple(_offsets(sq, ORTHOGONAL + DIAGONAL) for sq in range(64))
ROOK_RAYS = tuple(_rays(sq, ORTHOGONAL) for sq in range(64))
BISHOP_RAYS = tuple(_rays(sq, DIAGONAL) for sq in range(64))

# King's Step destinations that are *not* already part of the piece's classical
# movement. A rook's orthogonal step and a bishop's diagonal step are ordinary
# slides (and can capture); only the remaining directions are Asha moves.
KINGS_STEP_TARGETS = {
    "N": tuple(_offsets(sq, ORTHOGONAL + DIAGONAL) for sq in range(64)),
    "B": tuple(_offsets(sq, ORTHOGONAL) for sq in range(64)),
    "R": tuple(_offsets(sq, DIAGONAL) for sq in range(64)),
}

# Castling rights lost when a move starts or ends on one of these squares.
_CASTLING_SQUARES = {4: "KQ", 7: "K", 0: "Q", 60: "kq", 63: "k", 56: "q"}
# right -> (king from, king to, rook from, rook to, squares that must be empty)
_CASTLING = {
    "K": (4, 6, 7, 5, (5, 6)),
    "Q": (4, 2, 0, 3, (3, 2, 1)),
    "k": (60, 62, 63, 61, (61, 62)),
    "q": (60, 58, 56, 59, (59, 58, 57)),
}


@dataclass(frozen=True)
class Move:
    """A move. Identity is (from, to, promotion); ``kind`` is metadata."""

    from_sq: int
    to_sq: int
    promotion: str | None = None
    kind: str = field(default=QUIET, compare=False)

    @property
    def is_capture(self) -> bool:
        return self.kind in CAPTURE_KINDS

    @property
    def is_asha(self) -> bool:
        return self.kind in ASHA_KINDS

    def uci(self) -> str:
        return square_name(self.from_sq) + square_name(self.to_sq) + (self.promotion or "")

    @classmethod
    def from_uci(cls, text: str) -> Move:
        if len(text) not in (4, 5):
            raise ValueError(f"invalid UCI move: {text!r}")
        promotion = text[4:] or None
        if promotion is not None and promotion not in PROMOTION_PIECES:
            raise ValueError(f"invalid promotion piece: {text!r}")
        return cls(parse_square(text[:2]), parse_square(text[2:4]), promotion)

    def __str__(self) -> str:
        return self.uci()


def _is_white(piece: str) -> bool:
    return piece.isupper()


def _default_virgin(squares: list[str | None]) -> frozenset[int]:
    """Every pawn on its own starting rank, as in a FEN without the 7th field."""
    return frozenset(
        sq for sq in range(8, 56) if (sq >> 3 == 1 and squares[sq] == "P") or (sq >> 3 == 6 and squares[sq] == "p")
    )


def _parse_virgin(field: str) -> frozenset[int]:
    if field == "-":
        return frozenset()
    squares = [FILES.index(c.lower()) + (8 if c.isupper() else 48) for c in field if c.lower() in FILES]
    if len(squares) != len(field) or len(set(squares)) != len(squares):
        raise ValueError(f"invalid double-step field: {field!r}")
    return frozenset(squares)


def _format_virgin(virgin: frozenset[int]) -> str:
    white = "".join(FILES[sq & 7].upper() for sq in sorted(virgin) if sq >> 3 == 1)
    black = "".join(FILES[sq & 7] for sq in sorted(virgin) if sq >> 3 == 6)
    return white + black or "-"


def _castling_rook(move: Move, white: bool) -> tuple[int, int]:
    right = "K" if move.to_sq > move.from_sq else "Q"
    _, _, rook_from, rook_to, _ = _CASTLING[right if white else right.lower()]
    return rook_from, rook_to


class Board:
    """A mutable Asha Chess position with push/pop."""

    def __init__(self, fen: str = STARTING_FEN):
        self.set_fen(fen)

    # ------------------------------------------------------------------ FEN

    def set_fen(self, fen: str) -> None:
        parts = fen.split()
        if len(parts) not in (6, 7):
            raise ValueError(f"FEN must have 6 or 7 fields: {fen!r}")
        placement, turn, castling, ep, halfmove, fullmove = parts[:6]

        squares: list[str | None] = [None] * 64
        rows = placement.split("/")
        if len(rows) != 8:
            raise ValueError("FEN placement must have 8 ranks")
        for i, row in enumerate(rows):
            rank, file = 7 - i, 0
            for ch in row:
                if ch.isdigit():
                    file += int(ch)
                elif ch in "PNBRQKpnbrqk":
                    if file > 7:
                        raise ValueError(f"FEN rank too long: {row!r}")
                    squares[rank * 8 + file] = ch
                    file += 1
                else:
                    raise ValueError(f"invalid FEN character: {ch!r}")
            if file != 8:
                raise ValueError(f"FEN rank has wrong length: {row!r}")

        if turn not in ("w", "b"):
            raise ValueError(f"invalid side to move: {turn!r}")
        if castling != "-" and (any(c not in "KQkq" for c in castling) or len(set(castling)) != len(castling)):
            raise ValueError(f"invalid castling field: {castling!r}")

        self.squares = squares
        if len(parts) == 7:
            self.virgin = _parse_virgin(parts[6])
        else:
            self.virgin = _default_virgin(squares)
        self.turn = turn
        self.castling = "".join(c for c in "KQkq" if c in castling)
        self.ep_square = None if ep == "-" else parse_square(ep)
        self.halfmove_clock = int(halfmove)
        self.fullmove_number = int(fullmove)
        self._stack: list[tuple] = []
        self._validate()

    def _validate(self) -> None:
        s = self.squares
        kings: dict[bool, list[int]] = {True: [], False: []}
        for sq, p in enumerate(s):
            if p in ("K", "k"):
                kings[p == "K"].append(sq)
            elif p in ("P", "p") and sq >> 3 in (0, 7):
                raise ValueError("pawns cannot stand on the first or last rank")
        if len(kings[True]) != 1 or len(kings[False]) != 1:
            raise ValueError("each side must have exactly one king")
        self.kings = {True: kings[True][0], False: kings[False][0]}

        for right in self.castling:
            king_from, _, rook_from, _, _ = _CASTLING[right]
            king, rook = ("K", "R") if right.isupper() else ("k", "r")
            if s[king_from] != king or s[rook_from] != rook:
                raise ValueError(f"castling right {right!r} does not match the position")

        if self.ep_square is not None:
            white = self.turn == "w"
            ep, forward = self.ep_square, 8 if white else -8
            pawn = "p" if white else "P"
            if (
                ep >> 3 != (5 if white else 2)
                or s[ep] is not None
                or s[ep + forward] is not None
                or s[ep - forward] != pawn
            ):
                raise ValueError("invalid en passant square")

        for sq in self.virgin:
            if s[sq] != ("P" if sq >> 3 == 1 else "p"):
                raise ValueError(f"double-step right on {square_name(sq)} without a pawn on its starting square")

        if self.halfmove_clock < 0 or self.fullmove_number < 1:
            raise ValueError("invalid move counters")
        white = self.turn == "w"
        if self.is_attacked(self.kings[not white], white):
            raise ValueError("the side not to move is in check")

    def fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            row, empty = "", 0
            for file in range(8):
                p = self.squares[rank * 8 + file]
                if p is None:
                    empty += 1
                else:
                    row += (str(empty) if empty else "") + p
                    empty = 0
            rows.append(row + (str(empty) if empty else ""))
        ep = self.legal_ep_square()
        fields = [
            "/".join(rows),
            self.turn,
            self.castling or "-",
            "-" if ep is None else square_name(ep),
            str(self.halfmove_clock),
            str(self.fullmove_number),
        ]
        if self.virgin != _default_virgin(self.squares):
            fields.append(_format_virgin(self.virgin))
        return " ".join(fields)

    def piece_at(self, sq: int) -> str | None:
        return self.squares[sq]

    def piece_type(self, sq: int) -> str:
        """Uppercase letter of the piece on an occupied square."""
        piece = self.squares[sq]
        if piece is None:
            raise ValueError(f"no piece on {square_name(sq)}")
        return piece.upper()

    # --------------------------------------------------------------- attacks

    def is_attacked(self, sq: int, by_white: bool) -> bool:
        """Whether ``sq`` is attacked by the given side (classical geometry)."""
        s = self.squares
        f = sq & 7
        if by_white:
            pawn, knight, king, rook, bishop, queen = "P", "N", "K", "R", "B", "Q"
            pawn_from = sq - 8
        else:
            pawn, knight, king, rook, bishop, queen = "p", "n", "k", "r", "b", "q"
            pawn_from = sq + 8
        if 0 <= pawn_from < 64:
            if f > 0 and s[pawn_from - 1] == pawn:
                return True
            if f < 7 and s[pawn_from + 1] == pawn:
                return True
        for t in KNIGHT_TARGETS[sq]:
            if s[t] == knight:
                return True
        for t in KING_TARGETS[sq]:
            if s[t] == king:
                return True
        for ray in ROOK_RAYS[sq]:
            for t in ray:
                p = s[t]
                if p is not None:
                    if p == rook or p == queen:
                        return True
                    break
        for ray in BISHOP_RAYS[sq]:
            for t in ray:
                p = s[t]
                if p is not None:
                    if p == bishop or p == queen:
                        return True
                    break
        return False

    def is_check(self) -> bool:
        white = self.turn == "w"
        return self.is_attacked(self.kings[white], not white)

    def checked_king(self) -> int | None:
        return self.kings[self.turn == "w"] if self.is_check() else None

    # -------------------------------------------------------- move generation

    def _pseudo_legal_moves(self) -> list[Move]:
        """All moves obeying movement geometry, ignoring own-king safety.

        Castling is the exception: it is only emitted when fully legal, because
        its legality depends on attacked transit squares rather than on the
        resulting position alone.
        """
        s = self.squares
        white = self.turn == "w"
        moves: list[Move] = []
        add = moves.append
        for sq, p in enumerate(s):
            if p is None or _is_white(p) != white:
                continue
            kind = p.upper()
            if kind == "P":
                self._pawn_moves(sq, white, moves)
                continue
            if kind == "N" or kind == "K":
                for t in (KNIGHT_TARGETS if kind == "N" else KING_TARGETS)[sq]:
                    q = s[t]
                    if q is None:
                        add(Move(sq, t, None, QUIET))
                    elif _is_white(q) != white:
                        add(Move(sq, t, None, CAPTURE))
            else:
                rays: tuple[tuple[int, ...], ...] = ()
                if kind != "B":
                    rays += ROOK_RAYS[sq]
                if kind != "R":
                    rays += BISHOP_RAYS[sq]
                for ray in rays:
                    for t in ray:
                        q = s[t]
                        if q is None:
                            add(Move(sq, t, None, QUIET))
                        else:
                            if _is_white(q) != white:
                                add(Move(sq, t, None, CAPTURE))
                            break
            steps = KINGS_STEP_TARGETS.get(kind)
            if steps is not None:
                for t in steps[sq]:
                    if s[t] is None:
                        add(Move(sq, t, None, KINGS_STEP))
        self._castling_moves(white, moves)
        return moves

    def _pawn_moves(self, sq: int, white: bool, moves: list[Move]) -> None:
        s = self.squares
        f, r = sq & 7, sq >> 3
        forward = 8 if white else -8
        promotes = r == (6 if white else 1)

        def add(to: int, kind: str) -> None:
            if promotes:
                moves.extend(Move(sq, to, piece, kind) for piece in PROMOTION_PIECES)
            else:
                moves.append(Move(sq, to, None, kind))

        one = sq + forward
        if s[one] is None:
            add(one, QUIET)
            if sq in self.virgin and s[one + forward] is None:
                moves.append(Move(sq, one + forward, None, QUIET))
        for df in (-1, 1):
            if not 0 <= f + df < 8:
                continue
            target = one + df
            q = s[target]
            if q is not None:
                if _is_white(q) != white:
                    add(target, CAPTURE)
            elif target == self.ep_square:
                moves.append(Move(sq, target, None, EN_PASSANT))
            else:
                add(target, PAWN_DIAGONAL)
            side = sq + df
            if s[side] is None:
                moves.append(Move(sq, side, None, PAWN_LATERAL))

    def _castling_moves(self, white: bool, moves: list[Move]) -> None:
        rights = "KQ" if white else "kq"
        if not any(c in self.castling for c in rights):
            return
        king_sq = self.kings[white]
        if self.is_attacked(king_sq, not white):
            return
        for right in rights:
            if right not in self.castling:
                continue
            _, king_to, _, rook_to, empty = _CASTLING[right]
            if any(self.squares[t] is not None for t in empty):
                continue
            if self.is_attacked(rook_to, not white) or self.is_attacked(king_to, not white):
                continue
            moves.append(Move(king_sq, king_to, None, CASTLING))

    def _is_legal(self, move: Move) -> bool:
        if move.kind == CASTLING:
            return True
        white = self.turn == "w"
        self.push(move)
        legal = not self.is_attacked(self.kings[white], not white)
        self.pop()
        return legal

    def legal_moves(self) -> list[Move]:
        return [m for m in self._pseudo_legal_moves() if self._is_legal(m)]

    def legal_ep_square(self) -> int | None:
        """The en passant square, only if an en passant capture is legal now."""
        ep = self.ep_square
        if ep is None:
            return None
        white = self.turn == "w"
        pawn = "P" if white else "p"
        behind = ep - (8 if white else -8)
        for df in (-1, 1):
            if 0 <= (ep & 7) + df < 8 and self.squares[behind + df] == pawn:
                if self._is_legal(Move(behind + df, ep, None, EN_PASSANT)):
                    return ep
        return None

    # --------------------------------------------------------- make / unmake

    def push(self, move: Move) -> None:
        """Play a move produced by this board's generator (not re-validated)."""
        s = self.squares
        white = self.turn == "w"
        piece = s[move.from_sq]
        captured = s[move.to_sq]
        self._stack.append(
            (move, captured, self.castling, self.ep_square, self.halfmove_clock, self.fullmove_number, self.virgin)
        )

        s[move.to_sq] = piece
        s[move.from_sq] = None
        if move.kind == EN_PASSANT:
            victim_sq = move.to_sq - (8 if white else -8)
            captured = s[victim_sq]
            s[victim_sq] = None
        elif move.kind == CASTLING:
            rook_from, rook_to = _castling_rook(move, white)
            s[rook_to] = s[rook_from]
            s[rook_from] = None
        if move.promotion:
            s[move.to_sq] = move.promotion.upper() if white else move.promotion
        if piece == "K" or piece == "k":
            self.kings[white] = move.to_sq

        if self.castling:
            for sq in (move.from_sq, move.to_sq):
                lost = _CASTLING_SQUARES.get(sq)
                if lost:
                    self.castling = "".join(c for c in self.castling if c not in lost)

        # A pawn leaving its square, or being captured on it, loses the double step.
        if move.from_sq in self.virgin or move.to_sq in self.virgin:
            self.virgin = self.virgin - {move.from_sq, move.to_sq}

        is_pawn = piece == "P" or piece == "p"
        self.ep_square = (move.from_sq + move.to_sq) // 2 if is_pawn and abs(move.to_sq - move.from_sq) == 16 else None
        # Every pawn move resets the clock, including sideways and diagonal
        # steps: they can spend the pawn's double-step right.
        if captured is not None or is_pawn:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if not white:
            self.fullmove_number += 1
        self.turn = "b" if white else "w"

    def pop(self) -> Move:
        move, captured, castling, ep, halfmove, fullmove, virgin = self._stack.pop()
        s = self.squares
        self.turn = "w" if self.turn == "b" else "b"
        white = self.turn == "w"
        piece = s[move.to_sq]
        if move.promotion:
            piece = "P" if white else "p"
        s[move.from_sq] = piece
        s[move.to_sq] = captured
        if move.kind == EN_PASSANT:
            s[move.to_sq] = None
            s[move.to_sq - (8 if white else -8)] = "p" if white else "P"
        elif move.kind == CASTLING:
            rook_from, rook_to = _castling_rook(move, white)
            s[rook_from] = s[rook_to]
            s[rook_to] = None
        if piece == "K" or piece == "k":
            self.kings[white] = move.from_sq
        self.castling = castling
        self.ep_square = ep
        self.halfmove_clock = halfmove
        self.fullmove_number = fullmove
        self.virgin = virgin
        return move

    # ------------------------------------------------------------ utilities

    def position_key(self) -> tuple:
        """Identity of a position for repetition: placement, side to move,
        castling rights, a *legal* en passant possibility (FIDE 9.2.3) and the
        pawns' double-step rights."""
        return ("".join(p or "." for p in self.squares), self.turn, self.castling, self.legal_ep_square(), self.virgin)

    def is_insufficient_material(self) -> bool:
        """True only when no checkmate position exists for either side.

        Only K v K, K+N v K and K+B v K qualify. The classical same-coloured
        bishops rule does not apply: in Asha a bishop changes square colour
        with its King's Step.
        """
        others = [p for p in self.squares if p is not None and p not in ("K", "k")]
        return not others or (len(others) == 1 and others[0] in ("N", "B", "n", "b"))

    def notation(self, move: Move, legal_moves: list[Move]) -> str:
        """Notation for a legal move, without the check/mate suffix.

        Classical moves use standard SAN. Asha moves are written with their
        origin and a tilde so they can never be mistaken for SAN:
        King's Step ``Nb1~b2``, pawn sideways step ``e4~d4``, pawn diagonal
        step ``e4~d5`` (``e7~d8=Q`` when it promotes).
        """
        piece = self.piece_type(move.from_sq)
        to = square_name(move.to_sq)
        if move.kind == CASTLING:
            return "O-O" if move.to_sq > move.from_sq else "O-O-O"
        if move.kind == KINGS_STEP:
            return f"{piece}{square_name(move.from_sq)}~{to}"
        promotion = f"={move.promotion.upper()}" if move.promotion else ""
        if move.kind in (PAWN_LATERAL, PAWN_DIAGONAL):
            return f"{square_name(move.from_sq)}~{to}{promotion}"
        if piece == "P":
            if move.is_capture:
                return f"{FILES[move.from_sq & 7]}x{to}{promotion}"
            return to + promotion

        rivals = [
            m.from_sq
            for m in legal_moves
            if m.to_sq == move.to_sq
            and m.from_sq != move.from_sq
            and not m.is_asha
            and self.piece_type(m.from_sq) == piece
        ]
        origin = square_name(move.from_sq)
        if not rivals:
            disambiguation = ""
        elif all((r & 7) != (move.from_sq & 7) for r in rivals):
            disambiguation = origin[0]
        elif all((r >> 3) != (move.from_sq >> 3) for r in rivals):
            disambiguation = origin[1]
        else:
            disambiguation = origin
        return f"{piece}{disambiguation}{'x' if move.is_capture else ''}{to}"

    def perft(self, depth: int) -> int:
        if depth == 0:
            return 1
        moves = self.legal_moves()
        if depth == 1:
            return len(moves)
        total = 0
        for move in moves:
            self.push(move)
            total += self.perft(depth - 1)
            self.pop()
        return total
