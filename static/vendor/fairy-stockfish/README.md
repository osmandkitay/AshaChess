# Fairy-Stockfish (WebAssembly)

Unmodified files from the npm package `fairy-stockfish-nnue.wasm` 1.1.12
(published 2026-08-26), the WebAssembly port of Fairy-Stockfish used by pychess.org.

- Source: https://github.com/fairy-stockfish/fairy-stockfish.wasm (build) and
  https://github.com/fairy-stockfish/Fairy-Stockfish (engine)
- License: GNU GPL v3, see `Copying.txt`; authors in `AUTHORS`.

The build uses WebAssembly threads and SIMD, so the page must be cross-origin
isolated (`Cross-Origin-Opener-Policy: same-origin`,
`Cross-Origin-Embedder-Policy: require-corp`).
