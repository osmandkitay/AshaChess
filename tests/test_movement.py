"""Movement and capture geometry of every piece type."""

import pytest

from asha import (
    ASHA_KINDS,
    CAPTURE,
    KINGS_STEP,
    PAWN_DIAGONAL,
    PAWN_LATERAL,
    QUIET,
    STARTING_FEN,
    Board,
    Game,
    parse_square,
)
from tests.helpers import targets, ucis

# ------------------------------------------------------------ start position


def test_start_position_has_34_moves_including_14_diagonal_pawn_steps():
    board = Board(STARTING_FEN)
    classical = {f"{f}2{f}3" for f in "abcdefgh"} | {f"{f}2{f}4" for f in "abcdefgh"}
    classical |= {"b1a3", "b1c3", "g1f3", "g1h3"}
    diagonal = {f"{f}2{g}3" for f in "abcdefgh" for g in "abcdefgh" if abs(ord(f) - ord(g)) == 1}
    moves = board.legal_moves()
    assert len(moves) == 34 and len(diagonal) == 14
    assert ucis(board) == classical | diagonal
    assert {m.uci() for m in moves if m.kind == PAWN_DIAGONAL} == diagonal
    assert {m.kind for m in moves if m.is_asha} == {PAWN_DIAGONAL}


def test_black_reply_to_every_first_move_has_34_moves():
    # Sideways and King's Step squares are all occupied; only Black's 14
    # diagonal pawn steps onto the empty sixth rank are added.
    board = Board(STARTING_FEN)
    for move in board.legal_moves():
        board.push(move)
        moves = board.legal_moves()
        assert len(moves) == 34
        assert {m.kind for m in moves if m.is_asha} == {PAWN_DIAGONAL}
        board.pop()


# ---------------------------------------------------------------------- pawn


def test_white_pawn_on_start_rank():
    assert targets("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "e2") == {
        "e3": QUIET,
        "e4": QUIET,
        "d2": PAWN_LATERAL,
        "f2": PAWN_LATERAL,
        "d3": PAWN_DIAGONAL,
        "f3": PAWN_DIAGONAL,
    }


def test_black_pawn_on_start_rank():
    assert targets("4k3/4p3/8/8/8/8/8/4K3 b - - 0 1", "e7") == {
        "e6": QUIET,
        "e5": QUIET,
        "d7": PAWN_LATERAL,
        "f7": PAWN_LATERAL,
        "d6": PAWN_DIAGONAL,
        "f6": PAWN_DIAGONAL,
    }


def test_pawn_moves_forward_sideways_and_diagonally_forward_but_never_backward():
    moves = targets("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1", "e4")
    assert moves == {"e5": QUIET, "d4": PAWN_LATERAL, "f4": PAWN_LATERAL, "d5": PAWN_DIAGONAL, "f5": PAWN_DIAGONAL}
    for forbidden in ("e3", "d3", "f3", "c4", "g4", "e6", "c5", "g5"):
        assert forbidden not in moves


def test_black_pawn_never_moves_backward():
    moves = targets("4k3/8/8/4p3/8/8/8/4K3 b - - 0 1", "e5")
    assert moves == {"e4": QUIET, "d5": PAWN_LATERAL, "f5": PAWN_LATERAL, "d4": PAWN_DIAGONAL, "f4": PAWN_DIAGONAL}
    for forbidden in ("e6", "d6", "f6"):
        assert forbidden not in moves


def test_pawn_never_moves_backward_even_when_every_forward_square_is_blocked():
    assert targets("4k3/8/8/3NNN2/3NPN2/8/8/4K3 w - - 0 1", "e4") == {}
    assert targets("4k3/8/8/8/3npn2/3nnn2/8/7K b - - 0 1", "e4") == {}


def test_pawn_forward_blocked_still_allows_sideways_and_diagonal_steps():
    # A pawn cannot capture straight ahead.
    assert targets("4k3/8/8/4p3/4P3/8/8/4K3 w - - 0 1", "e4") == {
        "d4": PAWN_LATERAL,
        "f4": PAWN_LATERAL,
        "d5": PAWN_DIAGONAL,
        "f5": PAWN_DIAGONAL,
    }


def test_double_push_needs_both_squares_empty():
    assert "e4" not in targets("4k3/8/8/8/4p3/8/4P3/4K3 w - - 0 1", "e2")
    assert targets("4k3/8/8/8/8/4n3/4P3/4K3 w - - 0 1", "e2") == {
        "d2": PAWN_LATERAL,
        "f2": PAWN_LATERAL,
        "d3": PAWN_DIAGONAL,
        "f3": PAWN_DIAGONAL,
    }


