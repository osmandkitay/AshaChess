'use strict';

// Rendering and input only: every rule decision (legal moves, move kinds, check,
// results, notation) comes from the server state.
document.addEventListener('DOMContentLoaded', () => {
    const FILES = 'abcdefgh';
    const PROMOTION_ORDER = ['q', 'r', 'b', 'n'];
    const TARGET_CLASS = {
        quiet: 't-move',
        castling: 't-move',
        capture: 't-capture',
        en_passant: 't-capture',
        kings_step: 't-asha',
        pawn_lateral: 't-asha',
        pawn_diagonal: 't-asha',
    };
    const ASHA_KINDS = new Set(['kings_step', 'pawn_lateral', 'pawn_diagonal']);
    const VALUES = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 };
    const TERMINATIONS = {
        checkmate: 'Checkmate.',
        stalemate: 'Stalemate: no legal move, and not in check.',
        insufficient_material: 'Neither side can checkmate any more.',
        fivefold_repetition: 'The same position occurred five times.',
        seventyfive_moves: '75 moves each without a capture or pawn move.',
        threefold_repetition: 'Threefold repetition, claimed.',
        fifty_moves: '50-move rule, claimed.',
    };
    const CLAIM_LABELS = {
        threefold_repetition: 'Claim draw · repetition',
        fifty_moves: 'Claim draw · 50 moves',
    };
    const LEVEL_NAMES = { easy: 'Easy', medium: 'Medium', hard: 'Hard' };
    const TARGET_CLASSES = ['target', 't-move', 't-capture', 't-asha'];
    const STATE_CLASSES = ['selected', 'last', 'asha', 'check', 'drag-over', 'has-movable', ...TARGET_CLASSES];

    const $ = (id) => document.getElementById(id);
    const boardEl = $('chessboard');
    const promotionEl = $('promotion');
    const overlayEl = $('overlay');
    const chooserEl = $('chooser');
    const resultEl = $('result');
    const movesEl = $('moves');
    const hintEl = $('hint');
    const claimsEl = $('claims');
    const toastEl = $('toast');
    const newGameButton = $('new-game');
    const bars = { top: $('bar-top'), bottom: $('bar-bottom') };
    const hoverDevice = window.matchMedia('(hover: hover)').matches;

    let state = null;
    let settings = loadSettings();
    let orientation = null;
    let selected = null;
    let drag = null; // { from, x, y, ghost, touch } while a piece is held
    let suppressClick = false;
    let busy = false; // one request at a time, so responses cannot arrive out of order
    let pending = null; // uci of a move already shown on the board, awaiting the server
    let gameId = 0; // bumped by every new game, so late AI answers are dropped
    let aiThinking = false;
    let aiStatus = null; // 'loading' | 'thinking' | 'slow'
    let aiLoaded = false;
    let resultShown = false;
    const squares = {};

    // --------------------------------------------------------------- settings

    function loadSettings() {
        const defaults = { mode: 'human', human: 'white', level: 'medium' };
        try {
            return { ...defaults, ...JSON.parse(localStorage.getItem('asha-settings') || '{}') };
        } catch (e) {
            return defaults;
        }
    }

    function saveSettings() {
        try {
            localStorage.setItem('asha-settings', JSON.stringify(settings));
        } catch (e) { /* storage unavailable: settings last for this page only */ }
    }

    const other = (color) => (color === 'white' ? 'black' : 'white');
    const aiColor = () => (settings.mode === 'ai' ? other(settings.human) : null);
    const colorOf = (piece) => (piece === piece.toUpperCase() ? 'white' : 'black');
    const pieceClass = (piece) => (colorOf(piece) === 'white' ? 'w' : 'b') + piece.toUpperCase();

    // ------------------------------------------------------------------ sound

    // Short synthesized clicks: no audio files to download.
    const sound = (() => {
        let ctx = null;
        let enabled = true;
        try { enabled = localStorage.getItem('asha-sound') !== 'off'; } catch (e) { /* default on */ }

        function unlock() {
            if (!enabled || ctx) return;
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) ctx = new AudioContext();
        }

        function knock(t, freq, gain) {
            const osc = ctx.createOscillator();
            const env = ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, t);
            osc.frequency.exponentialRampToValueAtTime(freq * 0.55, t + 0.08);
            env.gain.setValueAtTime(gain, t);
            env.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);
            osc.connect(env).connect(ctx.destination);
            osc.start(t);
            osc.stop(t + 0.1);

            const noise = ctx.createBufferSource();
            const buffer = ctx.createBuffer(1, ctx.sampleRate * 0.03, ctx.sampleRate);
            const data = buffer.getChannelData(0);
            for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / data.length) ** 3;
            noise.buffer = buffer;
            const filter = ctx.createBiquadFilter();
            filter.type = 'bandpass';
            filter.frequency.value = freq * 9;
            const noiseGain = ctx.createGain();
            noiseGain.gain.value = gain * 0.9;
            noise.connect(filter).connect(noiseGain).connect(ctx.destination);
            noise.start(t);
        }

        function chime(t, freq) {
            const osc = ctx.createOscillator();
            const env = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = freq;
            env.gain.setValueAtTime(0.0001, t);
            env.gain.exponentialRampToValueAtTime(0.12, t + 0.02);
            env.gain.exponentialRampToValueAtTime(0.0001, t + 0.9);
            osc.connect(env).connect(ctx.destination);
            osc.start(t);
            osc.stop(t + 1);
        }

        function play(kind) {
            if (!enabled || !ctx) return;
            if (ctx.state === 'suspended') ctx.resume();
            const t = ctx.currentTime + 0.005;
            if (kind === 'capture') {
                knock(t, 150, 0.32);
                knock(t + 0.045, 110, 0.22);
            } else if (kind === 'end') {
                chime(t, 523.25);
                chime(t + 0.12, 659.25);
                chime(t + 0.24, 783.99);
            } else {
                knock(t, 190, 0.26);
            }
        }

        function toggle() {
            enabled = !enabled;
            try { localStorage.setItem('asha-sound', enabled ? 'on' : 'off'); } catch (e) { /* ignore */ }
            unlock();
            return enabled;
        }

        return { unlock, play, toggle, get enabled() { return enabled; } };
    })();

    const soundButton = $('sound-btn');
    soundButton.setAttribute('aria-pressed', String(sound.enabled));
    soundButton.addEventListener('click', () => {
        soundButton.setAttribute('aria-pressed', String(sound.toggle()));
    });
    window.addEventListener('pointerdown', sound.unlock, { capture: true });

    // ------------------------------------------------------------------ toast

    let toastTimer = null;
    function toast(text, ms = 3200) {
        toastEl.textContent = text;
        toastEl.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toastEl.classList.remove('show'), ms);
    }

    // --------------------------------------------------------------- dialogs

    document.querySelectorAll('[data-open]').forEach((button) => {
        button.addEventListener('click', () => openDialog($(button.dataset.open)));
    });
    $('about-btn').addEventListener('click', () => openDialog($('about')));
    document.querySelectorAll('dialog').forEach((dialog) => {
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog || e.target.closest('[data-dismiss]')) closeDialog(dialog);
        });
    });

    function openDialog(dialog) {
        if (dialog.showModal) dialog.showModal();
        else dialog.setAttribute('open', '');
        dialog.querySelector('.sheet-body').scrollTop = 0;
    }

    function closeDialog(dialog) {
        if (dialog.close) dialog.close();
        else dialog.removeAttribute('open');
    }

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
        api(path, body)
            .then(render)
            .catch((error) => {
                pending = null;
                if (state) renderBoard();
                toast(error instanceof TypeError ? 'Connection lost. Try again.' : error.message);
            })
            .finally(() => {
                busy = false;
                if (state) renderBoard(); // pieces become movable again
                maybeAiMove();
            });
    }

    // -------------------------------------------------------------------- AI

    const sleep = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });

    // The engine only picks among state.legalMoves; the server validates the move.
    async function maybeAiMove() {
        if (!state || busy || aiThinking || state.gameOver || state.turn !== aiColor() || !chooserEl.hidden) return;
        const searched = state;
        const game = gameId;
        const started = Date.now();
        let slowTimer = null;
        aiThinking = true;
        try {
            if (!aiLoaded) {
                setAiStatus('loading');
                await window.AshaAI.load();
                aiLoaded = true;
            }
            setAiStatus('thinking');
            slowTimer = setTimeout(() => setAiStatus('slow'), 5000);
            let move = await window.AshaAI.bestMove(searched, settings.level);
            if (state !== searched || game !== gameId || searched.turn !== aiColor()) return; // the game moved on
            if (!move) {
                console.warn('Engine offered no legal move; playing a random one.');
                move = searched.legalMoves[Math.floor(Math.random() * searched.legalMoves.length)].uci;
            }
            await sleep(Math.max(0, 450 - (Date.now() - started))); // let the player's move land first
            if (state !== searched || game !== gameId) return;
            aiThinking = false;
            setAiStatus(null);
            run('/api/move', { move });
        } catch (error) {
            if (game === gameId) {
                aiThinking = false;
                disableAi(error.message);
            }
        } finally {
            clearTimeout(slowTimer);
            if (aiThinking) {
                aiThinking = false;
                setAiStatus(null);
                maybeAiMove(); // the position changed meanwhile
            }
        }
    }

    function setAiStatus(status) {
        aiStatus = status;
        if (state) renderBars();
    }

    // Two players always works; the AI switches itself off where it cannot run.
    function disableAi(reason) {
        settings.mode = 'human';
        saveSettings();
        aiStatus = null;
        buildBoard();
        if (state) render(state);
        console.warn(`AI unavailable: ${reason}`);
        toast('The AI could not start here. Continuing as a 2-player game.', 6000);
    }

    // ----------------------------------------------------------------- board

    function buildBoard() {
        const bottom = settings.mode === 'ai' ? settings.human : 'white';
        if (orientation === bottom) return;
        orientation = bottom;
        boardEl.replaceChildren();
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const file = orientation === 'white' ? col : 7 - col;
                const rank = orientation === 'white' ? 8 - row : row + 1;
                const name = FILES[file] + rank;
                const square = document.createElement('div');
                square.className = `square ${(rank + file) % 2 === 1 ? 'dark' : 'light'}`; // a1 is dark
                square.dataset.square = name;
                square.dataset.row = row;
                square.dataset.col = col;
                if (col === 0) square.appendChild(coord('rank', rank));
                if (row === 7) square.appendChild(coord('file', FILES[file]));
                square.addEventListener('click', () => {
                    if (!suppressClick) onSquareClick(name);
                });
                squares[name] = square;
                boardEl.appendChild(square);
            }
        }
    }

    function coord(kind, text) {
        const span = document.createElement('span');
        span.className = `coord ${kind}`;
        span.textContent = text;
        return span;
    }

    function canMove() {
        return state && !busy && !aiThinking && !state.gameOver && state.turn !== aiColor() && overlayEl.hidden;
    }

    function movesFrom(from) {
        if (!canMove()) return [];
        return state.legalMoves.filter((m) => m.from === from);
    }

    function movesBetween(from, to) {
        return state.legalMoves.filter((m) => m.from === from && m.to === to);
    }

    // Pieces already in place are kept, so a slide in progress is not cut short.
    function renderBoard() {
        Object.entries(squares).forEach(([name, square]) => {
            square.classList.remove(...STATE_CLASSES);
            const piece = state.pieces[name];
            let el = square.querySelector('.piece');
            if (el && el.dataset.piece !== piece) {
                el.remove();
                el = null;
            }
            if (!piece) return;
            if (!el) {
                el = document.createElement('div');
                el.className = `piece ${pieceClass(piece)}`;
                el.dataset.piece = piece;
                square.appendChild(el);
            }
            const movable = movesFrom(name).length > 0;
            el.classList.toggle('movable', movable);
            square.classList.toggle('has-movable', movable);
        });
        const last = state.lastMove;
        if (last) {
            [last.from, last.to].forEach((name) => {
                squares[name].classList.add('last');
                if (ASHA_KINDS.has(last.kind)) squares[name].classList.add('asha');
            });
        }
        if (state.checkSquare) squares[state.checkSquare].classList.add('check');
        if (selected && movesFrom(selected).length) select(selected);
        else selected = null;
    }

    // Slide the piece now on `to` in from where `from` is.
    function slide(from, to) {
        const el = squares[to].querySelector('.piece');
        if (!el) return;
        const a = squares[from].getBoundingClientRect();
        const b = squares[to].getBoundingClientRect();
        el.classList.remove('sliding');
        el.style.transform = `translate(${a.left - b.left}px, ${a.top - b.top}px)`;
        el.getBoundingClientRect(); // commit the start position
        el.classList.add('sliding');
        el.style.transform = '';
        el.addEventListener('transitionend', () => el.classList.remove('sliding'), { once: true });
    }

    function slideCastlingRook(move) {
        const rank = move.to[1];
        const kingside = move.to[0] === 'g';
        slide(`${kingside ? 'h' : 'a'}${rank}`, `${kingside ? 'f' : 'd'}${rank}`);
    }

    // Pointer-event dragging works for mouse, pen and touch; tapping is the main input.
    function squareAt(x, y) {
        return document.elementFromPoint(x, y)?.closest('.square')?.dataset.square ?? null;
    }

    boardEl.addEventListener('pointerdown', (e) => {
        const from = e.target.closest('.square')?.dataset.square;
        if (e.button !== 0 || !from || !movesFrom(from).length) return;
        drag = { from, x: e.clientX, y: e.clientY, ghost: null, touch: e.pointerType !== 'mouse' };
    });

    window.addEventListener('pointermove', (e) => {
        if (!drag) return;
        if (!drag.ghost) {
            if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < (drag.touch ? 10 : 5)) return;
            const source = squares[drag.from].querySelector('.piece');
            if (!source || !canMove()) {
                drag = null;
                return;
            }
            if (selected !== drag.from) select(drag.from);
            drag.ghost = source.cloneNode(true);
            drag.ghost.classList.add('drag-ghost');
            drag.ghost.style.width = `${squares[drag.from].offsetWidth}px`;
            drag.ghost.style.height = `${squares[drag.from].offsetHeight}px`;
            document.body.appendChild(drag.ghost);
            source.classList.add('drag-source');
        }
        e.preventDefault();
        drag.ghost.style.left = `${e.clientX}px`;
        drag.ghost.style.top = `${e.clientY}px`;
        const over = squareAt(e.clientX, e.clientY);
        Object.entries(squares).forEach(([name, square]) => {
            square.classList.toggle('drag-over', name === over && movesBetween(drag.from, name).length > 0);
        });
    }, { passive: false });

    function endDrag(e, drop) {
        if (!drag) return;
        const { from, ghost } = drag;
        drag = null;
        if (!ghost) return; // a plain tap; the click handler takes over
        ghost.remove();
        squares[from].querySelector('.piece')?.classList.remove('drag-source');
        Object.values(squares).forEach((square) => square.classList.remove('drag-over'));
        suppressClick = true;
        setTimeout(() => { suppressClick = false; }, 0);
        const to = drop ? squareAt(e.clientX, e.clientY) : null;
        if (to && to !== from && canMove()) attempt(movesBetween(from, to), true);
    }

    window.addEventListener('pointerup', (e) => endDrag(e, true));
    window.addEventListener('pointercancel', (e) => endDrag(e, false));

    function clearSelection() {
        selected = null;
        Object.values(squares).forEach((square) => square.classList.remove('selected', ...TARGET_CLASSES));
    }

    function select(name) {
        clearSelection();
        selected = name;
        squares[name].classList.add('selected');
        movesFrom(name).forEach((move) => squares[move.to].classList.add('target', TARGET_CLASS[move.kind]));
    }

    function onSquareClick(name) {
        if (!canMove()) return;
        if (selected) {
            const candidates = movesBetween(selected, name);
            if (candidates.length) {
                attempt(candidates, false);
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

    function attempt(candidates, dragged) {
        if (!candidates.length) return;
        if (candidates.length === 1) submitMove(candidates[0], dragged);
        else choosePromotion(candidates, dragged); // several moves share from/to only when promoting
    }

    function choosePromotion(candidates, dragged) {
        clearSelection();
        const target = squares[candidates[0].to];
        const row = Number(target.dataset.row);
        const col = Number(target.dataset.col);
        const color = state.turn === 'white' ? 'w' : 'b';
        const column = document.createElement('div');
        column.className = 'promotion-col';
        column.style.left = `${col * 12.5}%`;
        if (row === 0) column.style.top = '0';
        else column.style.bottom = `${(7 - row) * 12.5}%`;
        const order = row === 0 ? PROMOTION_ORDER : [...PROMOTION_ORDER].reverse();
        order.forEach((piece) => {
            const move = candidates.find((m) => m.promotion === piece);
            if (!move) return;
            const button = document.createElement('button');
            button.type = 'button';
            button.setAttribute('aria-label', { q: 'Queen', r: 'Rook', b: 'Bishop', n: 'Knight' }[piece]);
            const icon = document.createElement('span');
            icon.className = `p ${color}${piece.toUpperCase()}`;
            button.appendChild(icon);
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                hidePromotion();
                submitMove(move, dragged);
            });
            column.appendChild(button);
        });
        promotionEl.replaceChildren(column);
        promotionEl.hidden = false;
        column.querySelector('button').focus({ preventScroll: true });
    }

    function hidePromotion() {
        promotionEl.hidden = true;
        promotionEl.replaceChildren();
    }

    promotionEl.addEventListener('click', () => {
        hidePromotion();
        clearSelection();
    });

    // Show the move at once; the server's answer confirms (or undoes) it.
    function submitMove(move, dragged) {
        clearSelection();
        pending = move.uci;
        const from = squares[move.from];
        const to = squares[move.to];
        const moving = from.querySelector('.piece');
        to.querySelector('.piece')?.remove();
        if (moving) to.appendChild(moving);
        Object.values(squares).forEach((square) => square.classList.remove('has-movable', 'last', 'asha', 'check'));
        from.classList.add('last');
        to.classList.add('last');
        if (ASHA_KINDS.has(move.kind)) [from, to].forEach((square) => square.classList.add('asha'));
        if (!dragged) slide(move.from, move.to);
        sound.play(move.capture ? 'capture' : 'move');
        run('/api/move', { move: move.uci });
    }

    // ---------------------------------------------------------------- panels

    function renderBars() {
        renderBar(bars.top, other(orientation));
        renderBar(bars.bottom, orientation);
    }

    function renderBar(bar, color) {
        const isAi = aiColor() === color;
        const toMove = !state.gameOver && state.turn === color;
        bar.classList.toggle('active', toMove);
        bar.querySelector('.side-disc').className = `side-disc ${color}`;

        const name = bar.querySelector('.player-name');
        if (settings.mode === 'ai') {
            name.textContent = isAi ? 'AI' : 'You';
            if (isAi) {
                const level = document.createElement('small');
                level.textContent = LEVEL_NAMES[settings.level] || '';
                name.appendChild(level);
            }
        } else {
            name.textContent = color === 'white' ? 'White' : 'Black';
        }

        renderCaptures(bar.querySelector('.captures'), color);

        const status = bar.querySelector('.player-status');
        status.replaceChildren();
        if (state.gameOver) {
            const { winner } = state.result;
            if (winner === color) status.appendChild(chip('Winner', 'turn'));
            else if (!winner) status.appendChild(chip('Draw', 'quiet'));
            return;
        }
        if (!toMove) return;
        if (state.check) status.appendChild(chip('Check', 'check'));
        if (isAi && aiStatus) {
            const label = { loading: 'Loading engine', thinking: 'Thinking', slow: 'Still thinking' }[aiStatus];
            const thinking = chip(label, 'ai');
            const dots = document.createElement('span');
            dots.className = 'thinking';
            dots.setAttribute('aria-hidden', 'true');
            dots.innerHTML = '<i></i><i></i><i></i>';
            thinking.appendChild(dots);
            status.appendChild(thinking);
        } else if (!isAi && !state.check) {
            status.appendChild(chip(settings.mode === 'ai' ? 'Your move' : 'To move', 'turn'));
        }
    }

    function chip(text, kind) {
        const span = document.createElement('span');
        span.className = `chip ${kind}`;
        span.textContent = text;
        return span;
    }

    // Pieces this side has captured, and its material lead.
    function renderCaptures(el, color) {
        el.replaceChildren();
        const taken = state.history
            .filter((entry) => entry.color === color && entry.captured)
            .map((entry) => entry.captured.toLowerCase())
            .sort((a, b) => VALUES[b] - VALUES[a]);
        const prefix = color === 'white' ? 'b' : 'w';
        taken.forEach((piece, i) => {
            const icon = document.createElement('span');
            icon.className = `p ${prefix}${piece.toUpperCase()}`;
            if (i > 0 && taken[i - 1] !== piece) icon.classList.add('gap');
            el.appendChild(icon);
        });
        let lead = 0;
        Object.values(state.pieces).forEach((piece) => {
            lead += (colorOf(piece) === color ? 1 : -1) * VALUES[piece.toLowerCase()];
        });
        if (lead > 0) {
            const adv = document.createElement('span');
            adv.className = 'adv';
            adv.textContent = `+${lead}`;
            el.appendChild(adv);
        }
    }

    function renderMoves() {
        movesEl.replaceChildren();
        let row = null;
        state.history.forEach((entry, i) => {
            if (entry.color === 'white' || !row) {
                row = document.createElement('li');
                const number = document.createElement('span');
                number.className = 'move-no';
                number.textContent = `${Math.ceil(entry.ply / 2)}.`;
                row.appendChild(number);
                if (entry.color === 'black') row.appendChild(moveSpan({ notation: '…', kind: '' }, false));
                movesEl.appendChild(row);
            }
            row.appendChild(moveSpan(entry, i === state.history.length - 1));
        });
        hintEl.hidden = state.history.length > 0 || state.gameOver;
        movesEl.scrollLeft = movesEl.scrollWidth;
        movesEl.scrollTop = movesEl.scrollHeight;
    }

    function moveSpan(entry, current) {
        const span = document.createElement('span');
        span.className = 'move';
        if (ASHA_KINDS.has(entry.kind)) span.classList.add('asha');
        if (current) span.classList.add('current');
        span.textContent = entry.notation;
        if (entry.uci) span.title = `${entry.uci} (${entry.kind.replace('_', ' ')})`;
        return span;
    }

    function renderClaims() {
        claimsEl.replaceChildren();
        if (state.turn === aiColor()) return;
        state.claimableDraws.forEach((reason) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn';
            button.textContent = CLAIM_LABELS[reason];
            button.addEventListener('click', () => run('/api/claim-draw', { reason }));
            claimsEl.appendChild(button);
        });
    }

    function renderResult() {
        newGameButton.classList.toggle('btn-primary', state.gameOver);
        if (!state.result) {
            resultShown = false;
            if (!resultEl.hidden) hideOverlay();
            return;
        }
        if (resultShown) return;
        resultShown = true;
        const { winner, termination } = state.result;
        let title;
        if (!winner) title = 'Draw';
        else if (settings.mode === 'ai') title = winner === settings.human ? 'You win' : 'AI wins';
        else title = `${winner === 'white' ? 'White' : 'Black'} wins`;
        $('result-title').textContent = title;
        const moves = Math.ceil(state.history.length / 2);
        $('result-sub').textContent = `${TERMINATIONS[termination]} ${moves} move${moves === 1 ? '' : 's'}.`;
        sound.play('end');
        setTimeout(() => {
            if (state.result && chooserEl.hidden) showOverlay(resultEl);
        }, 650); // let the final move be seen first
    }

    function render(newState) {
        const previous = state;
        state = newState;
        hidePromotion();
        renderBoard();
        const last = state.lastMove;
        const fresh = last && previous && last.ply === previous.history.length + 1;
        if (fresh && last.uci !== pending) {
            slide(last.from, last.to);
            if (last.kind === 'castling') slideCastlingRook(last);
            sound.play(last.capture ? 'capture' : 'move');
        } else if (fresh && last.kind === 'castling') {
            slideCastlingRook(last);
        }
        pending = null;
        renderBars();
        renderMoves();
        renderClaims();
        renderResult();
    }

    // -------------------------------------------------------- overlay cards

    function showOverlay(card) {
        clearSelection();
        [chooserEl, resultEl].forEach((c) => { c.hidden = c !== card; });
        overlayEl.hidden = false;
        if (state) renderBoard();
    }

    function hideOverlay() {
        overlayEl.hidden = true;
        chooserEl.hidden = true;
        resultEl.hidden = true;
        if (state) renderBoard();
        maybeAiMove();
    }

    overlayEl.addEventListener('click', (e) => {
        if (e.target.closest('[data-close]')) hideOverlay();
    });

    function openChooser() {
        const ongoing = Boolean(state && state.history.length);
        chooserEl.querySelector('.card-close').hidden = !ongoing;
        showStep('mode');
        showOverlay(chooserEl);
    }

    function showStep(step) {
        chooserEl.querySelectorAll('.step').forEach((el) => { el.hidden = el.dataset.step !== step; });
    }

    const unsupported = window.AshaAI.unsupportedReason();
    if (unsupported) {
        $('choose-ai').disabled = true;
        const note = $('ai-note');
        note.hidden = false;
        note.textContent = 'The AI needs a newer browser (iOS 16.4+, Chrome 91+). 2 Players works everywhere.';
        console.info(`AI unavailable: ${unsupported}`);
    }

    $('choose-2p').addEventListener('click', () => startGame({ mode: 'human' }));
    $('choose-ai').addEventListener('click', () => {
        showStep('level');
        renderColorChoice();
        window.AshaAI.load().then( // start downloading while the level is chosen
            () => { aiLoaded = true; },
            (error) => { $('engine-note').textContent = `The AI could not load (${error.message}).`; },
        );
    });
    $('choose-back').addEventListener('click', () => showStep('mode'));
    chooserEl.querySelectorAll('[data-color]').forEach((button) => {
        button.addEventListener('click', () => {
            settings.human = button.dataset.color;
            renderColorChoice();
        });
    });
    chooserEl.querySelectorAll('[data-level]').forEach((button) => {
        button.addEventListener('click', () => startGame({ mode: 'ai', level: button.dataset.level }));
    });

    function renderColorChoice() {
        chooserEl.querySelectorAll('[data-color]').forEach((button) => {
            button.setAttribute('aria-checked', String(button.dataset.color === settings.human));
        });
    }

    function startGame(choice) {
        settings = { ...settings, ...choice };
        saveSettings();
        gameId++;
        aiStatus = null;
        resultShown = false;
        selected = null;
        overlayEl.hidden = true;
        chooserEl.hidden = true;
        resultEl.hidden = true;
        buildBoard();
        state = null; // a new game, not a move to animate
        busy = false;
        run('/api/reset', {});
    }

    $('result-new').addEventListener('click', openChooser);
    newGameButton.addEventListener('click', openChooser);

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape' || document.querySelector('dialog[open]')) return;
        if (!promotionEl.hidden) {
            hidePromotion();
            clearSelection();
        } else if (!resultEl.hidden || (!chooserEl.hidden && !chooserEl.querySelector('.card-close').hidden)) {
            hideOverlay();
        } else if (selected) {
            clearSelection();
        }
    });

    // ------------------------------------------------------------------ start

    hintEl.firstChild.textContent = `${hoverDevice ? 'Click' : 'Tap'} a piece to see its moves. `;
    if (settings.mode === 'ai' && unsupported) settings.mode = 'human';
    buildBoard();
    busy = true;
    api('/api/state')
        .then((initial) => {
            resultShown = Boolean(initial.result); // a finished game on reload: show the board, not the card
            busy = false;
            render(initial);
            if (!initial.history.length) openChooser();
            else maybeAiMove();
        })
        .catch(() => {
            busy = false;
            toast('Could not reach the server. Reload to try again.', 8000);
        });
});
