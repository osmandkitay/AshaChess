"""Differential test against an independent generator built on python-chess."""

import random

import pytest

from asha import Board

chess = pytest.importorskip("chess")
from tests.oracle import asha_legal_ucis  # noqa: E402

START_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1",
]


@pytest.mark.parametrize("seed", range(12))
def test_random_games_match_oracle(seed):
    rng = random.Random(seed)
    fen = START_FENS[seed % len(START_FENS)]
    board, reference = Board(fen), chess.Board(fen)
    for _ in range(150):
        moves = board.legal_moves()
        assert {m.uci() for m in moves} == asha_legal_ucis(reference), board.fen()
        # The classical subset is exactly classical chess.
        assert {m.uci() for m in moves if not m.is_asha} == {m.uci() for m in reference.legal_moves}
        assert board.is_check() == reference.is_check()
        # Placement, side to move, castling rights and legal en passant agree.
        assert board.fen().split()[:4] == reference.fen().split()[:4]
        if not moves:
            break
        move = rng.choice(moves)
        board.push(move)
        reference.push(chess.Move.from_uci(move.uci()))
