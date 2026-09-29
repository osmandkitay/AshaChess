"""Independent Asha move generator used only as a test oracle.

It shares no code with ``asha``: classical moves come from python-chess, Asha's
extra steps are added naively and filtered by python-chess's own check test.
This is valid because Asha's attack geometry is exactly classical.

python-chess allows a double push from any pawn on its second rank, so the
oracle tracks the squares of never-moved pawns (``virgin``) itself.
"""

import chess

_ADJACENT = [(df, dr) for df in (-1, 0, 1) for dr in (-1, 0, 1) if (df, dr) != (0, 0)]


def start_virgin(board: chess.Board) -> frozenset[int]:
    """Every pawn on its own starting rank still has the double step."""
    return frozenset(
        sq
        for sq, piece in board.piece_map().items()
        if piece.piece_type == chess.PAWN and chess.square_rank(sq) == (1 if piece.color == chess.WHITE else 6)
    )


def after(virgin: frozenset[int], uci: str) -> frozenset[int]:
    move = chess.Move.from_uci(uci)
    return virgin - {move.from_square, move.to_square}


def asha_legal_ucis(board: chess.Board, virgin: frozenset[int]) -> set[str]:
    moves = {
        m.uci()
        for m in board.legal_moves
        if not (board.piece_type_at(m.from_square) == chess.PAWN and abs(m.to_square - m.from_square) == 16)
        or m.from_square in virgin
    }
    for sq, piece in board.piece_map().items():
        if piece.color != board.turn:
            continue
        f, r = chess.square_file(sq), chess.square_rank(sq)
        if piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK):
            deltas = _ADJACENT
        elif piece.piece_type == chess.PAWN:
            deltas = [(-1, 0), (1, 0)]
        else:
            continue
        for df, dr in deltas:
            if 0 <= f + df < 8 and 0 <= r + dr < 8:
                to = chess.square(f + df, r + dr)
                if board.piece_at(to) is None:
                    move = chess.Move(sq, to)
                    board.push(move)
                    if not board.was_into_check():
                        moves.add(move.uci())
                    board.pop()
    return moves


def asha_perft(board: chess.Board, depth: int, virgin: frozenset[int] | None = None) -> int:
    if virgin is None:
        virgin = start_virgin(board)
    if depth == 0:
        return 1
    total = 0
    for uci in asha_legal_ucis(board, virgin):
        board.push(chess.Move.from_uci(uci))
        total += asha_perft(board, depth - 1, after(virgin, uci))
        board.pop()
    return total
