"""Re-check the Asha moments of a run with a bigger search, and keep the puzzles.

A self-play game flags an *Asha moment* when the engine's move is an Asha
move and the best classical move scores far worse (lab/report.py). Those
scores come from two separate small searches, so some flags are noise. This
script searches every flagged position again with more nodes:

* **confirmed**: the bigger search still prefers an Asha move, and the best
  classical move is still an Asha moment's gap worse;
* **puzzle**: confirmed, and the best move is also at least ``UNIQUE_GAP``
  better than the second-best move of any kind, so it has one solution.

It writes <run>/moments.json. Positions the first pass did not flag are not
searched, so the confirmed count can only undercount.

    python -m lab.moments lab/runs/main
"""

from __future__ import annotations

import argparse
import atexit
import json
import multiprocessing
import time
from pathlib import Path

from asha.game import CHECKMATE

from .engine import Engine, is_mate
from .report import DECIDED, MOMENT_GAP, is_asha_moment, load
from .rules import AshaRules, is_asha_kind

UNIQUE_GAP = 150


def replay(moves: list[str]) -> AshaRules:
    rules = AshaRules()
    for uci in moves:
        rules.play(uci)
    return rules


def notation(moves: list[str], line: tuple[str, ...] | list[str]) -> list[str]:
    """Notation of a principal variation, cut where the Asha rules stop it."""
    rules = replay(moves)
    out = []
    for uci in line:
        if rules.result() is not None or uci not in rules.legal():
            break
        out.append(rules.play(uci).notation)
    return out


def check(engine: Engine, game: dict, ply: int, nodes: int) -> dict:
    moves = game["moves"][:ply]
    rules = replay(moves)
    legal = rules.legal()
    fen, history = rules.engine_input()
    both = engine.search("asha", fen, history, nodes=nodes, searchmoves=sorted(legal), multipv=min(2, len(legal)))
    best, second = both.lines[0], (both.lines[1] if len(both.lines) > 1 else None)
    classical_moves = sorted(m for m, k in legal.items() if not is_asha_kind(k))
    classical = (
        engine.search("asha", fen, history, nodes=nodes, searchmoves=classical_moves) if classical_moves else None
    )
    alternative = None if classical is None else classical.score
    confirmed = is_asha_kind(legal[best.move]) and is_asha_moment(best.score, alternative)
    unique = second is not None and best.score - second.score >= UNIQUE_GAP
    in_check = ply > 0 and game["checks"][ply - 1] == "1"
    after = replay(moves)
    piece = after.play(best.move).piece
    tags = []
    if in_check:
        tags.append("answers check")
    if after.game.board.is_check():
        tags.append("gives check")
    if is_mate(best.score) and best.score > 0:
        tags.append("mates")
    elif alternative is not None and alternative <= -DECIDED and best.score > -DECIDED:
        tags.append("saves")
    elif alternative is not None and best.score >= DECIDED and alternative < DECIDED:
        tags.append("wins")
    else:
        tags.append("keeps the balance")
    outcome = after.game.outcome()
    if outcome is not None and outcome.termination == CHECKMATE:
        tags.append("checkmate")
    return {
        "index": game["index"],
        "ply": ply,
        "fen": rules.fen(),
        "to_move": "white" if rules.white_to_move else "black",
        "played": game["moves"][ply],
        "first_pass": {"score": game["scores"][ply], "classical": _alt(game, ply)},
        "best": {
            "move": best.move,
            "kind": legal[best.move],
            "piece": piece,
            "score": best.score,
            "depth": best.depth,
        },
        "solution": notation(moves, best.pv),
        "second": None if second is None else {"move": second.move, "kind": legal[second.move], "score": second.score},
        "classical": None
        if classical is None
        else {"move": classical.bestmove, "score": classical.score, "line": notation(moves, classical.lines[0].pv)},
        "confirmed": confirmed,
        "puzzle": confirmed and unique,
        "tags": tags,
        "nodes": nodes,
    }


def _alt(game: dict, ply: int) -> int | None:
    for p, _move, score in game["alternatives"]:
        if p == ply:
            return score
    raise KeyError(ply)


def candidates(games: list[dict], opening_plies: int) -> list[tuple[dict, int]]:
    out = []
    for game in games:
        if game["variant"] != "asha" or "error" in game:
            continue
        for ply, _move, alternative in game["alternatives"]:
            if ply >= opening_plies and is_asha_moment(game["scores"][ply], alternative):
                out.append((game, ply))
    return out


_engine: Engine | None = None


def _init() -> None:
    global _engine
    _engine = Engine()
    atexit.register(_engine.close)


def _task(args: tuple[dict, int, int]) -> dict:
    assert _engine is not None
    return check(_engine, *args)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--nodes", type=int, help="nodes per search (default: 10 times the run's)")
    parser.add_argument("--workers", type=int, default=max(1, (multiprocessing.cpu_count() or 2) - 2))
    args = parser.parse_args(argv)
    config, games = load(args.run)
    cfg = config["config"]
    nodes = args.nodes or 10 * cfg["nodes"]
    todo = candidates(games, cfg["opening_plies"])
    print(f"{len(todo)} flagged positions, re-searching at {nodes:,} nodes with {args.workers} workers", flush=True)
    started = time.perf_counter()
    with multiprocessing.Pool(args.workers, initializer=_init) as pool:
        results = pool.map(_task, [(game, ply, nodes) for game, ply in todo])
    results.sort(key=lambda r: (r["index"], r["ply"]))
    asha_games = [g for g in games if g["variant"] == "asha" and "error" not in g]
    engine_moves = sum(max(0, g["plies"] - cfg["opening_plies"]) for g in asha_games)
    confirmed = [r for r in results if r["confirmed"]]
    summary = {
        "nodes": nodes,
        "moment_gap": MOMENT_GAP,
        "decided": DECIDED,
        "unique_gap": UNIQUE_GAP,
        "games": len(asha_games),
        "engine_moves": engine_moves,
        "flagged": len(results),
        "confirmed": len(confirmed),
        "puzzles": sum(r["puzzle"] for r in results),
        "games_with_confirmed": len({r["index"] for r in confirmed}),
        "confirmed_per_100_engine_moves": 100 * len(confirmed) / engine_moves if engine_moves else None,
    }
    out = args.run / "moments.json"
    out.write_text(json.dumps({"summary": summary, "moments": results}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(f"wrote {out} in {time.perf_counter() - started:.0f} s")


if __name__ == "__main__":
    main()
