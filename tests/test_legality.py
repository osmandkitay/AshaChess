"""King safety: pins, checks, castling and en passant under Asha movement."""

from asha import CASTLING, EN_PASSANT, KINGS_STEP, PAWN_DIAGONAL, PAWN_LATERAL, QUIET, Board, Game, parse_square
from tests.helpers import targets, ucis

# ---------------------------------------------------------------------- pins


def test_pinned_rook_may_only_slide_along_the_pin():
    moves = targets("4r2k/8/8/8/8/8/4R3/4K3 w - - 0 1", "e2")
    assert set(moves) == {"e3", "e4", "e5", "e6", "e7", "e8"}
    assert KINGS_STEP not in moves.values()


def test_pinned_bishop_may_only_capture_the_pinner():
    assert targets("7k/8/8/8/8/2b5/3B4/4K3 w - - 0 1", "d2") == {"c3": "capture"}


def test_pinned_knight_may_only_kings_step_along_the_pin():
    # No jump keeps the file blocked, but the step to e3 does.
    assert targets("4r2k/8/8/8/8/8/4N3/4K3 w - - 0 1", "e2") == {"e3": KINGS_STEP}
    # Pinned diagonally: the only free square on the line is the pinner on c3,
    # which neither a jump nor a (non-capturing) step can take.
    assert targets("7k/8/8/8/8/2b5/3N4/4K3 w - - 0 1", "d2") == {}


def test_pinned_pawn_cannot_step_sideways_or_diagonally_off_the_pin_line():
    assert targets("4r2k/8/8/8/8/8/4P3/4K3 w - - 0 1", "e2") == {"e3": QUIET, "e4": QUIET}


def test_pawn_pinned_along_its_rank_may_step_sideways_along_the_pin():
    # Rook a5, pawn d5, king e5: stepping to c5 keeps the line blocked.
    assert targets("7k/8/8/r2PK3/8/8/8/8 w - - 0 1", "d5") == {"c5": PAWN_LATERAL}


def test_pawn_pinned_diagonally_may_step_diagonally_along_the_pin():
    # King a1, pawn b2, bishop e5: only the non-capturing step to c3 stays on the line.
    assert targets("7k/8/8/4b3/8/8/1P6/K7 w - - 0 1", "b2") == {"c3": PAWN_DIAGONAL}
    # With the bishop on c3 the same square is a classical capture instead.
    assert targets("7k/8/8/8/8/2b5/1P6/K7 w - - 0 1", "b2") == {"c3": "capture"}


# --------------------------------------------------------------------- checks


def test_kings_step_can_give_direct_check():
    game = Game("8/7k/8/8/8/8/P7/K1B5 w - - 0 1")
    played = game.play("c1c2")
    assert played.move.kind == KINGS_STEP
    assert game.board.is_check()
    assert played.notation == "Bc1~c2+"


def test_pawn_sideways_step_can_give_check():
    game = Game("8/8/8/3k4/1P6/8/8/K7 w - - 0 1")
    played = game.play("b4c4")
    assert played.move.kind == PAWN_LATERAL
    assert played.check and played.notation == "b4~c4+"


def test_pawn_diagonal_step_can_give_check():
    game = Game("8/8/5k2/8/3P4/8/8/K7 w - - 0 1")
    played = game.play("d4e5")
    assert played.move.kind == PAWN_DIAGONAL
    assert played.check and played.notation == "d4~e5+"


def test_kings_step_can_give_discovered_check():
    game = Game("4k3/8/8/8/4N3/8/8/K3R3 w - - 0 1")
    played = game.play("e4d4")
    assert played.move.kind == KINGS_STEP
    assert played.notation == "Ne4~d4+"


def test_double_check_allows_only_king_moves():
    # Rook e1 and knight d6 both check; bishop c7 could take d6 and knight f6
    # could interpose with a King's Step on e6, but neither answers both checks.
    board = Board("4k3/2b5/3N1n2/8/8/8/8/K3R3 b - - 0 1")
    assert board.is_check()
    assert ucis(board) == {"e8d8", "e8f8", "e8d7"}


def test_check_can_be_blocked_by_kings_step():
    assert targets("4k3/8/8/3b4/8/8/8/K3R3 b - - 0 1", "d5") == {"e4": QUIET, "e6": QUIET, "e5": KINGS_STEP}


def test_check_can_be_blocked_by_pawn_sideways_or_diagonal_step():
    assert targets("4k3/8/3p4/8/8/8/8/K3R3 b - - 0 1", "d6") == {"e6": PAWN_LATERAL, "e5": PAWN_DIAGONAL}


def test_kings_step_cannot_capture_the_checking_piece():
    assert targets("4k3/8/8/3nR3/8/8/8/K7 b - - 0 1", "d5") == {"e6": KINGS_STEP, "e7": QUIET}


