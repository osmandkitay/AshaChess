from asha import Board, parse_square, square_name


def targets(fen: str, square: str) -> dict[str, str]:
    """Legal destinations (plus promotion letter) of the piece on ``square``, mapped to move kind."""
    board = Board(fen)
    origin = parse_square(square)
    return {square_name(m.to_sq) + (m.promotion or ""): m.kind for m in board.legal_moves() if m.from_sq == origin}


def ucis(board: Board) -> set[str]:
    return {m.uci() for m in board.legal_moves()}
