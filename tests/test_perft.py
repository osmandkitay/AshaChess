"""Perft regression oracle.

Every count below was verified once against the independent python-chess based
generator in ``tests/oracle.py``. Depth 1-2 of the start position equal
classical chess (20, 400): Asha's extra steps are all blocked until a pawn or
piece has moved. The last position has room for sideways pawn steps on the
starting ranks, so it exercises the loss of the double-step right.
"""

import pytest

from asha import Board

PERFT = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [20, 400, 10822, 291783]),
    ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", [33, 1085, 39405]),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [62, 3683, 229424]),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [22, 465, 10440]),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [12, 675, 34050]),
    ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", [8, 53, 455]),
    ("r3k2r/1b4n1/8/3B4/2p1P3/2N2p2/1P6/R3K2R w KQkq - 0 1", [55, 2374, 118222]),
    ("4k3/p1p1p1p1/8/8/8/8/P1P1P1P1/4K3 w - - 0 1", [19, 361, 6304, 109968]),
]


@pytest.mark.parametrize(("fen", "counts"), PERFT)
def test_perft(fen, counts):
    board = Board(fen)
    assert [board.perft(depth) for depth in range(1, len(counts) + 1)] == counts
    assert board.fen() == fen  # perft leaves the board untouched
