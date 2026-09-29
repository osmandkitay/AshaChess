"""Independent Asha move generator used only as a test oracle.

It shares no code with ``asha``: classical moves come from python-chess, Asha's
extra steps are added naively and filtered by python-chess's own check test.
This is valid because Asha's attack geometry is exactly classical.
"""

import chess

_ADJACENT = [(df, dr) for df in (-1, 0, 1) for dr in (-1, 0, 1) if (df, dr) != (0, 0)]


def asha_legal_ucis(board: chess.Board) -> set[str]:
    moves = {m.uci() for m in board.legal_moves}
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


def asha_perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    total = 0
    for uci in asha_legal_ucis(board):
        board.push(chess.Move.from_uci(uci))
        total += asha_perft(board, depth - 1)
        board.pop()
    return total
