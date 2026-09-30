"""Turn a self-play run into numbers: lab/runs/<run>/report.md and summary.json.

Every rate comes with a 95 % bootstrap confidence interval. Games, not moves,
are resampled, because the moves of one game are not independent. Games that
ended in an error are left out of every number and counted separately.

    python -m lab.report lab/runs/main
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median

ASHA_KINDS = ("kings_step", "pawn_lateral", "pawn_diagonal")
PHASES = {"o": "opening", "m": "middlegame", "e": "endgame"}
MARGINS = (15, 30, 50)

# An Asha moment: the engine's move is an Asha move and the best classical
# move scores at least MOMENT_GAP centipawns worse, while the position is not
# already decided either way (the Asha move does not score below
# -DECIDED and the classical alternative does not score above +DECIDED).
MOMENT_GAP = 200
DECIDED = 300


def load(run: Path) -> tuple[dict, list[dict]]:
    config = json.loads((run / "run.json").read_text(encoding="utf-8"))
    games = [json.loads(t) for t in (run / "games.jsonl").read_text(encoding="utf-8").splitlines() if t.strip()]
    games.sort(key=lambda g: (g["variant"], g["index"]))
    return config, games


# ------------------------------------------------------------ per game


def playable(lines: Sequence[Sequence], margin: int) -> list[str]:
    best = max(score for _, score in lines)
    return [move for move, score in lines if score >= best - margin]


def is_asha_moment(best: int, alternative: int | None) -> bool:
    """Whether only the Asha move holds the position (see MOMENT_GAP)."""
    if alternative is None:  # every legal move was an Asha move
        return best >= -DECIDED
    return best - alternative >= MOMENT_GAP and best >= -DECIDED and alternative <= DECIDED


def gap(best: int, alternative: int | None) -> float:
    if alternative is None:
        return math.inf
    return best - alternative


def summarize(game: dict, opening_plies: int, margin: int) -> dict[str, float]:
    """Numbers for one game; every reported rate is a ratio of sums of these."""
    s: Counter[str] = Counter()
    s["games"] = 1
    s["plies"] = game["plies"]
    winner = game["winner"]
    s["white_wins"] = winner == "white"
    s["black_wins"] = winner == "black"
    s["draws"] = winner is None
    s["white_points"] = 1 if winner == "white" else 0.5 if winner is None else 0
    s["decisive"] = winner is not None
    s["captures"] = game["captures"].count("1")
    s["checks"] = game["checks"].count("1")
    first = game["captures"].find("1")
    if first >= 0:
        s["has_capture"] = 1
        s["first_capture_move"] = first // 2 + 1  # full-move number of the first capture
    kinds, phases, checks = game["kinds"], game["phases"], game["checks"]
    for ply, kind in enumerate(kinds):
        asha = kind in ASHA_KINDS
        s["moves"] += 1
        s["asha_moves"] += asha
        s[f"moves_{phases[ply]}"] += 1
        s[f"asha_moves_{phases[ply]}"] += asha
        if asha:
            name = kind if kind != "kings_step" else f"kings_step_{game['pieces'][ply]}"
            s[f"kind_{name}"] += 1
        if ply >= opening_plies:
            s["engine_moves"] += 1
            s["engine_asha_moves"] += asha
            s["depth"] += game["depths"][ply]
        if ply > 0 and checks[ply - 1] == "1":
            s["evasions"] += 1
            s["asha_evasions"] += asha
    for ply, _move, alternative in game["alternatives"]:
        if ply < opening_plies:
            continue
        best = game["scores"][ply]
        g = gap(best, alternative)
        s["gap_100"] += g >= 100
        s["gap_200"] += g >= 200
        s["moments"] += is_asha_moment(best, alternative)
    s["games_with_moment"] = s["moments"] > 0
    product = 1.0
    for ply, entry in enumerate(game["opening"]):
        lines = entry["lines"]
        s[f"reached_{ply}"] = 1
        s[f"legal_{ply}"] = len(lines)
        for m in MARGINS:
            good = playable(lines, m)
            s[f"playable_{m}_{ply}"] = len(good)
            s[f"playable_{m}"] += len(good)
            if ply > 0:  # plies 2 onwards: the start position is the same in every game
                s[f"playable_{m}_later"] += len(good)
            if game["variant"] == "asha":
                s[f"playable_asha_{m}"] += sum(1 for move in good if _is_asha_uci(game, ply, move))
        product *= len(playable(lines, margin))
        s["positions_later"] += ply > 0
    s["opening_positions"] = len(game["opening"])
    if len(game["opening"]) == opening_plies:
        s["knuth"] = product
        s["full_opening"] = 1
    return dict(s)


def _is_asha_uci(game: dict, ply: int, move: str) -> bool:
    return move in game["opening"][ply]["asha"]


# ----------------------------------------------------------- statistics


@dataclass(frozen=True)
class Estimate:
    value: float
    low: float
    high: float

    def fmt(self, kind: str = "pct") -> str:
        f = _formatter(kind)
        return f"{f(self.value)} [{f(self.low)}, {f(self.high)}]"


def _formatter(kind: str) -> Callable[[float], str]:
    if kind == "pct":
        return lambda x: f"{100 * x:.1f} %"
    if kind == "pp":
        return lambda x: f"{100 * x:+.1f} pp"
    if kind == "big":
        return lambda x: f"{x:,.3g}" if x < 1e6 else f"{x:.2e}"
    if kind == "diff":
        return lambda x: f"{x:+.2f}"
    return lambda x: f"{x:.2f}"


def ratio(rows: Sequence[dict], num: str, den: str) -> float:
    n = sum(r.get(num, 0) for r in rows)
    d = sum(r.get(den, 0) for r in rows)
    return n / d if d else math.nan


class Bootstrap:
    """Percentile bootstrap over games, with the same resamples for every metric."""

    def __init__(self, rows: Sequence[dict], resamples: int, seed: str):
        rng = random.Random(seed)
        n = len(rows)
        self.rows = rows
        self.samples = [[rng.randrange(n) for _ in range(n)] for _ in range(resamples)] if n else []

    def draws(self, num: str, den: str) -> list[float]:
        nums = [r.get(num, 0) for r in self.rows]
        dens = [r.get(den, 0) for r in self.rows]
        out = []
        for sample in self.samples:
            d = sum(dens[i] for i in sample)
            out.append(sum(nums[i] for i in sample) / d if d else math.nan)
        return out

    def estimate(self, num: str, den: str) -> Estimate:
        return Estimate(ratio(self.rows, num, den), *_interval(self.draws(num, den)))


def _interval(values: list[float]) -> tuple[float, float]:
    values = sorted(v for v in values if not math.isnan(v))
    if not values:
        return math.nan, math.nan
    return values[int(0.025 * (len(values) - 1))], values[int(math.ceil(0.975 * (len(values) - 1)))]


def difference(a: Bootstrap, b: Bootstrap, num: str, den: str) -> Estimate:
    da, db = a.draws(num, den), b.draws(num, den)
    return Estimate(
        ratio(a.rows, num, den) - ratio(b.rows, num, den), *_interval([x - y for x, y in zip(da, db, strict=True)])
    )


def quotient(a: Bootstrap, b: Bootstrap, num: str, den: str) -> Estimate:
    da, db = a.draws(num, den), b.draws(num, den)
    return Estimate(
        ratio(a.rows, num, den) / ratio(b.rows, num, den), *_interval([x / y for x, y in zip(da, db, strict=True)])
    )


# --------------------------------------------------------------- report


METRICS: list[tuple[str, str, str, str]] = [
    # (label, numerator, denominator, format)
    ("White wins", "white_wins", "games", "pct"),
    ("Draws", "draws", "games", "pct"),
    ("Black wins", "black_wins", "games", "pct"),
    ("White score", "white_points", "games", "pct"),
    ("Decisive games", "decisive", "games", "pct"),
    ("Game length (half-moves)", "plies", "games", "num"),
    ("Captures per game", "captures", "games", "num"),
    ("Checks per game", "checks", "games", "num"),
    ("Move of the first capture", "first_capture_move", "has_capture", "num"),
    ("Average search depth at the node limit", "depth", "engine_moves", "num"),
]


def build(run: Path, resamples: int) -> tuple[str, dict]:
    config, games = load(run)
    cfg = config["config"]
    opening_plies, margin = cfg["opening_plies"], cfg["margin"]
    by_variant: dict[str, list[dict]] = {}
    errors: dict[str, list[dict]] = {}
    for game in games:
        (errors if "error" in game else by_variant).setdefault(game["variant"], []).append(game)
    rows = {v: [summarize(g, opening_plies, margin) for g in gs] for v, gs in by_variant.items()}
    boots = {v: Bootstrap(r, resamples, f"{cfg['seed']}:{v}") for v, r in rows.items()}
    variants = [v for v in ("asha", "chess") if v in rows]
    summary: dict = {"run": run.name, "config": cfg, "engine": config["engine"], "variants": {}}

    out: list[str] = []
    w = out.append
    w(f"# Asha Lab report: `{run.name}`\n")
    w(
        f"Engine: {config['engine']}, 1 thread, {cfg['hash_mb']} MB hash, NNUE off (the build has no network). "
        f"Each search starts from a cleared engine.\n"
    )
    w(
        f"Opening: the first {opening_plies} half-moves are chosen at random among the *playable* moves "
        f"(within {margin} cp of the best at depth {cfg['opening_depth']}, MultiPV over all legal moves). "
        f"Then {cfg['nodes']:,} nodes per move. Seed {cfg['seed']}. Commit `{config['git_commit'][:7]}`"
        + (" (with uncommitted changes)" if config.get("git_dirty") else "")
        + ".\n"
    )
    w("Values are shown as estimate [95 % bootstrap interval over games].\n")

    w("## Games\n")
    w("| | " + " | ".join(variants) + " |")
    w("|---|" + "---|" * len(variants))
    w("| Games analysed | " + " | ".join(str(len(rows[v])) for v in variants) + " |")
    w("| Games with an error (excluded) | " + " | ".join(str(len(errors.get(v, []))) for v in variants) + " |")
    for label, num, den, kind in METRICS:
        w(f"| {label} | " + " | ".join(boots[v].estimate(num, den).fmt(kind) for v in variants) + " |")
    medians = {v: median(g["plies"] for g in by_variant[v]) for v in variants}
    w("| Median game length (half-moves) | " + " | ".join(f"{medians[v]:g}" for v in variants) + " |")
    w("")
    if len(variants) == 2:
        a, b = boots["asha"], boots["chess"]
        w("### Asha minus classical\n")
        w("| | difference |")
        w("|---|---|")
        for label, num, den, kind in METRICS:
            w(f"| {label} | {difference(a, b, num, den).fmt('pp' if kind == 'pct' else 'diff')} |")
        w("")

    w("### How games ended\n")
    terms = {v: Counter(g["termination"] for g in by_variant[v]) for v in variants}
    names = sorted(set().union(*terms.values()), key=lambda t: -sum(c[t] for c in terms.values()))
    w("| | " + " | ".join(variants) + " |")
    w("|---|" + "---|" * len(variants))
    for name in names:
        w(f"| {name} | " + " | ".join(str(terms[v][name]) for v in variants) + " |")
    w("")

    w("## Opening: how many good choices\n")
    w(
        f"A move is *playable* if its depth-{cfg['opening_depth']} score is within the margin of the best move's. "
        f"Ply 1 is the start position, the same in every game.\n"
    )
    for m in MARGINS:
        w(f"**Margin {m} cp**\n")
        w("| Ply | " + " | ".join(f"{v} legal | {v} playable" for v in variants) + " |")
        w("|---|" + "---|---|" * len(variants))
        for ply in range(opening_plies):
            cells = []
            for v in variants:
                legal = boots[v].estimate(f"legal_{ply}", f"reached_{ply}")
                good = boots[v].estimate(f"playable_{m}_{ply}", f"reached_{ply}")
                cells += [f"{legal.value:.1f}", good.fmt("num") if ply else f"{good.value:g}"]
            w(f"| {ply + 1} | " + " | ".join(cells) + " |")
        w("")
    w(f"**Playable moves per position, plies 2–{opening_plies}**\n")
    both = len(variants) == 2
    w("| Margin | " + " | ".join(variants) + (" | Asha ÷ classical |" if both else " |"))
    w("|---|" + "---|" * (len(variants) + both))
    for m in MARGINS:
        cells = [boots[v].estimate(f"playable_{m}_later", "positions_later").fmt("num") for v in variants]
        if both:
            cells.append(quotient(boots["asha"], boots["chess"], f"playable_{m}_later", "positions_later").fmt("num"))
        w(f"| {m} cp | " + " | ".join(cells) + " |")
    w("")
    w(f"**Distinct openings** (margin {margin} cp, the one used to choose moves)\n")
    w("| | " + " | ".join(variants) + " |")
    w("|---|" + "---|" * len(variants))
    distinct = {v: len({tuple(g["moves"][:opening_plies]) for g in by_variant[v]}) for v in variants}
    w(
        "| Different openings among the games | "
        + " | ".join(f"{distinct[v]} / {len(rows[v])}" for v in variants)
        + " |"
    )
    knuth = {v: boots[v].estimate("knuth", "full_opening") for v in variants}
    w(
        f"| Playable {opening_plies}-half-move openings (Knuth estimate) | "
        + " | ".join(knuth[v].fmt("big") for v in variants)
        + " |"
    )
    w("")
    w(
        "The Knuth estimate is the average, over the sampled games, of the product of the number of playable moves "
        "at each opening ply. Because each move was drawn uniformly from the playable ones, it is an unbiased "
        "estimate of the number of distinct openings made only of playable moves (Knuth, 1975). Its interval is "
        "wide because the products are heavy-tailed.\n"
    )
    if "asha" in rows:
        w(
            "Share of the playable opening moves that are Asha moves: "
            + boots["asha"].estimate(f"playable_asha_{margin}", f"playable_{margin}").fmt()
            + "\n"
        )

    if "asha" in rows:
        b = boots["asha"]
        w("## Asha moves in play\n")
        w("Share of all moves played that are Asha moves (King's Step, pawn sideways or diagonal step):\n")
        w("| Phase | share |")
        w("|---|---|")
        w(f"| All moves | {b.estimate('asha_moves', 'moves').fmt()} |")
        w(f"| Engine moves (after the sampled opening) | {b.estimate('engine_asha_moves', 'engine_moves').fmt()} |")
        for p, name in PHASES.items():
            w(f"| {name.capitalize()} | {b.estimate(f'asha_moves_{p}', f'moves_{p}').fmt()} |")
        w(f"| Replies to check | {b.estimate('asha_evasions', 'evasions').fmt()} |")
        w("")
        w("| Asha move type | share of all moves |")
        w("|---|---|")
        for key, label in (
            ("kind_kings_step_N", "Knight King's Step"),
            ("kind_kings_step_B", "Bishop King's Step"),
            ("kind_kings_step_R", "Rook King's Step"),
            ("kind_pawn_lateral", "Pawn sideways step"),
            ("kind_pawn_diagonal", "Pawn diagonal step"),
        ):
            w(f"| {label} | {b.estimate(key, 'moves').fmt()} |")
        w("")
        w("### When only an Asha move will do\n")
        w(
            "For every engine move that was an Asha move, a second search of the same size, restricted to the "
            "classical moves, scored the best classical alternative. Both scores come from separate searches "
            f"at {cfg['nodes']:,} nodes, so small gaps are noise; the thresholds are deliberately large.\n"
        )
        w("| | per 100 engine moves | games with at least one |")
        w("|---|---|---|")
        w(f"| Best classical move ≥ 100 cp worse | {_per100(b, 'gap_100')} | |")
        w(f"| Best classical move ≥ 200 cp worse | {_per100(b, 'gap_200')} | |")
        w(
            f"| Asha moment (≥ {MOMENT_GAP} cp, position not already decided) | {_per100(b, 'moments')} | "
            f"{b.estimate('games_with_moment', 'games').fmt()} |"
        )
        w("")

    if len(variants) == 2:
        w("## Pre-registered checks\n")
        w(
            "The hypotheses and rules are in lab/HYPOTHESES.md. *Supported* means the 95 % interval meets the "
            "condition in this run; a public claim also needs the other run to point the same way.\n"
        )
        w("| | condition | this run | verdict |")
        w("|---|---|---|---|")
        for row in checks(boots["asha"], boots["chess"]):
            w("| " + " | ".join(row) + " |")
        w("")

    w("## Limitations\n")
    w(
        "- These are engine games. They show what the rules allow and reward at one engine strength, "
        "not what people will enjoy.\n"
        "- The engine uses its classical evaluation in both games. Its piece values for Asha's pieces are its "
        "own estimates, so a centipawn is not necessarily worth the same in both games; the opening tables "
        "therefore show three margins.\n"
        "- Fairy-Stockfish's Asha model differs from the rules in two known ways (it grants the double step by "
        "square rather than by whether the pawn has moved, and it does not see en passant); the root is restricted "
        "to Asha's legal moves, but the search below the root can be slightly off.\n"
        "- At the same node count the engine searches less deep in Asha, because Asha has more moves per "
        "position (see the depth row).\n"
        "- Insufficient material is judged by each game's own rules: python-chess also recognises classical "
        "dead positions such as bishops of the same colour, which Asha does not have.\n"
    )

    for v in variants:
        summary["variants"][v] = {
            "games": len(rows[v]),
            "errors": len(errors.get(v, [])),
            "metrics": {label: vars(boots[v].estimate(num, den)) for label, num, den, _ in METRICS},
            "terminations": dict(terms[v]),
            "distinct_openings": distinct[v],
            "knuth_openings": vars(knuth[v]),
        }
    return "\n".join(out) + "\n", summary


def checks(asha: Bootstrap, chess: Bootstrap) -> list[tuple[str, str, str, str]]:
    """The hypotheses of lab/HYPOTHESES.md, each checked against its 95 % interval."""

    def verdict(supported: bool, contradicted: bool) -> str:
        return "supported" if supported else "contradicted" if contradicted else "not supported"

    rows = []
    for m in MARGINS:
        q = quotient(asha, chess, f"playable_{m}_later", "positions_later")
        rows.append(
            (f"H1 ({m} cp)", "Asha ÷ classical playable moves > 1", q.fmt("num"), verdict(q.low > 1, q.high < 1))
        )
    for p in ("m", "e"):
        e = asha.estimate(f"asha_moves_{p}", f"moves_{p}")
        rows.append((f"H2 ({PHASES[p]})", "Asha share of moves ≥ 10 %", e.fmt(), verdict(e.low >= 0.1, e.high < 0.1)))
    e = asha.estimate("moments", "engine_moves")
    rows.append(
        (
            "H3 (rate)",
            "Asha moments ≥ 1 per 100 engine moves",
            _per100(asha, "moments"),
            verdict(e.low >= 0.01, e.high < 0.01),
        )
    )
    e = asha.estimate("games_with_moment", "games")
    rows.append(("H3 (games)", "games with an Asha moment ≥ 25 %", e.fmt(), verdict(e.low >= 0.25, e.high < 0.25)))
    d = difference(asha, chess, "decisive", "games")
    direction = "more decisive" if d.low > 0 else "fewer decisive" if d.high < 0 else "no clear difference"
    rows.append(("H4", "decisive games, Asha − classical (two-sided)", d.fmt("pp"), direction))
    e = asha.estimate("white_points", "games")
    inside, outside = e.low >= 0.45 and e.high <= 0.60, e.high < 0.45 or e.low > 0.60
    rows.append(("H5", "White score in Asha within 45–60 %", e.fmt(), verdict(inside, outside)))
    return rows


def _per100(b: Bootstrap, key: str) -> str:
    e = b.estimate(key, "engine_moves")
    return f"{100 * e.value:.2f} [{100 * e.low:.2f}, {100 * e.high:.2f}]"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args(argv)
    text, summary = build(args.run, args.resamples)
    (args.run / "report.md").write_text(text, encoding="utf-8")
    (args.run / "summary.json").write_text(json.dumps(_finite(summary), indent=2) + "\n", encoding="utf-8")
    print(text)


def _finite(value: object) -> object:
    """The value with NaN and infinities replaced by None, which JSON can represent."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_finite(v) for v in value]
    return value


if __name__ == "__main__":
    main()