def test_no_move_may_leave_own_king_in_check():
    board = Board("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    white_king = board.kings[True]
    for move in board.legal_moves():
        board.push(move)
        assert not board.is_attacked(board.kings[True], False), move.uci()
        board.pop()
    assert board.kings[True] == white_king


def test_king_cannot_walk_into_attack_or_next_to_enemy_king():
    moves = targets("8/8/8/3k4/8/3K4/7r/8 w - - 0 1", "d3")
    assert set(moves) == {"c3", "e3"}


# ------------------------------------------------------------------- castling

CASTLE_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"


def test_castling_both_sides():
    moves = targets(CASTLE_FEN, "e1")
    assert moves["g1"] == CASTLING and moves["c1"] == CASTLING


def test_castling_rook_is_moved():
    game = Game(CASTLE_FEN)
    assert game.play("e1g1").notation == "O-O"
    assert game.board.piece_at(parse_square("f1")) == "R"
    assert game.board.piece_at(parse_square("h1")) is None
    assert game.play("e8c8").notation == "O-O-O"
    assert game.board.piece_at(parse_square("d8")) == "r"
    assert game.board.castling == ""


def test_no_castling_through_or_into_attacked_square():
    assert "g1" not in targets("r3k2r/8/8/5r2/8/8/8/R3K2R w KQkq - 0 1", "e1")  # f1 attacked
    assert "g1" not in targets("r3k2r/8/8/6r1/8/8/8/R3K2R w KQkq - 0 1", "e1")  # g1 attacked
    assert "c1" not in targets("r3k2r/8/8/3r4/8/8/8/R3K2R w KQkq - 0 1", "e1")  # d1 attacked


def test_queenside_castling_allowed_when_only_b1_is_attacked():
    assert targets("r3k2r/8/8/1r6/8/8/8/R3K2R w KQkq - 0 1", "e1")["c1"] == CASTLING


def test_no_castling_out_of_check():
    moves = targets("r3k2r/8/8/4r3/8/8/8/R3K2R w KQkq - 0 1", "e1")
    assert "g1" not in moves and "c1" not in moves


def test_no_castling_with_piece_in_between():
    assert "c1" not in targets("r3k2r/8/8/8/8/8/8/RN2K2R w KQkq - 0 1", "e1")


def test_rook_kings_step_away_and_back_loses_castling_right():
    game = Game(CASTLE_FEN)
    assert game.play("h1g2").move.kind == KINGS_STEP
    game.play("a8a7")
    game.play("g2h1")
    game.play("a7a8")
    assert game.board.castling == "Qk"
    assert "e1g1" not in {m.uci() for m in game.legal_moves()}


def test_capturing_a_rook_removes_its_castling_right():
    game = Game("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    game.play("a1a8")
    assert game.board.castling == "Kk"


# ----------------------------------------------------------------- en passant


def test_en_passant_capture():
    game = Game("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
    move = next(m for m in game.legal_moves() if m.uci() == "e5d6")
    assert move.kind == EN_PASSANT
    played = game.play("e5d6")
    assert played.notation == "exd6" and played.captured == "P"
    assert game.board.piece_at(parse_square("d5")) is None
    assert game.board.piece_at(parse_square("d6")) == "P"


def test_en_passant_right_expires_after_one_move():
    game = Game("4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1")
    game.play("d7d5")
    assert targets(game.board.fen(), "e5")["d6"] == EN_PASSANT
    game.play("e1e2")
    game.play("e8f7")
    # Later the same square is only a non-capturing diagonal step: d5 survives.
    assert targets(game.board.fen(), "e5")["d6"] == PAWN_DIAGONAL
    played = game.play("e5d6")
    assert played.captured is None and played.notation == "e5~d6"
    assert game.board.piece_at(parse_square("d5")) == "p"


def test_diagonal_move_onto_the_en_passant_square_is_the_en_passant_capture():
    moves = targets("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", "e5")
    assert moves == {"d6": EN_PASSANT, "e6": QUIET, "f6": PAWN_DIAGONAL, "f5": PAWN_LATERAL}


def test_sideways_step_next_to_a_pawn_creates_no_en_passant():
    game = Game("4k3/8/8/2p1P3/8/8/8/4K3 b - - 0 1")
    game.play("c5d5")
    assert targets(game.board.fen(), "e5") == {
        "e6": QUIET,
        "f5": PAWN_LATERAL,
        "d6": PAWN_DIAGONAL,
        "f6": PAWN_DIAGONAL,
    }


def test_en_passant_that_exposes_own_king_is_illegal():
    # Capturing removes both pawns from the fifth rank and opens the rook's line.
    board = Board("8/8/8/K2pP2r/8/8/8/7k w - d6 0 2")
    assert "e5d6" not in ucis(board)
    assert board.fen().split()[3] == "-"


def test_black_en_passant():
    game = Game("4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1")
    game.play("e2e4")
    assert game.board.fen().split()[3] == "e3"
    played = game.play("d4e3")
    assert played.move.kind == EN_PASSANT
    assert game.board.piece_at(parse_square("e4")) is None
