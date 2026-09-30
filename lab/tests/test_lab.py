"""Tests for the lab's pure parts: UCI parsing, referees, per-game numbers, statistics.

pytest lab/tests
"""

from __future__ import annotations

import math

import pytest

from lab.engine import MATE, EngineError, parse_info, parse_search, score_value
from lab.report import Bootstrap, difference, gap, is_asha_moment, playable, ratio, summarize
from lab.rules import AshaRules, ChessRules, phase

# ------------------------------------------------------------------ UCI


def test_score_values_order_mates_above_centipawns():
    assert score_value("cp", -35) == -35
    assert score_value("mate", 1) == MATE - 1
    assert score_value("mate", 3) < score_value("mate", 1)
    assert score_value("mate", -1) == -MATE + 1
    assert score_value("mate", -3) > score_value("mate", -1)
    assert score_value("mate", 0) == -MATE
    assert score_value("mate", 30) > 50_000 > score_value("cp", 5000)
    with pytest.raises(ValueError):
        score_value("wdl", 1)


def test_parse_info_reads_multipv_score_bound_and_pv():
    text = "info depth 12 seldepth 18 multipv 3 score cp -27 upperbound nodes 81234 nps 1 time 9 pv e2e4 e7e5 g1f3"
    index, line, nodes = parse_info(text)
    assert index == 3
    assert (line.move, line.score, line.depth, line.bound) == ("e2e4", -27, 12, "upperbound")
    assert line.pv == ("e2e4", "e7e5", "g1f3")
    assert nodes == 81234


def test_parse_info_ignores_lines_without_a_scored_pv():
    assert parse_info("info depth 3 currmove e2e4 currmovenumber 1") is None
    assert parse_info("info string score pv are words here") is None
    assert parse_info("bestmove e2e4") is None


def test_parse_search_keeps_the_last_line_per_multipv_index():
    output = [
        "info depth 1 multipv 1 score cp 10 nodes 20 pv a2a3",
        "info depth 1 multipv 2 score cp 5 nodes 20 pv h2h3",
        "info depth 2 multipv 1 score mate 2 nodes 90 pv h2h4 a7a6 h4h5",
        "info depth 2 multipv 2 score cp 3 nodes 90 pv a2a3",
        "bestmove h2h4 ponder a7a6",
    ]
    result = parse_search(output)
    assert result.bestmove == "h2h4"
    assert [(line.move, line.score) for line in result.lines] == [("h2h4", MATE - 2), ("a2a3", 3)]
    assert result.nodes == 90 and result.depth == 2


def test_parse_search_rejects_output_without_bestmove_or_lines():
    with pytest.raises(EngineError):
        parse_search(["info depth 1 multipv 1 score cp 10 nodes 20 pv a2a3"])
    with pytest.raises(EngineError):
        parse_search(["bestmove a2a3"])


# -------------------------------------------------------------- referees


def test_phase_boundaries():
    assert phase(14, 0) == "o"
    assert phase(14, 19) == "o"
    assert phase(14, 20) == "m"
    assert phase(10, 3) == "m"
    assert phase(6, 3) == "e"
    assert phase(0, 100) == "e"


def test_both_referees_start_with_the_right_move_counts_and_kinds():
    asha, chess = AshaRules(), ChessRules()
    assert len(asha.legal()) == 34 and len(chess.legal()) == 20
    assert asha.pieces() == chess.pieces() == 14
    assert asha.legal()["e2d3"] == "pawn_diagonal"
    assert chess.legal()["e2e4"] == "quiet"
    assert asha.engine_input() == ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [])


def test_ply_records_agree_between_referees_on_classical_moves():
    asha, chess = AshaRules(), ChessRules()
    for uci in ("e2e4", "d7d5", "e4d5", "d8d5", "b1c3", "d5e5", "f1e2", "e5e2"):
        a, c = asha.play(uci), chess.play(uci)
        assert (a.kind, a.piece, a.capture, a.check) == (c.kind, c.piece, c.capture, c.check)
        assert a.notation == c.notation
    assert asha.play("g1e2").kind == chess.play("g1e2").kind == "capture"


def test_asha_move_records():
    asha = AshaRules()
    ply = asha.play("e2d3")
    assert (ply.kind, ply.piece, ply.capture, ply.check, ply.notation) == ("pawn_diagonal", "P", False, False, "e2~d3")
    asha.play("b8c6")
    assert asha.play("d3e3").notation == "d3~e3"
    ply = asha.play("c6c5")
    assert (ply.kind, ply.piece, ply.notation) == ("kings_step", "N", "Nc6~c5")


def test_scholars_mate_is_mate_in_both_games():
    # Asha adds nothing here: nothing can step between an adjacent queen and the king.
    moves = ("e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7")
    for rules in (ChessRules(), AshaRules()):
        for uci in moves:
            rules.play(uci)
        result = rules.result()
        assert result is not None and (result.termination, result.winner) == ("checkmate", "white")