def test_pawn_sideways_step_cannot_capture_or_enter_occupied_square():
    # d4 holds an enemy pawn, f4 a friendly knight.
    assert targets("4k3/8/8/8/3pPN2/8/8/4K3 w - - 0 1", "e4") == {
        "e5": QUIET,
        "d5": PAWN_DIAGONAL,
        "f5": PAWN_DIAGONAL,
    }


def test_pawn_never_captures_straight_ahead_or_sideways():
    # Enemies on e5, d4 and f4 cannot be taken; d5 and f5 are empty.
    assert targets("4k3/8/8/4r3/3nPb2/8/8/K7 w - - 0 1", "e4") == {"d5": PAWN_DIAGONAL, "f5": PAWN_DIAGONAL}
    assert targets("7k/8/8/8/3NpB2/4R3/8/K7 b - - 0 1", "e4") == {"d3": PAWN_DIAGONAL, "f3": PAWN_DIAGONAL}


def test_diagonal_step_onto_an_enemy_is_a_capture_and_onto_an_own_piece_is_impossible():
    moves = targets("4k3/8/8/3p1N2/4P3/8/8/4K3 w - - 0 1", "e4")
    assert moves == {"d5": CAPTURE, "e5": QUIET, "d4": PAWN_LATERAL, "f4": PAWN_LATERAL}


def test_pawn_sideways_step_is_exactly_one_square():
    moves = targets("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1", "e4")
    assert "c4" not in moves and "g4" not in moves


def test_pawns_on_edge_files():
    fen = "4k3/8/8/8/P6P/8/8/4K3 w - - 0 1"
    assert targets(fen, "a4") == {"a5": QUIET, "b4": PAWN_LATERAL, "b5": PAWN_DIAGONAL}
    assert targets(fen, "h4") == {"h5": QUIET, "g4": PAWN_LATERAL, "g5": PAWN_DIAGONAL}


def test_pawn_captures_only_diagonally_forward():
    moves = targets("4k3/8/8/3p1n2/4P3/3r1b2/8/4K3 w - - 0 1", "e4")
    assert moves == {"d5": CAPTURE, "f5": CAPTURE, "e5": QUIET, "d4": PAWN_LATERAL, "f4": PAWN_LATERAL}


def test_black_pawn_captures_only_diagonally_forward():
    moves = targets("4k3/8/3R1B2/4p3/3N4/8/8/4K3 b - - 0 1", "e5")
    assert moves == {"d4": CAPTURE, "e4": QUIET, "f4": PAWN_DIAGONAL, "d5": PAWN_LATERAL, "f5": PAWN_LATERAL}


def test_pawn_does_not_capture_own_piece():
    assert "d5" not in targets("4k3/8/8/3N4/4P3/8/8/4K3 w - - 0 1", "e4")


def test_pawn_has_no_kings_step():
    board = Board("4k3/8/8/8/4P3/8/8/4K3 w - - 0 1")
    assert all(m.kind != KINGS_STEP for m in board.legal_moves())


def test_white_promotion_offers_all_four_pieces_and_diagonal_steps_promote_but_sideways_steps_do_not():
    moves = targets("k2r4/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7")
    assert moves == {
        "e8q": QUIET, "e8r": QUIET, "e8b": QUIET, "e8n": QUIET,
        "d8q": CAPTURE, "d8r": CAPTURE, "d8b": CAPTURE, "d8n": CAPTURE,
        "f8q": PAWN_DIAGONAL, "f8r": PAWN_DIAGONAL, "f8b": PAWN_DIAGONAL, "f8n": PAWN_DIAGONAL,
        "d7": PAWN_LATERAL, "f7": PAWN_LATERAL,
    }  # fmt: skip


def test_black_promotion():
    moves = targets("4k3/8/8/8/8/8/3p4/K7 b - - 0 1", "d2")
    assert moves == {
        "d1q": QUIET, "d1r": QUIET, "d1b": QUIET, "d1n": QUIET,
        "c1q": PAWN_DIAGONAL, "c1r": PAWN_DIAGONAL, "c1b": PAWN_DIAGONAL, "c1n": PAWN_DIAGONAL,
        "e1q": PAWN_DIAGONAL, "e1r": PAWN_DIAGONAL, "e1b": PAWN_DIAGONAL, "e1n": PAWN_DIAGONAL,
        "c2": PAWN_LATERAL, "e2": PAWN_LATERAL,
    }  # fmt: skip


