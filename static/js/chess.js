'use strict';

// Rendering only: every rule decision (legal moves, move kinds, check, results,
// notation) comes from the server state.
document.addEventListener('DOMContentLoaded', () => {
    const GLYPHS = {
        K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
        k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
    };
    const PROMOTION_ORDER = ['q', 'r', 'b', 'n'];
    const TARGET_CLASS = {
        quiet: 'valid-move',
        castling: 'valid-move',
        capture: 'valid-capture',
        en_passant: 'valid-capture',
        kings_step: 'valid-kings-step',
        pawn_lateral: 'valid-pawn-lateral',
        pawn_diagonal: 'valid-pawn-lateral',
    };
    const ASHA_KINDS = new Set(['kings_step', 'pawn_lateral', 'pawn_diagonal']);
    const TERMINATIONS = {
        checkmate: ['Checkmate', 'The king is checkmated.'],
        stalemate: ['Draw — Stalemate', 'The side to move has no legal moves and is not in check.'],
        insufficient_material: ['Draw — Insufficient Material', 'Neither side can ever deliver checkmate.'],
        fivefold_repetition: ['Draw — Fivefold Repetition', 'The same position occurred five times.'],
        seventyfive_moves: ['Draw — 75-Move Rule', '75 moves by each side without a capture or pawn move.'],
        threefold_repetition: ['Draw — Threefold Repetition (claimed)', 'The same position occurred three times.'],
        fifty_moves: ['Draw — 50-Move Rule (claimed)', '50 moves by each side without a capture or pawn move.'],
    };
    const CLAIM_LABELS = {
        threefold_repetition: 'Claim draw (threefold repetition)',
        fifty_moves: 'Claim draw (50-move rule)',
    };
    const CLASSES_TO_CLEAR = [
        'selected', 'valid-move', 'valid-capture', 'valid-kings-step', 'valid-pawn-lateral',
        'in-check', 'last-move-from', 'last-move-to', 'last-move-asha', 'drag-over',
    ];

    const boardEl = document.getElementById('chessboard');
    const turnEl = document.getElementById('turn');
    const statusEl = document.getElementById('check-status');
    const messageEl = document.getElementById('message');
    const resetButton = document.getElementById('reset-button');
    const claimButtons = document.getElementById('claim-buttons');
    const historyEl = document.getElementById('move-history-list');
    const promotionEl = document.getElementById('promotion-popup');
    const promotionChoices = document.getElementById('promotion-choices');
    const gameOverEl = document.getElementById('game-over-popup');
    const opponentEl = document.getElementById('opponent');
    const levelEl = document.getElementById('ai-level');

    let state = null;
    let selected = null;
    let drag = null; // { from, x, y, ghost } while a piece is held
    let suppressClick = false;
    let gameOverDismissed = false;
    let busy = false; // one request at a time, so responses cannot arrive out of order
    let aiThinking = false;
    let aiLoaded = false;
    const squares = {};

    // ---------------------------------------------------------------- popups

    function openPopup(popup) { popup.classList.add('active'); }
    function closePopup(popup) { popup.classList.remove('active'); }

    document.getElementById('manifest-btn').addEventListener('click', () => openPopup(document.getElementById('manifest-popup')));
    document.getElementById('rules-btn').addEventListener('click', () => openPopup(document.getElementById('rules-popup')));
    document.querySelectorAll('.popup-overlay').forEach((popup) => {
        popup.addEventListener('click', (e) => {
            if (e.target === popup || e.target.closest('.popup-close')) closePopup(popup);
        });
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') document.querySelectorAll('.popup-overlay.active').forEach(closePopup);
    });
    gameOverEl.addEventListener('click', (e) => {
        if (e.target === gameOverEl) gameOverDismissed = true;
    });
    document.getElementById('game-over-close').addEventListener('click', () => {
        gameOverDismissed = true;
        closePopup(gameOverEl);
    });
    document.getElementById('game-over-reset').addEventListener('click', resetGame);

    // ------------------------------------------------------------------- API

    async function api(path, body) {
        const options = body === undefined
            ? {}
            : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
        const response = await fetch(path, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            if (data.state) render(data.state);
            throw new Error(data.error || `Request failed (${response.status})`);
        }
        return data;
    }

    function run(path, body) {
        if (busy) return;
        busy = true;
        messageEl.textContent = '';
        api(path, body)
            .then(render)
            .catch((error) => { messageEl.textContent = error.message; })
            .finally(() => {
                busy = false;
                maybeAiMove();
            });
    }

    // ------------------------------------------------------------------- AI

    // The engine only picks among state.legalMoves; the server validates the move.
    async function maybeAiMove() {
        if (!state || busy || aiThinking || state.gameOver || state.turn !== aiColor()) return;
        const searched = state;
        const color = aiColor();
        let stale = false;
        aiThinking = true;
        messageEl.textContent = aiLoaded ? 'AI is thinking…' : 'Loading AI…';
        try {
            let move = await window.AshaAI.bestMove(searched, levelEl.value);
            aiLoaded = true;
            if (state !== searched || aiColor() !== color) { // reset, or opponent changed meanwhile
                stale = true;
                return;
            }
            if (!move) {
                console.warn('Engine offered no legal move; playing a random one.');
                move = searched.legalMoves[Math.floor(Math.random() * searched.legalMoves.length)].uci;
            }
            aiThinking = false;
            run('/api/move', { move });
        } catch (error) {
            disableAi(error.message);
        } finally {
            aiThinking = false;
            if (stale) {
                messageEl.textContent = '';
                maybeAiMove();
            }
        }
    }

    // Two players always works; the AI switches itself off where it cannot run.
    function disableAi(reason) {
        opponentEl.value = 'human';
        messageEl.textContent = `AI unavailable: ${reason}`;
        if (state) render(state);
    }

    function prepareAi() {
        if (!aiColor()) return;
        window.AshaAI.load().then(() => { aiLoaded = true; }, (error) => disableAi(error.message));
    }

    function saveSettings() {
        try {
            localStorage.setItem('asha-ai', JSON.stringify({ opponent: opponentEl.value, level: levelEl.value }));
        } catch (e) { /* storage unavailable: settings last for this page only */ }
    }

    try {
        const saved = JSON.parse(localStorage.getItem('asha-ai') || '{}');
        if (saved.opponent) opponentEl.value = saved.opponent;
        if (saved.level) levelEl.value = saved.level;
    } catch (e) { /* ignore */ }
    const unsupported = window.AshaAI.unsupportedReason();
    if (unsupported) {
        opponentEl.querySelectorAll('option:not([value="human"])').forEach((option) => { option.disabled = true; });
        opponentEl.title = `AI unavailable: ${unsupported}`;
        opponentEl.value = 'human';
    }
    opponentEl.addEventListener('change', () => {
        saveSettings();
        messageEl.textContent = '';
        if (state) render(state);
        prepareAi();
        maybeAiMove();
    });
    levelEl.addEventListener('change', saveSettings);
    prepareAi();

    function resetGame() {
        gameOverDismissed = false;
        closePopup(gameOverEl);
        run('/api/reset', {});
    }

    // ----------------------------------------------------------------- board

    function buildBoard() {
        for (let rank = 8; rank >= 1; rank--) {
            for (let file = 0; file < 8; file++) {
                const name = 'abcdefgh'[file] + rank;
                const square = document.createElement('div');
                square.className = `square ${(rank + file) % 2 === 0 ? 'light' : 'dark'}`;
                square.dataset.square = name;
                square.addEventListener('click', () => {
                    if (!suppressClick) onSquareClick(name);
                });
                squares[name] = square;
                boardEl.appendChild(square);
            }
        }
    }

    function aiColor() {
        return opponentEl.value === 'human' ? null : opponentEl.value;
    }

    function movesFrom(from) {
        if (state.turn === aiColor()) return []; // the AI's pieces cannot be moved by hand
        return state.legalMoves.filter((m) => m.from === from);
    }

    function movesBetween(from, to) {
        return state.legalMoves.filter((m) => m.from === from && m.to === to);
    }

    function renderBoard() {
        Object.entries(squares).forEach(([name, square]) => {
            square.classList.remove(...CLASSES_TO_CLEAR);
            square.replaceChildren();
            const piece = state.pieces[name];
            if (!piece) return;
            const pieceEl = document.createElement('div');
            pieceEl.className = `piece ${piece === piece.toUpperCase() ? 'white' : 'black'}`;
            pieceEl.textContent = GLYPHS[piece];
            if (movesFrom(name).length) pieceEl.classList.add('movable');
            square.appendChild(pieceEl);
        });

        const last = state.lastMove;
        if (last) {
            squares[last.from].classList.add('last-move-from');
            squares[last.to].classList.add('last-move-to');
            if (ASHA_KINDS.has(last.kind)) squares[last.to].classList.add('last-move-asha');
        }
        if (state.checkSquare) squares[state.checkSquare].classList.add('in-check');
    }

    // Pointer-event dragging works for mouse, pen and touch alike.
    function squareAt(x, y) {
        return document.elementFromPoint(x, y)?.closest('.square')?.dataset.square ?? null;
    }

    boardEl.addEventListener('pointerdown', (e) => {
        const from = e.target.closest('.square')?.dataset.square;
        if (!state || busy || aiThinking || e.button !== 0 || !from || !movesFrom(from).length) return;
        drag = { from, x: e.clientX, y: e.clientY, ghost: null };
    });

    window.addEventListener('pointermove', (e) => {
        if (!drag) return;
        if (!drag.ghost) {
            if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 5) return;
            select(drag.from);
            const pieceEl = squares[drag.from].querySelector('.piece');
            drag.ghost = pieceEl.cloneNode(true);
            drag.ghost.classList.add('drag-ghost');
            drag.ghost.style.width = `${squares[drag.from].offsetWidth}px`;
            drag.ghost.style.height = `${squares[drag.from].offsetHeight}px`;
            document.body.appendChild(drag.ghost);
            pieceEl.classList.add('drag-source');
        }
        e.preventDefault();
        drag.ghost.style.left = `${e.clientX}px`;
        drag.ghost.style.top = `${e.clientY}px`;
        const over = squareAt(e.clientX, e.clientY);
        Object.entries(squares).forEach(([name, square]) => {
            square.classList.toggle('drag-over', name === over && movesBetween(drag.from, name).length > 0);
        });
    });

    function endDrag(e, drop) {
        if (!drag) return;
        const { from, ghost } = drag;
        drag = null;
        if (!ghost) return; // a plain click; the click handler takes over
        ghost.remove();
        squares[from].querySelector('.piece')?.classList.remove('drag-source');
        Object.values(squares).forEach((square) => square.classList.remove('drag-over'));
        suppressClick = true;
        setTimeout(() => { suppressClick = false; }, 0);
        const to = drop ? squareAt(e.clientX, e.clientY) : null;
        if (to) attempt(movesBetween(from, to));
    }

    window.addEventListener('pointerup', (e) => endDrag(e, true));
    window.addEventListener('pointercancel', (e) => endDrag(e, false));

    function clearSelection() {
        selected = null;
        Object.values(squares).forEach((square) => {
            square.classList.remove('selected', 'valid-move', 'valid-capture', 'valid-kings-step', 'valid-pawn-lateral');
        });
    }

    function select(name) {
        clearSelection();
        selected = name;
        squares[name].classList.add('selected');
        movesFrom(name).forEach((move) => squares[move.to].classList.add(TARGET_CLASS[move.kind]));
    }

    function onSquareClick(name) {
        if (!state || busy || aiThinking) return;
        if (selected) {
            const candidates = movesBetween(selected, name);
            if (candidates.length) {
                attempt(candidates);
                return;
            }
            if (name === selected) {
                clearSelection();
                return;
            }
        }
        if (movesFrom(name).length) select(name);
        else clearSelection();
    }

    function attempt(candidates) {
        if (!candidates.length) return;
        if (candidates.length === 1) {
            submitMove(candidates[0].uci);
            return;
        }
        // Several moves share from/to only when promoting: let the player choose.
        const color = state.turn === 'white';
        promotionChoices.replaceChildren();
        PROMOTION_ORDER.forEach((piece) => {
            const move = candidates.find((m) => m.promotion === piece);
            if (!move) return;
            const button = document.createElement('button');
            button.className = `promotion-choice piece ${color ? 'white' : 'black'}`;
            button.dataset.promotion = piece;
            button.textContent = GLYPHS[color ? piece.toUpperCase() : piece];
            button.addEventListener('click', () => {
                closePopup(promotionEl);
                submitMove(move.uci);
            });
            promotionChoices.appendChild(button);
        });
        openPopup(promotionEl);
    }

    function submitMove(uci) {
        clearSelection();
        run('/api/move', { move: uci });
    }

    // ---------------------------------------------------------------- status

    function renderStatus() {
        turnEl.textContent = state.turn === 'white' ? 'White' : 'Black';
        const result = state.result;
        if (result) {
            const [title] = TERMINATIONS[result.termination];
            statusEl.textContent = result.winner ? `${title} — ${capitalize(result.winner)} wins` : title;
        } else if (state.check) {
            statusEl.textContent = `${state.turn.toUpperCase()} IS IN CHECK!`;
        } else {
            statusEl.textContent = '';
        }
        resetButton.classList.toggle('highlight-reset', state.gameOver);

        claimButtons.replaceChildren();
        state.claimableDraws.forEach((reason) => {
            const button = document.createElement('button');
            button.className = 'claim-btn';
            button.textContent = CLAIM_LABELS[reason];
            button.addEventListener('click', () => run('/api/claim-draw', { reason }));
            claimButtons.appendChild(button);
        });
    }

    function renderHistory() {
        historyEl.replaceChildren();
        let row = null;
        state.history.forEach((entry) => {
            if (entry.color === 'white' || !row) {
                row = document.createElement('div');
                row.className = 'move-entry';
                const number = document.createElement('span');
                number.className = 'move-number';
                number.textContent = `${Math.ceil(entry.ply / 2)}.`;
                row.appendChild(number);
                if (entry.color === 'black') row.appendChild(notationSpan({ notation: '…', kind: '' }));
                historyEl.appendChild(row);
            }
            row.appendChild(notationSpan(entry));
        });
        historyEl.scrollTop = historyEl.scrollHeight;
    }

    function notationSpan(entry) {
        const span = document.createElement('span');
        span.className = `move-notation ${ASHA_KINDS.has(entry.kind) ? 'asha-move' : ''}`;
        span.textContent = entry.notation;
        if (entry.uci) span.title = `${entry.uci} (${entry.kind.replace('_', ' ')})`;
        return span;
    }

    function renderGameOver() {
        if (!state.result) {
            closePopup(gameOverEl);
            return;
        }
        const [title, subtitle] = TERMINATIONS[state.result.termination];
        document.getElementById('game-over-title').textContent =
            state.result.winner ? `${capitalize(state.result.winner)} Wins!` : title;
        document.getElementById('game-over-subtitle').textContent = subtitle;
        if (!gameOverDismissed) openPopup(gameOverEl);
    }

    function capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function render(newState) {
        state = newState;
        selected = null;
        closePopup(promotionEl);
        renderBoard();
        renderStatus();
        renderHistory();
        renderGameOver();
    }

    resetButton.addEventListener('click', resetGame);
    buildBoard();
    run('/api/state');
});