def test_fools_mate_is_not_mate_in_asha():
    moves = ("f2f3", "e7e5", "g2g4", "d8h4")
    chess, asha = ChessRules(), AshaRules()
    for uci in moves:
        chess.play(uci)
        asha.play(uci)
    assert chess.result().termination == "checkmate"
    assert asha.result() is None
    assert {"g1f2", "f1f2", "e2f2", "f3g3", "h2g3"} <= {m for m in asha.legal()}


def test_threefold_repetition_is_claimed_by_both_referees():
    shuffle = ("g1f3", "g8f6", "f3g1", "f6g8") * 2
    for rules in (AshaRules(), ChessRules()):
        for uci in shuffle:
            assert rules.result() is None
            rules.play(uci)
        result = rules.result()
        assert result is not None and result.termination == "threefold_repetition" and result.winner is None


# ------------------------------------------------------ per-game numbers


def test_playable_uses_the_margin_inclusively():
    lines = [("a", 50), ("b", 20), ("c", 19), ("d", -100)]
    assert playable(lines, 30) == ["a", "b"]
    assert playable(lines, 0) == ["a"]
    assert playable(lines, 1000) == ["a", "b", "c", "d"]


def test_asha_moment_needs_a_large_gap_in_an_undecided_position():
    assert is_asha_moment(0, -200)
    assert not is_asha_moment(0, -199)
    assert not is_asha_moment(900, 400)  # the classical move still wins clearly
    assert not is_asha_moment(-400, -800)  # lost either way
    assert is_asha_moment(MATE - 3, 0)  # the Asha move mates, the classical one does not
    assert not is_asha_moment(MATE - 3, MATE - 5)  # both mate
    assert is_asha_moment(10, None)  # only Asha moves were legal
    assert gap(10, None) == math.inf


def _game(**overrides):
    game = {
        "variant": "asha",
        "plies": 6,
        "winner": "white",
        "moves": ["e2d3", "e7e5", "g1f3", "b8c6", "f3e3", "c6d4"],
        "kinds": ["pawn_diagonal", "quiet", "quiet", "quiet", "kings_step", "quiet"],
        "pieces": "PPNNNN",
        "captures": "000001",
        "checks": "000100",
        "phases": "oooomm",
        "scores": [10, 0, 5, 0, 40, -250],
        "depths": [10, 10, 7, 8, 9, 9],
        "opening": [
            {"lines": [["e2d3", 30], ["e2e4", 20], ["a2a3", -40]], "asha": ["e2d3"]},
            {"lines": [["e7e5", 0], ["d7d5", -40]], "asha": []},
        ],
        "alternatives": [[0, "e2e4", 20], [4, "f3g5", -200]],
    }
    game.update(overrides)
    return game


def test_summarize_counts_moves_phases_and_moments():
    s = summarize(_game(), opening_plies=2, margin=30)
    assert s["white_wins"] and not s["draws"] and s["white_points"] == 1 and s["decisive"]
    assert s["moves"] == 6 and s["asha_moves"] == 2
    assert s["moves_o"] == 4 and s["asha_moves_o"] == 1 and s["moves_m"] == 2 and s["asha_moves_m"] == 1
    assert s["kind_pawn_diagonal"] == 1 and s["kind_kings_step_N"] == 1
    assert s["engine_moves"] == 4 and s["engine_asha_moves"] == 1 and s["depth"] == 33
    assert s["evasions"] == 1 and s["asha_evasions"] == 1  # f3e3 answered the check given by b8c6
    assert s["captures"] == 1 and s["first_capture_move"] == 3
    # The opening Asha move at ply 0 is not an engine move, so only ply 4 counts: 40 vs -200.
    assert s["gap_100"] == 1 and s["gap_200"] == 1 and s["moments"] == 1 and s["games_with_moment"]
    assert s["playable_30_0"] == 2 and s["playable_30_1"] == 1
    assert s["playable_asha_30"] == 1 and s["playable_30"] == 3
    assert s["knuth"] == 2 and s["full_opening"] == 1


def test_summarize_draw_and_short_opening():
    s = summarize(_game(winner=None, opening=_game()["opening"][:1]), opening_plies=2, margin=30)
    assert s["draws"] and s["white_points"] == 0.5 and not s["decisive"]
    assert "knuth" not in s and "full_opening" not in s


# ------------------------------------------------------------ statistics


def test_ratio_and_bootstrap_interval_contain_the_estimate():
    rows = [{"x": i % 2, "n": 1} for i in range(200)]
    assert ratio(rows, "x", "n") == 0.5
    assert math.isnan(ratio(rows, "x", "missing"))
    boot = Bootstrap(rows, 500, "seed")
    estimate = boot.estimate("x", "n")
    assert estimate.value == 0.5 and 0.4 < estimate.low < 0.5 < estimate.high < 0.6
    assert Bootstrap(rows, 500, "seed").estimate("x", "n") == estimate  # seeded


def test_difference_of_identical_samples_is_centred_on_zero():
    rows = [{"x": i % 3 == 0, "n": 1} for i in range(300)]
    d = difference(Bootstrap(rows, 400, "a"), Bootstrap(rows, 400, "b"), "x", "n")
    assert d.value == 0 and d.low < 0 < d.high
