'use strict';

// Browser opponent: Fairy-Stockfish (WebAssembly, GPL-3.0) configured for Asha.
// It only proposes moves. The search is restricted to the server's legal moves
// and the chosen move is submitted to /api/move like any other, so the Asha
// engine on the server stays the only referee.
window.AshaAI = (() => {
    const BASE = '/static/vendor/fairy-stockfish/';

    // Asha pieces in Betza notation (m = move only, c = capture only,
    // e = en passant, i = initial double step, s = sideways, f = forward).
    // Known gap: Fairy-Stockfish grants the double step by square, not by
    // whether the pawn has moved. searchmoves keeps the root legal; deeper in
    // the tree the gap did not measurably change playing strength.
    const VARIANT = [
        '[asha:chess]',
        'customPiece1 = p:fmWsmWfmFfceFifmnD',
        'customPiece2 = n:NmK',
        'customPiece3 = b:BmW',
        'customPiece4 = r:RmF',
        'pawnTypes = p',
        'promotionPawnTypes = p',
        'enPassantTypes = p',
        'nMoveRuleTypes = p',
        'castlingRookPieces = r',
        'promotionPieceTypes = qrbn',
    ].join('\n');

    const LEVELS = {
        easy: { skill: 0, movetime: 300 },
        medium: { skill: 8, movetime: 800 },
        hard: { skill: 20, movetime: 2000 },
    };

    // WebAssembly SIMD feature probe (from wasm-feature-detect).
    const SIMD_PROBE = new Uint8Array([
        0, 97, 115, 109, 1, 0, 0, 0, 1, 5, 1, 96, 0, 1, 123, 3, 2, 1, 0, 10, 10, 1, 8, 0, 65, 0, 253, 15, 253, 98, 11,
    ]);

    let engine = null;

    // Why the engine cannot run here, or null when it can.
    function unsupportedReason() {
        if (typeof WebAssembly !== 'object') return 'WebAssembly is not available in this browser.';
        if (!window.crossOriginIsolated || typeof SharedArrayBuffer === 'undefined') {
            return 'The page is not cross-origin isolated, so the threaded engine cannot start.';
        }
        if (!WebAssembly.validate(SIMD_PROBE)) return 'This browser does not support WebAssembly SIMD.';
        return null;
    }

    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = () => reject(new Error('Could not load the engine.'));
            document.head.appendChild(script);
        });
    }

    // Start the engine; resolves to send(commands, pattern) for UCI exchanges.
    async function start() {
        const reason = unsupportedReason();
        if (reason) throw new Error(reason);
        await loadScript(`${BASE}stockfish.js`);
        const sf = await window.Stockfish({ locateFile: (file) => BASE + file });

        let lines = [];
        let waiter = null;
        sf.addMessageListener((line) => {
            lines.push(line);
            if (waiter && waiter.pattern.test(line)) {
                const { resolve } = waiter;
                waiter = null;
                resolve(lines);
            }
        });
        // Send UCI commands and wait for the line matching pattern (default: readyok).
        function send(commands, pattern) {
            if (!pattern) {
                commands = [...commands, 'isready'];
                pattern = /^readyok/;
            }
            lines = [];
            const done = new Promise((resolve) => { waiter = { pattern, resolve }; });
            commands.forEach((command) => sf.postMessage(command));
            return done;
        }
        send.stop = () => sf.postMessage('stop');

        sf.FS.writeFile('/asha.ini', `${VARIANT}\n`);
        const threads = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 2) - 1));
        await send(['uci'], /^uciok/);
        await send([
            `setoption name Threads value ${threads}`,
            'setoption name VariantPath value /asha.ini',
            'setoption name UCI_Variant value asha',
        ]);
        return send;
    }

    // Start loading the engine (about 1.7 MB) ahead of its first move.
    function load() {
        engine = engine || start().catch((error) => { engine = null; throw error; });
        return engine;
    }

    function withTimeout(promise, ms, message) {
        let timer;
        const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(message)), ms); });
        return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
    }

    // Engine's choice among state.legalMoves (UCI), or null if it offered none of them.
    async function bestMove(state, level) {
        const send = await load();
        const { skill, movetime } = LEVELS[level] || LEVELS.medium;
        const position = state.enginePosition;
        const legal = state.legalMoves.map((m) => m.uci);
        const moves = position.moves.length ? ` moves ${position.moves.join(' ')}` : '';
        const search = send([
            `setoption name Skill Level value ${skill}`,
            `position fen ${position.fen}${moves}`,
            `go movetime ${movetime} searchmoves ${legal.join(' ')}`,
        ], /^bestmove/);
        // movetime bounds the search; a stalled engine is told to stop, then given up on.
        const nudge = setTimeout(send.stop, movetime + 3000);
        try {
            const lines = await withTimeout(search, movetime + 10000, 'The engine stopped responding.');
            const move = lines[lines.length - 1].split(' ')[1];
            return legal.includes(move) ? move : null;
        } catch (error) {
            engine = null; // start a fresh engine next time
            throw error;
        } finally {
            clearTimeout(nudge);
        }
    }

    return { bestMove, load, unsupportedReason };
})();
