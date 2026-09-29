"""Perft regression oracle.

Every count below was verified once against the independent python-chess based
generator in ``tests/oracle.py``. The start position has 34 moves, not
classical chess's 20: each side adds 14 non-capturing diagonally-forward pawn
steps (34 * 34 = 1156 at depth 2). The last position has room for sideways
pawn steps on the starting ranks, so it exercises the loss of the double-step
right.
"""

import pytest

from asha import Board

PERFT = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [34, 1156, 45800, 1806576]),
    ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", [47, 2196, 108795]),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [71, 4644, 330344]),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [26, 640, 16402]),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [13, 859, 55080]),
    ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", [9, 76, 802]),
    ("r3k2r/1b4n1/8/3B4/2p1P3/2N2p2/1P6/R3K2R w KQkq - 0 1", [57, 2670, 139615]),
    ("4k3/p1p1p1p1/8/8/8/8/P1P1P1P1/4K3 w - - 0 1", [26, 676, 16532, 404082]),
]


def test_start_position_has_34_moves_not_the_classical_20():
    board = Board()
    moves = board.legal_moves()
    assert len(moves) == 34
    assert sum(m.kind == "pawn_diagonal" for m in moves) == 14
    assert len(moves) - 14 == 20  # the classical moves are all still there


@pytest.mark.parametrize(("fen", "counts"), PERFT)
def test_perft(fen, counts):
    board = Board(fen)
    assert [board.perft(depth) for depth in range(1, len(counts) + 1)] == counts
    assert board.fen() == fen  # perft leaves the board untouched
