'use strict';

// UCI over stdin/stdout for the Fairy-Stockfish WebAssembly build that ships
// with the game (static/vendor/fairy-stockfish), so the lab measures the same
// engine players meet. The Asha variant is read from static/js/asha-ai.js, not
// copied, and written to /asha.ini inside the engine's virtual file system.
// The client selects it with "setoption name VariantPath value /asha.ini".

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const ROOT = path.resolve(__dirname, '..');
const VENDOR = path.join(ROOT, 'static', 'vendor', 'fairy-stockfish');

function ashaVariant() {
    const source = fs.readFileSync(path.join(ROOT, 'static', 'js', 'asha-ai.js'), 'utf8');
    const block = source.match(/const VARIANT = \[([\s\S]*?)\]\.join/);
    if (!block) throw new Error('VARIANT not found in static/js/asha-ai.js');
    return [...block[1].matchAll(/'([^']*)'/g)].map((m) => m[1]).join('\n');
}

(async () => {
    const Stockfish = require(path.join(VENDOR, 'stockfish.js'));
    const sf = await Stockfish({
        locateFile: (file) => path.join(VENDOR, file),
        wasmBinary: fs.readFileSync(path.join(VENDOR, 'stockfish.wasm')),
    });
    const variant = ashaVariant();
    sf.FS.writeFile('/asha.ini', `${variant}\n`);
    sf.addMessageListener((line) => process.stdout.write(`${line}\n`));
    process.stdout.write(`info string asha-variant ${JSON.stringify(variant)}\n`);

    const input = readline.createInterface({ input: process.stdin });
    input.on('line', (line) => {
        if (line.trim() === 'quit') {
            sf.terminate();
            process.exit(0);
        }
        sf.postMessage(line);
    });
    input.on('close', () => {
        sf.terminate();
        process.exit(0);
    });
})().catch((error) => {
    process.stderr.write(`${error.stack || error}\n`);
    process.exit(1);
});
