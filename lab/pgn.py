"""Write a run's games as PGN, one file per variant, so anyone can read them.

Asha games use the game's own notation (``Nb1~b2`` for Asha moves), which
ordinary PGN software shows as text but cannot replay.

    python -m lab.pgn lab/runs/main
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from .report import load

TERMINATION = {
    "checkmate": "checkmate",
    "stalemate": "stalemate",
    "insufficient_material": "insufficient material",
    "fivefold_repetition": "fivefold repetition",
    "seventyfive_moves": "75-move rule",
    "threefold_repetition": "threefold repetition (claimed)",
    "fifty_moves": "50-move rule (claimed)",
    "ply_cap": "stopped at the half-move cap",
}


def game_pgn(game: dict, run: str, config: dict) -> str:
    cfg = config["config"]
    engine = f"{config['engine'].split(' [')[0]}, {cfg['nodes']:,} nodes"
    tags = {
        "Event": f"Asha Lab {run}",
        "Site": "engine self-play",
        "Round": str(game["index"] + 1),
        "White": engine,
        "Black": engine,
        "Result": game["result"],
        "Variant": "Asha" if game["variant"] == "asha" else "Standard",
        "Termination": TERMINATION.get(game["termination"], game["termination"]),
        "PlyCount": str(game["plies"]),
        "Sampling": f"first {cfg['opening_plies']} half-moves drawn from the playable moves (seed {cfg['seed']})",
    }
    header = "\n".join(f'[{key} "{value}"]' for key, value in tags.items())
    tokens = []
    for ply, move in enumerate(game["notation"]):
        tokens.append(f"{ply // 2 + 1}. {move}" if ply % 2 == 0 else move)
    tokens.append(game["result"])
    return header + "\n\n" + textwrap.fill(" ".join(tokens), width=80) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    config, games = load(args.run)
    for variant in config["config"]["variants"]:
        chosen = [g for g in games if g["variant"] == variant and "error" not in g]
        out = args.run / f"games-{variant}.pgn"
        out.write_text("\n".join(game_pgn(g, args.run.name, config) for g in chosen), encoding="utf-8")
        print(f"wrote {len(chosen)} games to {out}")


if __name__ == "__main__":
    main()
