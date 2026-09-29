"""Game termination, draw claims, repetition, notation, history and FEN."""

import random

import pytest

from asha import (
    CHECKMATE,
    FIFTY_MOVES,
    FIVEFOLD_REPETITION,
    INSUFFICIENT_MATERIAL,
    KINGS_STEP,
    PAWN_LATERAL,
    SEVENTYFIVE_MOVES,
    STALEMATE,
    STARTING_FEN,
    THREEFOLD_REPETITION,
    Board,
    Game,
    GameOverError,
    IllegalMoveError,
    Outcome,
    parse_square,
)
from tests.helpers import ucis

# ------------------------------------------------------------ mate / stalemate


def test_back_rank_checkmate():
    game = Game("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    played = game.play("a1a8")
    assert played.checkmate and played.notation == "Ra8#"
    assert game.outcome() == Outcome(CHECKMATE, "white")
    assert game.legal_moves() == []


def test_scholars_mate_is_still_mate():
    game = Game.replay(["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"])
    assert game.outcome() == Outcome(CHECKMATE, "white")
    assert game.history[-1].notation == "Qxf7#"


def test_fools_mate_is_not_mate_because_of_kings_steps():
    game = Game.replay(["f2f3", "e7e5", "g2g4", "d8h4"])
    assert game.board.is_check()
    assert game.outcome() is None
    assert game.history[-1].notation == "Qh4+"
    kinds = {m.uci(): m.kind for m in game.legal_moves()}
    # Classically mate; in Asha four non-capturing moves block the diagonal.
    assert kinds == {"g1f2": KINGS_STEP, "f1f2": KINGS_STEP, "e2f2": PAWN_LATERAL, "f3g3": PAWN_LATERAL}


def test_stalemate():
    game = Game("7k/8/6K1/8/8/8/8/5Q2 w - - 0 1")
    played = game.play("f1f7")
    assert played.notation == "Qf7"  # no check or mate suffix on a stalemating move
    assert game.outcome() == Outcome(STALEMATE, None)


def test_classical_stalemate_is_not_stalemate_when_a_pawn_can_step_sideways():
    game = Game("7k/5Q2/6K1/p7/P7/8/8/8 b - - 0 1")
    assert game.outcome() is None
    assert [m.uci() for m in game.legal_moves()] == ["a5b5"]


def test_no_moves_after_game_over():
    game = Game("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    game.play("a1a8")
    with pytest.raises(GameOverError):
        game.play("g8h8")
    with pytest.raises(IllegalMoveError):
        game.claim_draw()


def test_illegal_and_malformed_moves_are_rejected():
    game = Game()
    for bad in ("e2e5", "e2d3", "e1e2", "", "e2", "zz99", "e2e4x", "e7e5"):
        with pytest.raises(IllegalMoveError):
            game.play(bad)
    assert game.history == []


# ------------------------------------------------------- insufficient material


@pytest.mark.parametrize(
    "fen",
    [
        "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/4KN2 w - - 0 1",
        "4k3/8/8/8/8/8/8/4KB2 b - - 0 1",
        "4kn2/8/8/8/8/8/8/4K3 w - - 0 1",
    ],
)
def test_insufficient_material(fen):
    assert Game(fen).outcome() == Outcome(INSUFFICIENT_MATERIAL, None)


@pytest.mark.parametrize(
    "fen",
    [
        # Classical chess calls same-coloured bishops dead; Asha bishops change colour.
        "4k3/8/8/8/8/8/2b5/4KB2 w - - 0 1",
        "4k3/8/8/8/8/3B4/8/4KB2 w - - 0 1",
        "4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1",
        "4kb2/8/8/8/8/8/8/4KN2 w - - 0 1",
        "4k3/8/8/8/8/8/P7/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/8/4K2R w - - 0 1",
    ],
)
def test_sufficient_material(fen):
    assert not Board(fen).is_insufficient_material()


def test_capture_into_bare_kings_ends_the_game():
    game = Game("4k3/8/8/8/8/8/3q4/4K3 w - - 0 1")
    game.play("e1d2")
    assert game.outcome() == Outcome(INSUFFICIENT_MATERIAL, None)


# ------------------------------------------------------------------ repetition

KNIGHT_SHUFFLE = ["g1f3", "g8f6", "f3g1", "f6g8"]


def test_threefold_is_claimable_and_fivefold_is_automatic():
    game = Game()
    for uci in KNIGHT_SHUFFLE:
        game.play(uci)
    assert game.claimable_draws() == []
    for uci in KNIGHT_SHUFFLE:
        game.play(uci)
    assert game.claimable_draws() == [THREEFOLD_REPETITION]
    assert game.outcome() is None
    for uci in KNIGHT_SHUFFLE * 2:
        game.play(uci)
    assert game.outcome() == Outcome(FIVEFOLD_REPETITION, None)
    assert game.claimable_draws() == []


def test_claiming_threefold_ends_the_game():
    game = Game.replay(KNIGHT_SHUFFLE * 2)
    assert game.claim_draw() == Outcome(THREEFOLD_REPETITION, None)
    assert game.is_over and game.legal_moves() == []
    with pytest.raises(GameOverError):
        game.play("g1f3")


def test_claim_is_rejected_when_not_available():
    game = Game.replay(KNIGHT_SHUFFLE)
    with pytest.raises(IllegalMoveError):
        game.claim_draw()
    with pytest.raises(IllegalMoveError):
        game.claim_draw(FIFTY_MOVES)


def test_repetition_counts_castling_rights_not_just_placement():
    # Same placement three times, but the first occurrence still had White's
    # kingside castling right, so it is a different position.
    game = Game.replay(["g1f3", "g8f6", "h1g1", "f6g8", "g1h1", "g8f6"])
    loop = ["f3g1", "f6g8", "g1f3", "g8f6"]
    for uci in loop:
        game.play(uci)
    assert game.claimable_draws() == []
    for uci in loop:
        game.play(uci)
    assert game.claimable_draws() == [THREEFOLD_REPETITION]


def test_repetition_counts_side_to_move():
    # White triangulates (3 moves) while Black shuffles (2 moves): the
    # placement returns with Black to move, which is a different position.
    fen = "4k3/p7/8/8/8/8/P7/4K3 w - - 0 1"
    game = Game(fen)
    for uci in ["e1e2", "e8e7", "e2d1", "e7e8", "d1e1"]:
        game.play(uci)
    start = Board(fen).position_key()
    assert game.board.position_key()[0] == start[0]
    assert game.board.position_key() != start
    assert game._repetitions[start] == 1


def test_position_key_includes_en_passant_only_when_capture_is_legal():
    with_ep = Board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
    without = Board("4k3/8/8/3pP3/8/8/8/4K3 w - - 0 2")
    assert with_ep.position_key() != without.position_key()
    # Here the en passant capture is illegal (it exposes the king): same position.
    pinned_ep = Board("8/8/8/K2pP2r/8/8/8/7k w - d6 0 2")
    pinned_none = Board("8/8/8/K2pP2r/8/8/8/7k w - - 0 2")
    assert pinned_ep.position_key() == pinned_none.position_key()


def test_repetition_counts_double_step_rights():
    # d2~c2, c2~d2 restores the placement, but the pawn has lost its double
    # step: the start position never occurs again.
    fen = "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1"
    game = Game.replay(["d2c2", "e8e7", "c2d2", "e7e8"], fen=fen)
    start = Board(fen).position_key()
    assert game.board.position_key()[0] == start[0]
    assert game.board.position_key() != start
    for uci in ["e1f1", "e8f8", "f1e1", "f8e8"]:
        game.play(uci)
    assert game.claimable_draws() == []  # placement seen 3 times, position only twice
    for uci in ["e1f1", "e8f8", "f1e1", "f8e8"]:
        game.play(uci)
    assert game.claimable_draws() == [THREEFOLD_REPETITION]


# --------------------------------------------------------- fifty / seventy-five


def test_fifty_move_rule_is_claimable():
    game = Game("4k3/8/8/8/8/8/8/R3K3 w - - 99 80")
    game.play("a1a2")
    assert game.board.halfmove_clock == 100
    assert game.outcome() is None
    assert game.claimable_draws() == [FIFTY_MOVES]
    assert game.claim_draw(FIFTY_MOVES) == Outcome(FIFTY_MOVES, None)


def test_seventyfive_move_rule_is_automatic():
    game = Game("4k3/8/8/8/8/8/8/R3K3 w - - 149 100")
    game.play("a1a2")
    assert game.outcome() == Outcome(SEVENTYFIVE_MOVES, None)


def test_checkmate_takes_precedence_over_seventyfive_moves():
    game = Game("6k1/5ppp/8/8/8/8/8/R5K1 w - - 149 100")
    game.play("a1a8")
    assert game.outcome() == Outcome(CHECKMATE, "white")


def test_halfmove_clock_resets_on_every_pawn_move_and_capture():
    game = Game("4k3/8/8/8/3p4/8/2P1P3/R3K3 w - - 10 20")
    game.play("c2d2")  # sideways pawn step
    assert game.board.halfmove_clock == 0
    game.play("e8e7")
    assert game.board.halfmove_clock == 1
    game.play("e2e3")  # forward pawn move
    assert game.board.halfmove_clock == 0
    game.play("d4e3")  # capture
    assert game.board.halfmove_clock == 0
    game.play("a1a2")
    assert game.board.halfmove_clock == 1
    game.play("e3f3")  # black sideways step
    assert game.board.halfmove_clock == 0


# ------------------------------------------------------------------- notation


def test_notation_disambiguation_ignores_kings_steps():
    game = Game("4k3/8/8/8/8/2N5/8/1N2K3 w - - 0 1")
    notations = {m.uci(): game.board.notation(m, game.legal_moves()) for m in game.legal_moves()}
    assert notations["b1d2"] == "Nd2"  # c3 reaches d2 only by a King's Step
    assert notations["c3d2"] == "Nc3~d2"
    assert notations["b1a3"] == "Na3"


def test_notation_disambiguation_by_file_rank_and_square():
    board = Board("4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1")
    move = next(m for m in board.legal_moves() if m.uci() == "b1d2")
    assert board.notation(move, board.legal_moves()) == "Nbd2"
    board = Board("4k3/8/8/R7/8/8/8/R3K3 w - - 0 1")
    move = next(m for m in board.legal_moves() if m.uci() == "a1a3")
    assert board.notation(move, board.legal_moves()) == "R1a3"
    board = Board("7k/8/8/8/Q1Q5/8/Q7/4K3 w - - 0 1")
    move = next(m for m in board.legal_moves() if m.uci() == "a4b3")
    assert board.notation(move, board.legal_moves()) == "Qa4b3"


def test_history_metadata():
    game = Game.replay(["e2e4", "d7d5", "e4d4", "d8d6", "g1f3", "d6e6", "f3e3"])
    entries = [(p.color, p.piece, p.move.kind, p.captured, p.notation, p.check) for p in game.history]
    assert entries == [
        ("white", "P", "quiet", None, "e4", False),
        ("black", "P", "quiet", None, "d5", False),
        ("white", "P", "pawn_lateral", None, "e4~d4", False),
        ("black", "Q", "quiet", None, "Qd6", False),
        ("white", "N", "quiet", None, "Nf3", False),
        ("black", "Q", "quiet", None, "Qe6+", True),
        ("white", "N", "kings_step", None, "Nf3~e3", False),
    ]


def test_capture_promotion_notation_and_metadata():
    game = Game("3r3k/4P3/8/8/8/8/8/4K3 w - - 0 1")
    played = game.play("e7d8n")
    assert (played.notation, played.captured, played.move.kind, played.move.promotion) == (
        "exd8=N",
        "R",
        "capture",
        "n",
    )


# ------------------------------------------------------------------ FEN / state


@pytest.mark.parametrize(
    "fen",
    [
        STARTING_FEN,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
        "4k3/8/8/8/3p4/8/8/4K3 b - - 17 42",
        "r3k3/8/8/8/8/8/8/4K2R b Kq - 3 9",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 ABCDFGHabcdefgh",
        "4k3/3p4/8/8/8/8/3P4/4K3 b - - 0 3 -",
    ],
)
def test_fen_round_trip(fen):
    assert Board(fen).fen() == fen


def test_fen_carries_double_step_rights():
    game = Game.replay(["e2e4", "a7a6", "d2e2", "a6a5"])
    fen = game.board.fen()
    assert fen == "rnbqkbnr/1ppppppp/8/p7/4P3/8/PPP1PPPP/RNBQKBNR w KQkq - 0 3 ABCFGHbcdefgh"
    restored = Board(fen)
    assert restored.virgin == game.board.virgin
    assert {m.uci() for m in restored.legal_moves()} == {m.uci() for m in game.legal_moves()}
    assert "e2e4" not in {m.uci() for m in restored.legal_moves()}
    # Without the seventh field every pawn on its starting rank keeps the right.
    assert parse_square("e2") in Board(" ".join(fen.split()[:6])).virgin


@pytest.mark.parametrize(
    "fen",
    [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0",  # 5 fields
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN w KQkq - 0 1",  # short rank
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNRR w KQkq - 0 1",  # long rank
        "4k3/8/8/8/8/8/8/8 w - - 0 1",  # no white king
        "4k2P/8/8/8/8/8/8/4K3 w - - 0 1",  # pawn on last rank
        "4k3/8/8/8/8/8/8/4K3 w K - 0 1",  # castling right without rook
        "4k3/8/8/8/8/8/8/4K3 x - - 0 1",  # bad side to move
        "4k3/8/8/8/8/8/8/4K3 w - e3 0 1",  # impossible en passant square
        "4k3/8/8/8/8/8/8/4K2r b - - 0 1",  # side not to move is in check
        "4k3/8/8/8/8/8/8/4K3 w - - -1 1",  # negative clock
        "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1 E",  # double-step right without a pawn
        "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1 DD",  # duplicate file
        "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1 x",  # not a file
        "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1 d",  # black right on an empty d7
        "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1 D -",  # 8 fields
    ],
)
def test_invalid_fen_is_rejected(fen):
    with pytest.raises(ValueError):
        Board(fen)


def test_push_pop_restores_every_position():
    rng = random.Random(7)
    for fen in (STARTING_FEN, "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"):
        board = Board(fen)
        seen = []
        for _ in range(120):
            moves = board.legal_moves()
            if not moves:
                break
            seen.append((board.fen(), board.squares[:], dict(board.kings)))
            board.push(rng.choice(moves))
        while seen:
            board.pop()
            fen_before, squares_before, kings_before = seen.pop()
            assert (board.fen(), board.squares, board.kings) == (fen_before, squares_before, kings_before)


def test_replay_rebuilds_identical_game():
    rng = random.Random(3)
    game = Game()
    while not game.is_over and len(game.history) < 200:
        game.play(rng.choice(game.legal_moves()).uci())
    again = Game.replay([p.move.uci() for p in game.history])
    assert again.board.fen() == game.board.fen()
    assert again.history == game.history
    assert again.outcome() == game.outcome()


def test_legal_moves_are_not_stale_after_a_move():
    game = Game()
    first = game.legal_moves()
    game.play("e2e4")
    assert game.legal_moves() is not first
    assert ucis(game.board) == {m.uci() for m in game.legal_moves()}
