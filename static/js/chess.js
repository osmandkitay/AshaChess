document.addEventListener('DOMContentLoaded', () => {
    const chessboard = document.getElementById('chessboard');
    const turnDisplay = document.getElementById('turn');
    const checkStatus = document.getElementById('check-status');
    const resetButton = document.getElementById('reset-button');
    
    // New UI elements
    const manifestBtn = document.getElementById('manifest-btn');
    const rulesBtn = document.getElementById('rules-btn');
    const manifestPopup = document.getElementById('manifest-popup');
    const rulesPopup = document.getElementById('rules-popup');
    const moveHistoryList = document.getElementById('move-history-list');
    
    // Move history tracking
    let moveHistory = [];
    let moveCounter = 1;
    
    let selectedSquare = null;
    let boardState = null;
    let draggedPiece = null;
    let draggedPieceSquare = null;
    let isDragging = false;  // Flag to track if a drag operation is in progress
    
    // Popup functionality
    manifestBtn.addEventListener('click', () => {
        showPopup(manifestPopup);
    });
    
    rulesBtn.addEventListener('click', () => {
        showPopup(rulesPopup);
    });
    
    // Close popups when clicking outside
    manifestPopup.addEventListener('click', (e) => {
        if (e.target === manifestPopup) {
            hidePopup(manifestPopup);
        }
    });
    
    rulesPopup.addEventListener('click', (e) => {
        if (e.target === rulesPopup) {
            hidePopup(rulesPopup);
        }
    });
    
    // ESC key to close popups
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hidePopup(manifestPopup);
            hidePopup(rulesPopup);
        }
    });
    
    function showPopup(popup) {
        popup.classList.add('active');
    }
    
    function hidePopup(popup) {
        popup.classList.remove('active');
    }
    
    function addMoveToHistory(move, piece, isCapture, isCheck, isCheckmate, isKingsStep) {
        const moveNotation = generateMoveNotation(move, piece, isCapture, isCheck, isCheckmate, isKingsStep);
        
        // Add to history array
        if (boardState.turn === 'white') {
            // White's move just finished, so this is the end of a white move
            moveHistory.push({
                number: moveCounter,
                white: moveNotation,
                black: null
            });
        } else {
            // Black's move just finished
            if (moveHistory.length > 0 && moveHistory[moveHistory.length - 1].black === null) {
                moveHistory[moveHistory.length - 1].black = moveNotation;
                moveCounter++;
            } else {
                // This shouldn't normally happen, but handle it
                moveHistory.push({
                    number: moveCounter,
                    white: null,
                    black: moveNotation
                });
                moveCounter++;
            }
        }
        
        updateMoveHistoryDisplay();
    }
    
    function generateMoveNotation(move, piece, isCapture, isCheck, isCheckmate, isKingsStep) {
        let notation = '';
        
        // Piece notation (except for pawns)
        if (piece.toLowerCase() !== 'p') {
            notation += piece.toUpperCase();
        }
        
        // Capture notation
        if (isCapture) {
            if (piece.toLowerCase() === 'p') {
                notation += move.from[0]; // Add file for pawn captures
            }
            notation += 'x';
        }
        
        // Destination square
        notation += move.to;
        
        // King's Step notation
        if (isKingsStep) {
            notation += '(KS)';
        }
        
        // Check/Checkmate notation
        if (isCheckmate) {
            notation += '#';
        } else if (isCheck) {
            notation += '+';
        }
        
        return notation;
    }
    
    function updateMoveHistoryDisplay() {
        moveHistoryList.innerHTML = '';
        
        moveHistory.forEach(move => {
            const moveElement = document.createElement('div');
            moveElement.className = 'move-entry';
            
            moveElement.innerHTML = `
                <span class="move-number">${move.number}.</span>
                <span class="move-notation">${move.white || ''}</span>
                ${move.black ? `<span class="move-notation">${move.black}</span>` : ''}
            `;
            
            moveHistoryList.appendChild(moveElement);
        });
        
        // Scroll to bottom
        moveHistoryList.scrollTop = moveHistoryList.scrollHeight;
    }
    
    function clearMoveHistory() {
        moveHistory = [];
        moveCounter = 1;
        updateMoveHistoryDisplay();
    }
    
    // Unicode chess pieces
    const chessPieces = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
    };
    
    // Initialize the board
    function initializeBoard() {
        chessboard.innerHTML = '';
        
        // Reset all state
        selectedSquare = null;
        draggedPiece = null;
        draggedPieceSquare = null;
        isDragging = false;
        
        // Create 64 squares
        for (let rank = 7; rank >= 0; rank--) {
            for (let file = 0; file < 8; file++) {
                const square = document.createElement('div');
                square.className = `square ${(rank + file) % 2 === 0 ? 'light' : 'dark'}`;
                
                // Data attributes for position
                const squareName = String.fromCharCode(97 + file) + (rank + 1);
                square.dataset.square = squareName;
                
                // Click handler for move selection
                square.addEventListener('click', (e) => {
                    // Only handle click if not in the middle of a drag operation
                    if (!isDragging) {
                        handleSquareClick(squareName);
                    }
                    e.stopPropagation(); // Prevent event bubbling
                });
                
                // Drag and drop event listeners
                square.addEventListener('dragover', (e) => {
                    e.preventDefault(); // Allow drop
                    square.classList.add('drag-over');
                });
                
                square.addEventListener('dragleave', () => {
                    square.classList.remove('drag-over');
                });
                
                square.addEventListener('drop', (e) => {
                    e.preventDefault();
                    square.classList.remove('drag-over');
                    if (draggedPiece && draggedPieceSquare) {
                        handleDrop(squareName);
                    }
                });
                
                chessboard.appendChild(square);
            }
        }
        
        // Add a click handler to the whole board to deselect when clicking outside
        document.addEventListener('click', (e) => {
            // If clicking outside a square and not dragging, deselect
            if (!e.target.closest('.square') && !isDragging && selectedSquare) {
                clearHighlights();
            }
        });
        
        // Fetch initial board state
        fetchBoardState();
    }
    
    // Fetch the current board state from the server
    function fetchBoardState() {
        // Clear any existing highlights first
        clearHighlights();
        
        fetch('/api/board')
            .then(response => response.json())
            .then(data => {
                boardState = data;
                updateBoard();
                updateGameStatus();
                
                // If checkmate is detected, immediately disable the board
                if (boardState.isGameOver) {
                    disableBoardInteraction();
                }
            })
            .catch(error => console.error('Error fetching board state:', error));
    }
    
    // Update the board display based on current state
    function updateBoard() {
        // Clear previous highlights
        document.querySelectorAll('.square').forEach(square => {
            square.classList.remove('selected', 'valid-move', 'valid-capture', 'in-check', 'drag-over', 'last-move-from', 'last-move-to', 'kings-step-destination');
            square.innerHTML = '';
        });
        
        // Parse FEN string to place pieces
        const fen = boardState.fen.split(' ')[0];
        const rows = fen.split('/');
        
        // Highlight last move if present
        if (boardState.lastMove) {
            const fromSquare = document.querySelector(`.square[data-square="${boardState.lastMove.from}"]`);
            const toSquare = document.querySelector(`.square[data-square="${boardState.lastMove.to}"]`);
            
            if (fromSquare) fromSquare.classList.add('last-move-from');
            if (toSquare) toSquare.classList.add('last-move-to');
            
            // If it was a King's Step move, add special class
            if (boardState.lastMove.isKingsStep && toSquare) {
                toSquare.classList.add('kings-step-destination');
            }
        }
        
        // Highlight king in check
        if (boardState.inCheck) {
            const checkSquare = document.querySelector(`.square[data-square="${boardState.inCheck}"]`);
            if (checkSquare) {
                checkSquare.classList.add('in-check');
            }
        }
        
        rows.forEach((row, rank) => {
            let file = 0;
            
            for (let i = 0; i < row.length; i++) {
                const char = row[i];
                
                if (!isNaN(char)) {
                    file += parseInt(char);
                } else {
                    const squareName = String.fromCharCode(97 + file) + (8 - rank);
                    const squareElement = document.querySelector(`.square[data-square="${squareName}"]`);
                    
                    if (squareElement) {
                        const pieceElement = document.createElement('div');
                        pieceElement.className = 'piece';
                        pieceElement.textContent = chessPieces[char];
                        pieceElement.dataset.piece = char;
                        
                        // Add color class
                        if (char === char.toUpperCase()) {
                            pieceElement.classList.add('white');
                        } else {
                            pieceElement.classList.add('black');
                        }
                        
                        // Add drag and drop event listeners to pieces
                        pieceElement.draggable = true;
                        
                        pieceElement.addEventListener('mousedown', (e) => {
                            // Prevent drag conflicts with click handling
                            e.stopPropagation();
                        });
                        
                        pieceElement.addEventListener('dragstart', (e) => {
                            // Only allow dragging if it's the correct player's turn
                            const isPieceWhite = pieceElement.classList.contains('white');
                            const isWhiteTurn = boardState.turn === 'white';
                            
                            if ((isPieceWhite && isWhiteTurn) || (!isPieceWhite && !isWhiteTurn)) {
                                isDragging = true;
                                draggedPiece = pieceElement;
                                draggedPieceSquare = squareName;
                                
                                // Set drag image (transparent)
                                const dragImage = document.createElement('div');
                                dragImage.textContent = pieceElement.textContent;
                                dragImage.style.opacity = '0.01';
                                document.body.appendChild(dragImage);
                                e.dataTransfer.setDragImage(dragImage, 0, 0);
                                setTimeout(() => document.body.removeChild(dragImage), 0);
                                
                                setTimeout(() => {
                                    pieceElement.classList.add('dragging');
                                }, 0);
                                
                                // Also select the piece to show valid moves
                                if (selectedSquare !== squareName) {
                                    clearHighlights();
                                    selectedSquare = squareName;
                                    highlightValidMoves(squareName);
                                }
                            } else {
                                e.preventDefault(); // Prevent dragging if it's not this player's turn
                            }
                        });
                        
                        pieceElement.addEventListener('dragend', () => {
                            isDragging = false;
                            if (draggedPiece) {
                                draggedPiece.classList.remove('dragging');
                                draggedPiece = null;
                            }
                        });
                        
                        // Add click handler for piece selection (compatible with drag-and-drop)
                        pieceElement.addEventListener('click', (e) => {
                            // Avoid triggering when ending a drag operation
                            if (!isDragging) {
                                handleSquareClick(squareName);
                            }
                            e.stopPropagation(); // Prevent event from bubbling to square
                        });
                        
                        squareElement.appendChild(pieceElement);
                    }
                    
                    file++;
                }
            }
        });
        
        // If game is over or in checkmate, don't show any valid moves
        if (boardState.isGameOver || boardState.isCheckmate) {
            selectedSquare = null;
            return;
        }
        
        // Restore selection if any
        if (selectedSquare) {
            const squareElement = document.querySelector(`.square[data-square="${selectedSquare}"]`);
            if (squareElement) {
                squareElement.classList.add('selected');
                highlightValidMoves(selectedSquare);
            }
        }
    }
    
    // Handle drop event
    function handleDrop(targetSquare) {
        // Ignore if same square (dropped on original position)
        if (targetSquare === draggedPieceSquare) {
            return;
        }
        
        // Check if the drop is on a valid move square
        const isValidMove = boardState.moveInfo[draggedPieceSquare]?.moves.includes(targetSquare);
        const isValidCapture = boardState.moveInfo[draggedPieceSquare]?.captures.includes(targetSquare);
        
        if (isValidMove || isValidCapture) {
            const move = `${draggedPieceSquare}${targetSquare}`;
            makeMove(move);
        }
        
        // Reset drag state
        draggedPieceSquare = null;
        clearHighlights();
    }
    
    // Update game status display
    function updateGameStatus() {
        turnDisplay.textContent = boardState.turn.charAt(0).toUpperCase() + boardState.turn.slice(1);

        if (boardState.isGameOver || boardState.isCheckmate) {
            let message = '';
            let gameOverTitle = '';
            const winner = boardState.turn === 'white' ? 'Black' : 'White';
            
            // Set message based on the game over reason
            if (boardState.gameOverReason === "checkmate" || boardState.isCheckmate) {
                gameOverTitle = `${winner} Wins!`;
                message = `CHECKMATE! ${winner} wins! Press 'Reset Game' to play again.`;
            } else if (boardState.gameOverReason === "stalemate") {
                gameOverTitle = 'Draw - Stalemate';
                message = 'STALEMATE! Game is a draw. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "repetition") {
                gameOverTitle = 'Draw - Repetition';
                message = 'DRAW BY REPETITION! Same position occurred three times. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "fifty_moves") {
                gameOverTitle = 'Draw - Fifty Moves';
                message = 'DRAW BY FIFTY-MOVE RULE! No captures or pawn moves in the last 50 moves. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "insufficient_material") {
                gameOverTitle = 'Draw - Insufficient Material';
                message = 'DRAW! Insufficient material to checkmate. Press \'Reset Game\' to play again.';
            } else {
                gameOverTitle = 'Game Over';
                message = 'GAME OVER! Press \'Reset Game\' to play again.';
            }
            
            checkStatus.textContent = message;
            disableBoardInteraction(gameOverTitle);
            
            // Highlight the reset button to draw attention to it
            document.getElementById('reset-button').classList.add('highlight-reset');
        } else if (boardState.isCheck) {
            checkStatus.textContent = `${boardState.turn.toUpperCase()} IS IN CHECK!`;
        } else {
            checkStatus.textContent = '';
            document.getElementById('reset-button').classList.remove('highlight-reset');
        }
    }
    
    // Disable board interaction when game is over
    function disableBoardInteraction(gameOverTitle = 'Game Over') {
        selectedSquare = null;
        draggedPiece = null;
        draggedPieceSquare = null;
        isDragging = false;
        
        // Create an overlay to visually indicate the game is over
        let overlay = document.querySelector('.game-over-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'game-over-overlay';
            document.body.appendChild(overlay);
            
            // Add click to close functionality
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    closeGameOverOverlay();
                }
            });
        }
        
        // Determine subtitle based on game state
        let subtitle = 'Click anywhere to continue playing or reset the game.';
        if (boardState.gameOverReason === 'checkmate') {
            subtitle = 'The king has been checkmated! Game completed.';
        } else if (boardState.gameOverReason === 'stalemate') {
            subtitle = 'No legal moves available. The game ends in a draw.';
        } else if (boardState.gameOverReason === 'repetition') {
            subtitle = 'The same position occurred three times.';
        } else if (boardState.gameOverReason === 'fifty_moves') {
            subtitle = 'No captures or pawn moves in the last 50 moves.';
        } else if (boardState.gameOverReason === 'insufficient_material') {
            subtitle = 'Neither player has enough pieces to checkmate.';
        }
        
        overlay.innerHTML = '<div class="game-over-content">' +
            '<div class="close-hint">Click outside to close</div>' +
            '<div class="game-over-message">' + gameOverTitle + '</div>' +
            '<div class="game-over-subtitle">' + subtitle + '</div>' +
            '<div class="game-over-actions">' +
            '<button class="game-over-btn" onclick="closeGameOverOverlay()">Continue Viewing</button>' +
            '<button class="game-over-btn reset" onclick="resetGame()">New Game</button>' +
            '</div>' +
            '</div>';
        overlay.style.display = 'flex';
        
        // Disable all square click events and dragging
        document.querySelectorAll('.square').forEach(square => {
            square.style.cursor = 'default';
            const clone = square.cloneNode(true);
            square.parentNode.replaceChild(clone, square);
        });
        
        // Disable dragging on all pieces
        document.querySelectorAll('.piece').forEach(piece => {
            piece.draggable = false;
        });
    }
    
    // Close game over overlay
    function closeGameOverOverlay() {
        const overlay = document.querySelector('.game-over-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
        // Note: Don't reset the game state, just hide the overlay
        // Users can still see the final position and move history
    }
    
    // Make functions available globally for onclick handlers
    window.closeGameOverOverlay = closeGameOverOverlay;
    window.resetGame = resetGame;
    
    // Highlight valid moves for the selected square
    function highlightValidMoves(square) {
        // First, highlight the selected square
        const selectedElement = document.querySelector(`.square[data-square="${square}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }
        
        // Get move info for this square
        const moveInfo = boardState.moveInfo[square];
        if (!moveInfo) return;
        
        // Get piece information to determine if King's Step is applicable
        const pieceElement = selectedElement?.querySelector('.piece');
        const piece = pieceElement?.dataset.piece;
        const isWhite = piece && piece === piece.toUpperCase();
        const pieceType = piece ? piece.toLowerCase() : null;
        
        // Determine if this piece can make King's Step moves (not king, not queen)
        const canMakeKingsStep = pieceType && !['k', 'q'].includes(pieceType);
        
        // Helper function to check if a move is likely a King's Step
        function isLikelyKingsStep(from, to) {
            // Only non-kings, non-queens can make King's Step
            if (!canMakeKingsStep) return false;
            
            // Get algebraic coordinates
            const fromFile = from.charCodeAt(0) - 97; // 'a' -> 0
            const fromRank = parseInt(from[1]) - 1;   // '1' -> 0
            const toFile = to.charCodeAt(0) - 97;
            const toRank = parseInt(to[1]) - 1;
            
            // Calculate distance
            const fileDiff = Math.abs(fromFile - toFile);
            const rankDiff = Math.abs(fromRank - toRank);
            
            // For pawns, forward one square is normal move
            if (pieceType === 'p') {
                // White pawn moving up or black pawn moving down
                const normalDirection = isWhite ? (toRank - fromRank === 1) : (fromRank - toRank === 1);
                const sameFile = fromFile === toFile;
                
                // Normal pawn move
                if (normalDirection && sameFile) return false;
                
                // Initial two-square move
                if (isWhite && fromRank === 1 && toRank === 3 && sameFile) return false;
                if (!isWhite && fromRank === 6 && toRank === 4 && sameFile) return false;
            }
            
            // For knights, L-shape is normal move
            if (pieceType === 'n') {
                if ((fileDiff === 1 && rankDiff === 2) || (fileDiff === 2 && rankDiff === 1)) {
                    return false;
                }
            }
            
            // For bishops, diagonal is normal move
            if (pieceType === 'b') {
                if (fileDiff === rankDiff) return false;
            }
            
            // For rooks, straight line is normal move
            if (pieceType === 'r') {
                if (fileDiff === 0 || rankDiff === 0) return false;
            }
            
            // King's Step is one square in any direction
            return fileDiff <= 1 && rankDiff <= 1;
        }
        
        // Highlight valid moves (non-captures)
        moveInfo.moves.forEach(targetSquare => {
            const squareElement = document.querySelector(`.square[data-square="${targetSquare}"]`);
            if (squareElement) {
                if (isLikelyKingsStep(square, targetSquare)) {
                    squareElement.classList.add('valid-kings-step');
                } else {
                    squareElement.classList.add('valid-move');
                }
            }
        });
        
        // Highlight valid captures
        moveInfo.captures.forEach(targetSquare => {
            const squareElement = document.querySelector(`.square[data-square="${targetSquare}"]`);
            if (squareElement) {
                squareElement.classList.add('valid-capture');
            }
        });
    }
    
    // Handle square click
    function handleSquareClick(squareName) {
        // Check if the game is over or in checkmate
        if (boardState.isGameOver || boardState.isCheckmate) {
            // Highlight the reset button and show a message prompting restart
            document.getElementById('reset-button').classList.add('highlight-reset');
            // Add a pulsing animation to the reset button
            if (!document.getElementById('reset-message')) {
                const message = document.createElement('div');
                message.id = 'reset-message';
                message.textContent = 'Game is over. Click Reset to play again.';
                message.style.color = '#e74c3c';
                message.style.fontWeight = 'bold';
                message.style.margin = '10px 0';
                document.querySelector('.controls').appendChild(message);
            }
            return; // Exit the function
        }

        const squareElement = document.querySelector(`.square[data-square="${squareName}"]`);

        // If no square is currently selected
        if (!selectedSquare) {
            // Check if the square has a piece of the current player's color
            const piece = squareElement.querySelector('.piece');
            if (!piece) return;

            const isPieceWhite = piece.classList.contains('white');
            const isWhiteTurn = boardState.turn === 'white';

            if ((isPieceWhite && isWhiteTurn) || (!isPieceWhite && !isWhiteTurn)) {
                selectedSquare = squareName;
                squareElement.classList.add('selected');
                highlightValidMoves(squareName);
            }
        } 
        // If a square is already selected
        else {
            // If clicking the same square, deselect it
            if (squareName === selectedSquare) {
                selectedSquare = null;
                squareElement.classList.remove('selected');
                clearHighlights();
                return;
            }
            
            const isValidMove = boardState.moveInfo[selectedSquare]?.moves.includes(squareName);
            const isValidCapture = boardState.moveInfo[selectedSquare]?.captures.includes(squareName);

            if (isValidMove || isValidCapture) {
                const move = `${selectedSquare}${squareName}`;
                makeMove(move);
            } else {
                // Check if the new square has a piece of the current player's color
                const piece = squareElement.querySelector('.piece');
                if (piece) {
                    const isPieceWhite = piece.classList.contains('white');
                    const isWhiteTurn = boardState.turn === 'white';

                    if ((isPieceWhite && isWhiteTurn) || (!isPieceWhite && !isWhiteTurn)) {
                        // Change selection to the new piece
                        clearHighlights();
                        selectedSquare = squareName;
                        squareElement.classList.add('selected');
                        highlightValidMoves(squareName);
                    }
                } else {
                    // Clicked on an empty square that's not a valid move
                    selectedSquare = null;
                    clearHighlights();
                }
            }
        }
    }
    
    // Clear all highlights
    function clearHighlights() {
        document.querySelectorAll('.square').forEach(square => {
            square.classList.remove('selected', 'valid-move', 'valid-capture', 'drag-over', 'last-move-from', 'last-move-to', 'valid-kings-step', 'kings-step-destination');
            
            // Reset any piece styling
            const piece = square.querySelector('.piece');
            if (piece) {
                piece.style.transform = '';
                piece.style.transition = '';
            }
        });
        
        // Set a flag to indicate no square is selected
        selectedSquare = null;
    }
    
    // Make a move
    function makeMove(move) {
        // Clear any existing highlights
        clearHighlights();
        
        // Store previous board state to track move details
        const previousBoardState = JSON.parse(JSON.stringify(boardState));
        
        fetch('/api/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ move: move })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => Promise.reject(data));
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Get move details for history
                const from = move.substring(0, 2);
                const to = move.substring(2, 4);
                const movedPiece = getPieceAt(from, previousBoardState.fen);
                const isCapture = data.lastMove && data.lastMove.isCapture;
                const isCheck = data.isCheck;
                const isCheckmate = data.isCheckmate || data.isGameOver;
                const isKingsStep = data.lastMove && data.lastMove.isKingsStep;
                
                // Add move to history
                addMoveToHistory(
                    { from: from, to: to },
                    movedPiece,
                    isCapture,
                    isCheck,
                    isCheckmate,
                    isKingsStep
                );
                
                // Update board state with new data
                boardState = data;
                updateBoard();
                updateGameStatus();
                
                // Deselect the current square
                selectedSquare = null;
                
                // If game is over after this move, disable board
                if (data.isGameOver) {
                    const winner = previousBoardState.turn === 'white' ? 'White' : 'Black';
                    const gameOverTitle = data.gameOverReason === 'checkmate' ? `${winner} Wins!` : 'Game Over';
                    disableBoardInteraction(gameOverTitle);
                }
            }
        })
        .catch(error => {
            console.error('Error making move:', error);
            
            // If this was an invalid move due to game over, update UI
            if (error.isGameOver) {
                boardState.isGameOver = error.isGameOver;
                boardState.isCheckmate = error.isCheckmate;
                updateGameStatus();
                disableBoardInteraction();
            }
        });
    }
    
    // Helper function to get piece at square from FEN
    function getPieceAt(square, fen) {
        const fenBoard = fen.split(' ')[0];
        const ranks = fenBoard.split('/');
        
        const file = square.charCodeAt(0) - 97; // a=0, b=1, etc.
        const rank = parseInt(square[1]) - 1;   // 1=0, 2=1, etc.
        
        const boardRank = ranks[7 - rank]; // FEN ranks are from 8 to 1
        let currentFile = 0;
        
        for (let i = 0; i < boardRank.length; i++) {
            const char = boardRank[i];
            if (isNaN(char)) {
                if (currentFile === file) {
                    return char;
                }
                currentFile++;
            } else {
                currentFile += parseInt(char);
                if (currentFile > file) {
                    return null; // Empty square
                }
            }
        }
        return null;
    }
    
    // Reset game
    function resetGame() {
        // Clear any selected squares and highlights
        clearHighlights();
        
        // Clear move history
        clearMoveHistory();
        
        // Remove game over overlay if it exists
        const overlay = document.querySelector('.game-over-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        // Remove any reset messages
        const resetMessage = document.getElementById('reset-message');
        if (resetMessage) {
            resetMessage.remove();
        }
        
        // Reset game state
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Refresh the board with new state
                fetchBoardState();
            } else {
                console.error('Failed to reset game:', data.error);
            }
        })
        .catch(error => console.error('Error resetting game:', error));
    }
    
    // Event listeners
    resetButton.addEventListener('click', resetGame);
    
    // Add window resize event listener to clear any lingering highlights
    window.addEventListener('resize', () => {
        // Clear highlights on resize to avoid UI issues
        clearHighlights();
        // Redraw the board with current state
        updateBoard();
    });
    
    // Initialize the board when the page loads
    initializeBoard();
});