def test_diagonal_step_promotion_requires_a_piece_choice():
    game = Game("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
    with pytest.raises(ValueError):
        game.play("e7f8")
    played = game.play("e7f8q")
    assert game.board.piece_at(parse_square("f8")) == "Q"
    assert (played.move.kind, played.captured, played.notation) == (PAWN_DIAGONAL, None, "e7~f8=Q+")


def test_underpromotion_places_chosen_piece():
    game = Game("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
    played = game.play("e7e8n")
    assert game.board.piece_at(parse_square("e8")) == "N"
    assert played.notation == "e8=N"
    assert played.move.promotion == "n"


def test_promotion_requires_a_piece_choice():
    game = Game("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
    with pytest.raises(ValueError):
        game.play("e7e8")
    with pytest.raises(ValueError):
        game.play("e7e8k")


def test_sideways_step_on_seventh_rank_keeps_a_pawn():
    game = Game("k7/4P3/8/8/8/8/8/4K3 w - - 0 1")
    game.play("e7d7")
    assert game.board.piece_at(parse_square("d7")) == "P"


def test_sideways_step_on_the_start_rank_spends_the_double_step():
    game = Game("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    game.play("e2d2")
    game.play("e8e7")
    assert targets(game.board.fen(), "d2") == {
        "d3": QUIET,
        "c2": PAWN_LATERAL,
        "e2": PAWN_LATERAL,
        "c3": PAWN_DIAGONAL,
        "e3": PAWN_DIAGONAL,
    }
    assert "d2d4" not in {m.uci() for m in game.legal_moves()}
    # Returning to the original square does not restore the right.
    game.play("d2e2")
    game.play("e7e8")
    assert targets(game.board.fen(), "e2") == {
        "e3": QUIET,
        "d2": PAWN_LATERAL,
        "f2": PAWN_LATERAL,
        "d3": PAWN_DIAGONAL,
        "f3": PAWN_DIAGONAL,
    }


def test_black_sideways_step_spends_the_double_step():
    game = Game("4k3/3p4/8/8/8/8/8/4K3 b - - 0 1")
    game.play("d7c7")
    game.play("e1e2")
    assert targets(game.board.fen(), "c7") == {
        "c6": QUIET,
        "b7": PAWN_LATERAL,
        "d7": PAWN_LATERAL,
        "b6": PAWN_DIAGONAL,
        "d6": PAWN_DIAGONAL,
    }


@pytest.mark.parametrize(
    ("fen", "uci"),
    [
        ("4k3/8/8/8/8/8/4P3/4K3 w - - 7 1", "e2d3"),
        ("4k3/4p3/8/8/8/8/8/4K3 b - - 7 1", "e7f6"),
    ],
)
def test_diagonal_step_spends_the_double_step_and_resets_the_clock(fen, uci):
    game = Game(fen)
    assert game.board.virgin == {parse_square(uci[:2])}
    played = game.play(uci)
    assert played.move.kind == PAWN_DIAGONAL and played.notation == f"{uci[:2]}~{uci[2:]}"
    assert game.board.virgin == frozenset()
    assert game.board.halfmove_clock == 0
    assert game.board.ep_square is None  # only the two-square push creates en passant


def test_other_pawns_keep_their_double_step():
    game = Game.replay(["e2e4", "a7a6", "e4d4", "a6a5"])
    assert {"d2d3", "c2c4", "f2f4"} <= {m.uci() for m in game.legal_moves()}
    game = Game.replay(["e2e4", "a7a6", "e4e5", "a6a5", "d2e2", "a5a4"])
    moves = {m.uci() for m in game.legal_moves()}
    assert "e2e3" in moves and "c2c4" in moves and "e2e4" not in moves


# -------------------------------------------------------------------- knight


def test_knight_classical_jumps_plus_kings_step():
    moves = targets("4k3/8/8/8/3N4/8/8/4K3 w - - 0 1", "d4")
    jumps = {"b3", "b5", "c2", "c6", "e2", "e6", "f3", "f5"}
    steps = {"c3", "c4", "c5", "d3", "d5", "e3", "e4", "e5"}
    assert moves == {**dict.fromkeys(jumps, QUIET), **dict.fromkeys(steps, KINGS_STEP)}


def test_knight_captures_only_with_its_jump():
    moves = targets("4k3/8/2p5/3p4/3N4/8/8/4K3 w - - 0 1", "d4")
    assert moves["c6"] == CAPTURE
    assert "d5" not in moves  # adjacent enemy cannot be taken by a King's Step


def test_knight_in_corner():
    assert targets("4k3/8/8/8/8/8/8/N3K3 w - - 0 1", "a1") == {
        "b3": QUIET,
        "c2": QUIET,
        "a2": KINGS_STEP,
        "b1": KINGS_STEP,
        "b2": KINGS_STEP,
    }


# -------------------------------------------------------------------- bishop


def test_bishop_classical_diagonals_plus_orthogonal_kings_step():
    moves = targets("4k3/8/8/8/3B4/8/8/4K3 w - - 0 1", "d4")
    diagonals = {"a1", "b2", "c3", "e5", "f6", "g7", "h8", "a7", "b6", "c5", "e3", "f2", "g1"}
    steps = {"d3", "d5", "c4", "e4"}
    assert moves == {**dict.fromkeys(diagonals, QUIET), **dict.fromkeys(steps, KINGS_STEP)}


def test_bishop_changes_square_colour_with_kings_step():
    game = Game("4k3/8/8/8/3B4/8/P7/4K3 w - - 0 1")
    before = parse_square("d4")
    game.play("d4d5")
    after = parse_square("d5")
    assert game.board.piece_at(after) == "B"
    assert ((before & 7) + (before >> 3)) % 2 != ((after & 7) + (after >> 3)) % 2


def test_bishop_captures_only_diagonally():
    moves = targets("4k3/8/5r2/3p4/3B4/8/8/4K3 w - - 0 1", "d4")
    assert moves["f6"] == CAPTURE
    assert "d5" not in moves
    assert "g7" not in moves and "h8" not in moves  # blocked beyond the capture


# ---------------------------------------------------------------------- rook


def test_rook_classical_lines_plus_diagonal_kings_step():
    moves = targets("4k3/8/8/8/3R4/8/8/4K3 w - - 0 1", "d4")
    lines = {"d1", "d2", "d3", "d5", "d6", "d7", "d8", "a4", "b4", "c4", "e4", "f4", "g4", "h4"}
    steps = {"c3", "c5", "e3", "e5"}
    assert moves == {**dict.fromkeys(lines, QUIET), **dict.fromkeys(steps, KINGS_STEP)}


def test_rook_captures_only_orthogonally():
    moves = targets("4k3/8/8/2p5/3Rp3/8/8/4K3 w - - 0 1", "d4")
    assert moves["e4"] == CAPTURE
    assert "c5" not in moves
    assert "f4" not in moves


# ------------------------------------------------------------- king / queen


def test_queen_gains_nothing():
    moves = targets("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1", "d4")
    assert len(moves) == 27
    assert set(moves.values()) == {QUIET}


def test_king_gains_nothing():
    moves = targets("4k3/8/8/8/3K4/8/8/8 w - - 0 1", "d4")
    assert set(moves) == {"c3", "c4", "c5", "d3", "d5", "e3", "e4", "e5"}
    assert set(moves.values()) == {QUIET}


# ----------------------------------------------------- occupied destinations


@pytest.mark.parametrize(
    ("piece", "captures"),
    [
        ("N", set()),
        ("B", {"c3", "e3", "c5", "e5"}),
        ("R", {"d3", "c4", "e4", "d5"}),
    ],
)
def test_kings_step_never_enters_an_enemy_occupied_square(piece, captures):
    fen = f"7k/8/8/2ppp3/2p{piece}p3/2ppp3/8/7K w - - 0 1"
    moves = targets(fen, "d4")
    assert KINGS_STEP not in moves.values()
    assert {sq for sq, kind in moves.items() if kind == CAPTURE} == captures


@pytest.mark.parametrize("piece", ["N", "B", "R"])
def test_kings_step_never_enters_an_own_occupied_square(piece):
    fen = f"7k/8/8/2PPP3/2P{piece}P3/2PPP3/8/7K w - - 0 1"
    moves = targets(fen, "d4")
    assert KINGS_STEP not in moves.values()
    if piece == "N":
        assert set(moves) == {"b3", "b5", "c2", "c6", "e2", "e6", "f3", "f5"}
    else:
        assert moves == {}


def test_asha_moves_never_capture():
    board = Board("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    for move in board.legal_moves():
        if move.kind in ASHA_KINDS:
            assert board.piece_at(move.to_sq) is None
