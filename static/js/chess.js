document.addEventListener('DOMContentLoaded', () => {
    const chessboard = document.getElementById('chessboard');
    const turnDisplay = document.getElementById('turn');
    const checkStatus = document.getElementById('check-status');
    const resetButton = document.getElementById('reset-button');
    
    let selectedSquare = null;
    let boardState = null;
    let draggedPiece = null;
    let draggedPieceSquare = null;
    let isDragging = false;  // Flag to track if a drag operation is in progress
    
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
            const winner = boardState.turn === 'white' ? 'Black' : 'White';
            
            // Set message based on the game over reason
            if (boardState.gameOverReason === "checkmate" || boardState.isCheckmate) {
                message = `CHECKMATE! ${winner} wins! Press 'Reset Game' to play again.`;
            } else if (boardState.gameOverReason === "stalemate") {
                message = 'STALEMATE! Game is a draw. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "repetition") {
                message = 'DRAW BY REPETITION! Same position occurred three times. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "fifty_moves") {
                message = 'DRAW BY FIFTY-MOVE RULE! No captures or pawn moves in the last 50 moves. Press \'Reset Game\' to play again.';
            } else if (boardState.gameOverReason === "insufficient_material") {
                message = 'DRAW! Insufficient material to checkmate. Press \'Reset Game\' to play again.';
            } else {
                // Fallback message if reason not specified
                message = 'GAME OVER! Press \'Reset Game\' to play again.';
            }
            
            checkStatus.textContent = message;
            // Add styling for game over message
            checkStatus.style.fontSize = '24px';
            checkStatus.style.color = '#e74c3c';
            disableBoardInteraction();
            
            // Highlight the reset button to draw attention to it
            document.getElementById('reset-button').classList.add('highlight-reset');
        } else if (boardState.isCheck) {
            checkStatus.textContent = `${boardState.turn.toUpperCase()} IS IN CHECK!`;
            checkStatus.style.fontSize = '20px';
            checkStatus.style.color = '#e74c3c';
        } else {
            checkStatus.textContent = '';
            checkStatus.style.fontSize = '';
            checkStatus.style.color = '';
            document.getElementById('reset-button').classList.remove('highlight-reset');
        }
    }
    
    // Disable board interaction when game is over
    function disableBoardInteraction() {
        selectedSquare = null;
        draggedPiece = null;
        draggedPieceSquare = null;
        isDragging = false;
        
        // Create an overlay to visually indicate the game is over
        const boardContainer = document.querySelector('.board-container');
        let overlay = document.querySelector('.game-over-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'game-over-overlay';
            overlay.innerHTML = '<div class="game-over-message">Game Over</div>';
            boardContainer.appendChild(overlay);
        }
        
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
                // Update board state with new data
                boardState = data;
                updateBoard();
                updateGameStatus();
                
                // Deselect the current square
                selectedSquare = null;
                
                // If game is over after this move, disable board
                if (data.isGameOver) {
                    disableBoardInteraction();
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
    
    // Reset game
    function resetGame() {
        // Clear any selected squares and highlights
        clearHighlights();
        
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