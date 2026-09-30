"""Engine self-play for Asha Chess and, as the control, classical chess.

The same engine (the Fairy-Stockfish WebAssembly build the game ships), the
same settings and the same procedure play both games:

1. Opening (the first ``--opening-plies`` half-moves): every legal move is
   scored with a MultiPV search to ``--opening-depth``. A move counts as
   *playable* when it scores within ``--margin`` centipawns of the best, and
   one playable move is chosen at random (seeded). This makes the games
   differ from each other and measures how many good choices a player has.
2. Afterwards the engine plays its best move at ``--nodes`` nodes per move.
   Whenever that move is an Asha move (King's Step, pawn sideways or diagonal
   step), a second search restricted to the classical moves scores the best
   classical alternative, so the report can tell how often only an Asha move
   keeps the evaluation.

Games are refereed by the ``asha`` package and python-chess, and end under
the rules in lab/rules.py. Each search starts from a cleared engine, so a
game depends only on its seed and the settings: rerunning a run reproduces
it move for move.

Results go to <out>/games.jsonl (one game per line, appended as games finish,
so an interrupted run resumes where it stopped) and <out>/run.json.

    python -m lab.selfplay --games 500 --out lab/runs/main
"""

from __future__ import annotations

import argparse
import atexit
import json
import multiprocessing
import platform
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import chess

from .engine import Engine, EngineError, SearchResult
from .rules import RULES, Result, is_asha_kind, phase

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    variants: tuple[str, ...] = ("asha", "chess")
    games: int = 100  # per variant
    nodes: int = 20_000
    opening_plies: int = 8
    opening_depth: int = 10
    margin: int = 30
    max_plies: int = 600
    hash_mb: int = 16
    seed: int = 1


class LabError(RuntimeError):
    pass


