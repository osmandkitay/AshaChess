"""A small UCI client for lab/engine.cjs (Fairy-Stockfish WebAssembly in Node).

Every search starts from a cleared engine (``ucinewgame``), so its result
depends only on the position, the move list and the limits. With one thread
and a node or depth limit that makes each search reproducible.
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

ENGINE_JS = Path(__file__).with_name("engine.cjs")

# Scores are centipawns from the side to move's point of view. A mate in n
# (n > 0: the side to move mates; n < 0: it is mated) becomes
# sign(n) * (MATE - |n|), so every mate outranks every centipawn score and a
# shorter mate outranks a longer one.
MATE = 100_000


def score_value(kind: str, value: int) -> int:
    if kind == "cp":
        return value
    if kind != "mate":
        raise ValueError(f"unknown score type: {kind!r}")
    if value > 0:
        return MATE - value
    return -MATE - value  # mated in |value|; "mate 0" (already mated) is -MATE


def is_mate(score: int) -> bool:
    return abs(score) > MATE - 1000


@dataclass(frozen=True)
class Line:
    move: str
    score: int
    depth: int
    bound: str | None  # "lowerbound" / "upperbound" if the score is only a bound
    pv: tuple[str, ...]


@dataclass(frozen=True)
class SearchResult:
    bestmove: str
    lines: tuple[Line, ...]  # MultiPV lines, best first
    nodes: int

    @property
    def score(self) -> int:
        return self.lines[0].score

    @property
    def depth(self) -> int:
        return self.lines[0].depth


def parse_info(text: str) -> tuple[int, Line, int] | None:
    """(multipv index, line, nodes) from an ``info ... pv ...`` line, else None."""
    tokens = text.split()
    if not tokens or tokens[0] != "info" or "pv" not in tokens or "score" not in tokens:
        return None
    fields: dict[str, str] = {}
    bound = None
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token == "pv":
            break
        if token == "score":
            fields["score_kind"], fields["score"] = tokens[i + 1], tokens[i + 2]
            i += 3
            continue
        if token in ("lowerbound", "upperbound"):
            bound = token
            i += 1
            continue
        if token == "string":
            return None
        if i + 1 < len(tokens):
            fields[token] = tokens[i + 1]
        i += 2
    pv = tuple(tokens[tokens.index("pv") + 1 :])
    if not pv:
        return None
    line = Line(pv[0], score_value(fields["score_kind"], int(fields["score"])), int(fields["depth"]), bound, pv)
    return int(fields.get("multipv", 1)), line, int(fields.get("nodes", 0))


def parse_search(output: list[str]) -> SearchResult:
    """The final line per MultiPV index and the bestmove of one search."""
    last: dict[int, Line] = {}
    nodes = 0
    for text in output:
        parsed = parse_info(text)
        if parsed:
            index, line, line_nodes = parsed
            last[index] = line
            nodes = max(nodes, line_nodes)
    best = output[-1].split()
    if not best or best[0] != "bestmove" or len(best) < 2:
        raise EngineError(f"no bestmove in engine output: {output[-1:]!r}")
    if not last:
        raise EngineError("engine returned no scored line")
    lines = tuple(last[i] for i in sorted(last))
    return SearchResult(best[1], lines, nodes)


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, hash_mb: int = 16, timeout: float = 600.0):
        self.hash_mb = hash_mb
        self.timeout = timeout
        self._variant: str | None = None
        self._multipv = 1
        self._start()

    def _start(self) -> None:
        self._proc = subprocess.Popen(
            ["node", str(ENGINE_JS)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self._lines: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=self._read, args=(self._proc, self._lines), daemon=True).start()
        self.asha_variant = ""
        for text in self._until("uciok", ["uci"]):
            if text.startswith("id name "):
                self.name = text[len("id name ") :]
            if text.startswith("info string asha-variant "):
                self.asha_variant = json.loads(text[len("info string asha-variant ") :])
        if not self.asha_variant:
            raise EngineError("engine.cjs did not report the Asha variant")
        for command in (
            "setoption name Threads value 1",
            f"setoption name Hash value {self.hash_mb}",
            "setoption name Use NNUE value false",
            "setoption name VariantPath value /asha.ini",
        ):
            self._send(command)
        self._ready()
        self._variant = None
        self._multipv = 1

    @staticmethod
    def _read(proc: subprocess.Popen[str], lines: queue.Queue[str | None]) -> None:
        assert proc.stdout is not None
        for text in proc.stdout:
            lines.put(text.rstrip("\r\n"))
        lines.put(None)

    def _send(self, command: str) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.write(command + "\n")
        self._proc.stdin.flush()

    def _until(self, prefix: str, commands: list[str]) -> list[str]:
        """Send commands, then collect output up to the first line starting with prefix."""
        for command in commands:
            self._send(command)
        output = []
        while True:
            try:
                text = self._lines.get(timeout=self.timeout)
            except queue.Empty:
                raise EngineError(f"engine timed out waiting for {prefix!r}") from None
            if text is None:
                raise EngineError("engine process exited")
            output.append(text)
            if text.startswith(prefix):
                return output

    def _ready(self) -> None:
        self._until("readyok", ["isready"])

    def search(
        self,
        variant: str,
        fen: str,
        moves: list[str],
        *,
        nodes: int | None = None,
        depth: int | None = None,
        searchmoves: list[str] | None = None,
        multipv: int = 1,
    ) -> SearchResult:
        """One search from a cleared engine; exactly one of nodes and depth."""
        if (nodes is None) == (depth is None):
            raise ValueError("give exactly one of nodes and depth")
        if searchmoves is not None and not searchmoves:
            raise ValueError("searchmoves must not be empty")
        if variant != self._variant:
            self._send(f"setoption name UCI_Variant value {variant}")
            self._variant = variant
        if multipv != self._multipv:
            self._send(f"setoption name MultiPV value {multipv}")
            self._multipv = multipv
        self._send("ucinewgame")
        self._ready()
        position = f"position fen {fen}" + (f" moves {' '.join(moves)}" if moves else "")
        go = f"go nodes {nodes}" if nodes is not None else f"go depth {depth}"
        if searchmoves is not None:
            go += " searchmoves " + " ".join(searchmoves)
        try:
            return parse_search(self._until("bestmove", [position, go]))
        except EngineError:
            self.restart()
            raise

    def restart(self) -> None:
        self.close()
        self._start()

    def close(self) -> None:
        if self._proc.poll() is None:
            try:
                self._send("quit")
                self._proc.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                self._proc.kill()

    def __enter__(self) -> Engine:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