def play_game(engine: Engine, config: Config, variant: str, index: int, cache: dict | None = None) -> dict:
    rng = random.Random(f"{config.seed}:{variant}:{index}")
    rules = RULES[variant]()
    moves: list[str] = []
    notation, kinds, pieces, captures, checks, phases = [], [], [], [], [], []
    scores: list[int] = []
    depths: list[int] = []
    opening: list[dict] = []
    alternatives: list[list] = []  # [ply, best classical move or None, its score or None]
    started = time.perf_counter()
    result: Result | None = None
    error = None
    try:
        while True:
            result = rules.result()
            if result is not None:
                break
            if len(moves) >= config.max_plies:
                result = Result("ply_cap", None)
                break
            ply = len(moves)
            legal = rules.legal()
            fen, history = rules.engine_input()
            searchmoves = sorted(legal)
            phases.append(phase(rules.pieces(), ply))
            if ply < config.opening_plies:
                search = _opening_search(engine, cache, variant, fen, history, config.opening_depth, searchmoves)
                # Best first; the stable sort keeps the engine's order among equal scores.
                ranked = sorted(((line.move, line.score) for line in search.lines), key=lambda x: -x[1])
                if sorted(m for m, _ in ranked) != searchmoves:
                    raise LabError(f"MultiPV did not score every legal move at ply {ply}")
                best = ranked[0][1]
                playable = sorted(m for m, s in ranked if s >= best - config.margin)
                move = rng.choice(playable)
                score = dict(ranked)[move]
                depth = search.depth
                opening.append({"lines": ranked, "asha": [m for m, _ in ranked if is_asha_kind(legal[m])]})
                if is_asha_kind(legal[move]):
                    classical = [(m, s) for m, s in ranked if not is_asha_kind(legal[m])]
                    alternatives.append([ply, *classical[0]] if classical else [ply, None, None])
            else:
                search = engine.search(variant, fen, history, nodes=config.nodes, searchmoves=searchmoves)
                move = _checked(search, legal, ply)
                score, depth = search.score, search.depth
                if is_asha_kind(legal[move]):
                    classical = sorted(m for m, k in legal.items() if not is_asha_kind(k))
                    if classical:
                        alt = engine.search(variant, fen, history, nodes=config.nodes, searchmoves=classical)
                        alternatives.append([ply, _checked(alt, legal, ply), alt.score])
                    else:
                        alternatives.append([ply, None, None])
            played = rules.play(move)
            moves.append(move)
            notation.append(played.notation)
            kinds.append(played.kind)
            pieces.append(played.piece)
            captures.append("1" if played.capture else "0")
            checks.append("1" if played.check else "0")
            scores.append(score)
            depths.append(depth)
    except (EngineError, LabError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
        result = None
    record = {
        "variant": variant,
        "index": index,
        "result": result.score if result else None,
        "winner": result.winner if result else None,
        "termination": result.termination if result else "error",
        "plies": len(moves),
        "moves": moves,
        "notation": notation,
        "kinds": kinds,
        "pieces": "".join(pieces),
        "captures": "".join(captures),
        "checks": "".join(checks),
        "phases": "".join(phases[: len(moves)]),
        "scores": scores,
        "depths": depths,
        "opening": opening,
        "alternatives": alternatives,
        "seconds": round(time.perf_counter() - started, 2),
    }
    if error:
        record["error"] = error
    return record


def _checked(search: SearchResult, legal: dict[str, str], ply: int) -> str:
    if search.bestmove not in legal:
        raise LabError(f"engine chose {search.bestmove!r}, not a legal move, at ply {ply}")
    if search.lines[0].move != search.bestmove:
        raise LabError(f"bestmove {search.bestmove} differs from the first PV line at ply {ply}")
    return search.bestmove


def _opening_search(
    engine: Engine,
    cache: dict | None,
    variant: str,
    fen: str,
    history: list[str],
    depth: int,
    searchmoves: list[str],
) -> SearchResult:
    """MultiPV over every legal move. Searches are deterministic, so results can be cached."""
    key = (variant, fen, tuple(history), depth)
    if cache is not None and key in cache:
        return cache[key]
    result = engine.search(variant, fen, history, depth=depth, searchmoves=searchmoves, multipv=len(searchmoves))
    if cache is not None:
        cache[key] = result
    return result


# ------------------------------------------------------------------ workers

_engine: Engine | None = None
_config: Config | None = None
_cache: dict = {}


def _init_worker(config: Config) -> None:
    global _engine, _config
    _config = config
    _engine = Engine(hash_mb=config.hash_mb)
    atexit.register(_engine.close)


def _run_task(task: tuple[str, int]) -> dict:
    assert _engine is not None and _config is not None
    return play_game(_engine, _config, *task, cache=_cache)


# ------------------------------------------------------------- provenance


def _command(args: list[str]) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True, cwd=ROOT).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def provenance(config: Config) -> dict:
    with Engine(hash_mb=config.hash_mb) as engine:
        name, variant = engine.name, engine.asha_variant
    return {
        "config": asdict(config),
        "engine": name,
        "engine_options": {"Threads": 1, "Hash": config.hash_mb, "Use NNUE": False},
        "asha_variant": variant,
        "git_commit": _command(["git", "rev-parse", "HEAD"]),
        "git_dirty": bool(_command(["git", "status", "--porcelain", "--", "asha", "app.py", "static", "lab"])),
        "python": sys.version.split()[0],
        "python_chess": chess.__version__,
        "node": _command(["node", "--version"]),
        "platform": platform.platform(),
        "started": time.strftime("%Y-%m-%d %H:%M:%S %z"),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    defaults = Config()
    parser.add_argument("--out", type=Path, required=True, help="run directory")
    parser.add_argument("--variants", default=",".join(defaults.variants))
    parser.add_argument("--games", type=int, default=defaults.games, help="games per variant")
    parser.add_argument("--nodes", type=int, default=defaults.nodes)
    parser.add_argument("--opening-plies", type=int, default=defaults.opening_plies)
    parser.add_argument("--opening-depth", type=int, default=defaults.opening_depth)
    parser.add_argument("--margin", type=int, default=defaults.margin, help="centipawns")
    parser.add_argument("--max-plies", type=int, default=defaults.max_plies)
    parser.add_argument("--hash", type=int, default=defaults.hash_mb, dest="hash_mb")
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument("--workers", type=int, default=max(1, (multiprocessing.cpu_count() or 2) - 2))
    args = parser.parse_args(argv)
    variants = tuple(v.strip() for v in args.variants.split(",") if v.strip())
    unknown = [v for v in variants if v not in RULES]
    if unknown:
        parser.error(f"unknown variant(s): {', '.join(unknown)}")
    config = Config(
        variants=variants,
        games=args.games,
        nodes=args.nodes,
        opening_plies=args.opening_plies,
        opening_depth=args.opening_depth,
        margin=args.margin,
        max_plies=args.max_plies,
        hash_mb=args.hash_mb,
        seed=args.seed,
    )

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    run_file, games_file = out / "run.json", out / "games.jsonl"
    if run_file.exists():
        previous = json.loads(run_file.read_text(encoding="utf-8"))["config"]
        same = {k: v for k, v in previous.items() if k != "games"} == {
            k: v for k, v in json.loads(json.dumps(asdict(config))).items() if k != "games"
        }
        if not same:
            sys.exit(f"{run_file} was made with different settings; use a new --out directory")
        run = json.loads(run_file.read_text(encoding="utf-8"))
        run["config"]["games"] = max(run["config"]["games"], config.games)
    else:
        run = provenance(config)
    run_file.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")

    done = set()
    if games_file.exists():
        for text in games_file.read_text(encoding="utf-8").splitlines():
            if text.strip():
                game = json.loads(text)
                done.add((game["variant"], game["index"]))
    tasks = [(v, i) for i in range(config.games) for v in variants if (v, i) not in done]
    print(f"{len(done)} games already in {games_file}, {len(tasks)} to play with {args.workers} workers", flush=True)
    if not tasks:
        return

    started = time.perf_counter()
    with multiprocessing.Pool(args.workers, initializer=_init_worker, initargs=(config,)) as pool:
        with games_file.open("a", encoding="utf-8") as sink:
            for count, game in enumerate(pool.imap_unordered(_run_task, tasks), 1):
                sink.write(json.dumps(game, separators=(",", ":")) + "\n")
                sink.flush()
                elapsed = time.perf_counter() - started
                eta = elapsed / count * (len(tasks) - count)
                print(
                    f"[{count}/{len(tasks)}] {game['variant']} #{game['index']}: {game['result'] or 'ERROR'} "
                    f"{game['termination']} {game['plies']} plies {game['seconds']:.0f}s"
                    f" | {elapsed / 60:.1f} min, about {eta / 60:.0f} min left"
                    + (f" | {game['error']}" if "error" in game else ""),
                    flush=True,
                )


if __name__ == "__main__":
    main()
