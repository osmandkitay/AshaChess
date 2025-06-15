from flask import Flask, render_template, request, jsonify
import chess

app = Flask(__name__)

# Custom 2HS Chess Board: With Knights + Fixed Game Termination Detection
class TwoHSChessBoard:
    # Starting FEN with knights (standard chess starting position)
    VARIANT_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, fen=VARIANT_STARTING_FEN):
        self.board = chess.Board(fen)
        # "King's Step" directions
        self.kings_step_directions = [
            (0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)
        ]
        # Store position history for repetition detection
        self.position_history = []
        self.update_position_history()
        
        # Cache for legal moves to avoid recalculation
        self._legal_moves_cache = None
        self._last_fen = None
        
        # Last move made for better UI highlighting
        self.last_move = None
        
        # Game termination reason
        self.termination_reason = None
        
        # Extended FEN information - additional flags for 2HS rules
        # Currently no additional flags needed, but prepared for extensions
        self.extended_fen_flags = {}
    
    def get_extended_fen(self):
        """Get the extended FEN that includes 2HS Chess specific flags."""
        base_fen = self.board.fen()
        # If we have any custom flags to add, we can append them here
        # For future extensions like super_pawns, variable castling, etc.
        return base_fen

    def update_position_history(self):
        # Add current position to history for repetition detection
        position_key = self.board.fen().split(' ')[0]  # Just the piece positions
        self.position_history.append(position_key)
        
        # Prevent memory leak by limiting history size
        # Keep only last 100 positions (sufficient for repetition detection)
        # Threefold repetition needs only 3 occurrences, so 100 positions is more than enough
        if len(self.position_history) > 100:
            self.position_history = self.position_history[-100:]
    
    def _clear_cache(self):
        """Clear the legal moves cache to prevent stale data."""
        self._legal_moves_cache = None
        self._last_fen = None
    
    def reset_position_history(self):
        """Reset position history for a new game to prevent memory accumulation."""
        self.position_history = []
        self.update_position_history()
        
    def legal_moves(self):
        """
        Generates all legal moves for the current position, including standard chess
        moves and custom "King's Step" moves. This is the single source of truth for move legality.
        A move is legal if, and only if, it does not leave the player's king in check.
        """
        current_fen = self.board.fen()
        if self._legal_moves_cache is not None and self._last_fen == current_fen:
            return self._legal_moves_cache

        legal_moves = []
        
        # 1. Generate standard pseudo-legal moves from python-chess
        candidate_moves = list(self.board.pseudo_legal_moves)
        
        # 2. Generate "King's Step" pseudo-legal moves
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            # Any piece except King or Queen can perform a King's Step
            if piece and piece.color == self.board.turn and piece.piece_type not in [chess.KING, chess.QUEEN]:
                for dx, dy in self.kings_step_directions:
                    file, rank = chess.square_file(square), chess.square_rank(square)
                    new_file, new_rank = file + dx, rank + dy
                    if 0 <= new_file < 8 and 0 <= new_rank < 8:
                        to_sq = chess.square(new_file, new_rank)
                        # The destination square must be empty
                        if self.board.piece_at(to_sq) is None:
                            candidate_moves.append(chess.Move(square, to_sq))
                            
        # 3. Validate all candidate moves by simulation
        for move in set(candidate_moves): # Use set to handle duplicates
            try:
                # Create a temporary board to simulate the move
                temp_board = self.board.copy()
                temp_board.push(move)
                
                # A move is legal if the player's own king is NOT in check after the move.
                # This single check correctly handles all check/pin-related rules.
                king_square = temp_board.king(self.board.turn)
                if not temp_board.is_attacked_by(not self.board.turn, king_square):
                    legal_moves.append(move)
            except Exception:
                # Ignore fundamentally illegal moves that python-chess might raise errors on.
                continue

        self._legal_moves_cache = legal_moves
        self._last_fen = current_fen
        return legal_moves

    def get_move_info(self):
        """Get information about valid moves for UI display."""
        moves_info = {}
        
        # If in checkmate, return empty moves
        if self.is_checkmate():
            return {}
        
        # Get all legal moves including King's Step
        legal_moves = self.legal_moves()
        
        # Group moves by origin square
        for move in legal_moves:
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            entry = moves_info.setdefault(from_sq, {"moves": [], "captures": []})
            
            # Categorize as capture or regular move
            if self.board.is_capture(move):
                entry["captures"].append(to_sq)
            else:
                entry["moves"].append(to_sq)
                
        return moves_info

    def is_move_valid(self, move_uci: str):
        """
        Checks if a move is valid by referencing the main legal_moves engine.
        This ensures all rules are applied consistently from a single source of truth.
        """
        if self.is_game_over():
            return False
            
        try:
            move = chess.Move.from_uci(move_uci)
            # A move is legal if and only if it exists in our main function's generated list.
            return move in self.legal_moves()
        except (ValueError, IndexError):
            # Handle invalid UCI format or board errors.
            return False

    def make_move(self, move):
        """Make a move on the board if it's valid."""
        # First check if game is already over
        if self.is_game_over():
            return False
            
        # Verify the move is legal
        if self.is_move_valid(move):
            # Parse the move
            chess_move = chess.Move.from_uci(move)
            
            # Save as last move for UI highlighting
            self.last_move = chess_move
            
            # Execute the move
            self.board.push(chess_move)
            
            # Clear the legal moves cache since the position changed
            self._clear_cache()
            
            # Update position history for repetition detection
            self.update_position_history()
            
            # Check if this move ended the game
            if self.is_game_over():
                if self.is_checkmate():
                    self.termination_reason = "checkmate"
                elif self.is_stalemate():
                    self.termination_reason = "stalemate"
                elif self.is_insufficient_material():
                    self.termination_reason = "insufficient_material"
                elif self.is_threefold_repetition():
                    self.termination_reason = "threefold_repetition"
                elif self.is_fifty_moves():
                    self.termination_reason = "fifty_moves"
            
            return True
        return False

    def fen(self):
        """Get the FEN of the current position."""
        return self.board.fen()

    def turn(self):
        """Get the side to move."""
        return self.board.turn

    def is_check(self):
        """Check if the current side to move is in check."""
        return self.board.is_check()

    def is_checkmate(self):
        """Check if the current position is checkmate."""
        # A position is checkmate when the king is in check and there are no legal moves
        # Use all legal moves (including King's Step) for consistent detection
        return self.board.is_check() and len(self.legal_moves()) == 0

    def is_stalemate(self):
        """Check if the current position is stalemate."""
        # A position is stalemate when the king is not in check and there are no legal moves
        # Use all legal moves (including King's Step) for consistent detection
        return not self.board.is_check() and len(self.legal_moves()) == 0

    def is_insufficient_material(self):
        """Check if there's insufficient material to checkmate."""
        # Use python-chess's built-in insufficient material detection
        # which correctly handles standard chess rules
        return self.board.is_insufficient_material()

    def is_threefold_repetition(self):
        """Check if the current position has occurred three times."""
        current_position = self.board.fen().split(' ')[0]
        return self.position_history.count(current_position) >= 3

    def is_fifty_moves(self):
        """Check if the fifty-move rule applies."""
        # Check if the fifty-move rule applies (no captures or pawn moves in the last 50 moves)
        return self.board.halfmove_clock >= 100  # 50 full moves = 100 half-moves

    def is_game_over(self):
        """Check if the game has ended."""
        # 1. First check for checkmate (highest priority)
        if self.is_checkmate():
            return True
            
        # 2. Check for stalemate
        if self.is_stalemate():
            return True
            
        # 3. Check for draws
        if (self.is_insufficient_material() or
            self.is_threefold_repetition() or
            self.is_fifty_moves()):
            return True
            
        return False

    def king(self, color):
        """Get the square of the king of the given color."""
        return self.board.king(color)

    def is_kings_step_move(self, move):
        """Determine if a move is a King's Step move."""
        # Convert string move to Move object if necessary
        if isinstance(move, str):
            try:
                move = chess.Move.from_uci(move)
            except ValueError:
                return False
        
        # If the move is in standard legal moves, it's not a King's Step
        if move in self.board.legal_moves:
            return False
            
        piece = self.board.piece_at(move.from_square)
        if piece is None or piece.piece_type in [chess.KING, chess.QUEEN]:
            return False
            
        # Calculate Manhattan distance
        from_file = chess.square_file(move.from_square)
        from_rank = chess.square_rank(move.from_square)
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        
        # King's Step is one square in any direction
        file_diff = abs(from_file - to_file)
        rank_diff = abs(from_rank - to_rank)
        
        # Basic King's Step check
        is_kings_step = file_diff <= 1 and rank_diff <= 1 and not (file_diff == 0 and rank_diff == 0)
        
        # For pawns, normal forward moves and captures aren't King's Step
        if piece.piece_type == chess.PAWN:
            direction = 1 if piece.color == chess.WHITE else -1
            
            # Normal forward move
            if file_diff == 0 and (to_rank - from_rank) == direction:
                return False
                
            # Initial two-square move
            if file_diff == 0 and from_rank in [1, 6] and abs(to_rank - from_rank) == 2:
                return False
                
            # Normal capture
            if file_diff == 1 and (to_rank - from_rank) == direction:
                return False
        
        # For knights, L-shape moves aren't King's Step
        if piece.piece_type == chess.KNIGHT:
            if (file_diff == 1 and rank_diff == 2) or (file_diff == 2 and rank_diff == 1):
                return False
        
        # For bishops, diagonal moves aren't King's Step
        if piece.piece_type == chess.BISHOP:
            if file_diff == rank_diff:
                return False
        
        # For rooks, horizontal and vertical moves aren't King's Step
        if piece.piece_type == chess.ROOK:
            if file_diff == 0 or rank_diff == 0:
                return False
        
        # If it passed all the above checks and is within 1 square, it's a King's Step
        return is_kings_step


        
    def get_pin_direction_and_attacker(self, square):
        """Get the direction of the pin and the attacker's square for a pinned piece.
        
        Returns a tuple (file_dir, rank_dir, attacker_square) or None if not pinned.
        """
        piece = self.board.piece_at(square)
        if piece is None:
            return None
            
        color = piece.color
        king_square = self.board.king(color)
        
        # Check if pinned using our main method
        is_pinned, file_dir, rank_dir = self.is_pinned_against_king(square)
        if not is_pinned:
            return None
            
        # Look for the attacker in the direction from the piece away from the king
        piece_file = chess.square_file(square)
        piece_rank = chess.square_rank(square)
        attacker_square = None
        current_file = piece_file + file_dir
        current_rank = piece_rank + rank_dir
        
        while 0 <= current_file <= 7 and 0 <= current_rank <= 7:
            current_square = chess.square(current_file, current_rank)
            current_piece = self.board.piece_at(current_square)
            
            if current_piece is not None:
                # Check if this piece could be pinning our piece
                if current_piece.color != color:
                    # Horizontal or vertical pin
                    if (file_dir != 0 and rank_dir == 0) or (file_dir == 0 and rank_dir != 0):
                        if current_piece.piece_type in [chess.ROOK, chess.QUEEN]:
                            attacker_square = current_square
                            break
                    # Diagonal pin
                    elif file_dir != 0 and rank_dir != 0:
                        if current_piece.piece_type in [chess.BISHOP, chess.QUEEN]:
                            attacker_square = current_square
                            break
                
                # If we hit any other piece first, there's no pin from this direction
                break
                
            current_file += file_dir
            current_rank += rank_dir
            
        return (file_dir, rank_dir, attacker_square) if attacker_square is not None else None
    
    def is_move_along_pin_line(self, move):
        """Check if a move is along the pin line (connecting the king, piece, and attacker).
        
        If a piece is pinned, it can only move along the line of the pin.
        """
        from_square = move.from_square
        to_square = move.to_square
        
        # Get pin information
        pin_info = self.get_pin_direction_and_attacker(from_square)
        if pin_info is None:
            # Not pinned, any move is allowed
            return True
            
        file_dir, rank_dir, attacker_square = pin_info
        
        # Calculate positions
        king_square = self.board.king(self.board.piece_at(from_square).color)
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        to_file = chess.square_file(to_square)
        to_rank = chess.square_rank(to_square)
        
        # For a move to be along the pin line, it must:
        # 1. Be on the same rank, file, or diagonal as the king and piece
        # 2. Be between the king and the attacker or beyond the king in the opposite direction
        
        # Check if the target is on the same line as the king
        if file_dir == 0:  # Vertical pin
            if to_file != king_file:
                return False
        elif rank_dir == 0:  # Horizontal pin
            if to_rank != king_rank:
                return False
        else:  # Diagonal pin
            # Check if on the same diagonal
            if abs(to_file - king_file) != abs(to_rank - king_rank):
                return False
                
            # Check if the direction matches
            to_file_dir = 1 if king_file < to_file else -1
            to_rank_dir = 1 if king_rank < to_rank else -1
            
            if to_file_dir != file_dir or to_rank_dir != rank_dir:
                # Allow moves in the opposite direction (away from the attacker, behind the king)
                if to_file_dir != -file_dir or to_rank_dir != -rank_dir:
                    return False
        
        return True

# Global game state
game_state = {"board": TwoHSChessBoard()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/board', methods=['GET'])
def get_board():
    b = game_state["board"]
    
    # Get game state information
    is_game_over = b.is_game_over()
    checkmate = b.is_checkmate()
    stalemate = b.is_stalemate()
    threefold_repetition = b.is_threefold_repetition()
    fifty_moves = b.is_fifty_moves()
    insufficient_material = b.is_insufficient_material()
    
    # Determine the specific reason for game over
    game_over_reason = b.termination_reason
    
    # Last move information for UI highlighting
    last_move = None
    if b.last_move:
        last_move = {
            "from": chess.square_name(b.last_move.from_square),
            "to": chess.square_name(b.last_move.to_square),
            "isKingsStep": b.is_kings_step_move(b.last_move)
        }
    
    return jsonify({
        "fen": b.fen(),
        "extendedFen": b.get_extended_fen(),
        "turn": "white" if b.turn() else "black",
        "moveInfo": b.get_move_info(),
        "isCheck": b.is_check(),
        "isGameOver": is_game_over,
        "gameOverReason": game_over_reason,
        "isCheckmate": checkmate,
        "isStalemate": stalemate,
        "isThreefoldRepetition": threefold_repetition,
        "isFiftyMoves": fifty_moves,
        "isInsufficientMaterial": insufficient_material,
        "inCheck": chess.square_name(b.king(b.turn())) if b.is_check() else None,
        "lastMove": last_move
    })

@app.route('/api/move', methods=['POST'])
def make_move():
    data = request.json
    move = data.get('move')
    if not move:
        return jsonify({"error": "Move not provided"}), 400

    b = game_state["board"]
    
    # Check if game is already over
    if b.is_game_over():
        return jsonify({
            "error": "Game is already over. Please reset to start a new game.",
            "isGameOver": True,
            "gameOverReason": b.termination_reason,
            "isCheckmate": b.is_checkmate(),
            "isStalemate": b.is_stalemate(),
            "isThreefoldRepetition": b.is_threefold_repetition(),
            "isFiftyMoves": b.is_fifty_moves(),
            "isInsufficientMaterial": b.is_insufficient_material()
        }), 400

    if b.make_move(move):
        # Get updated game state information
        is_game_over = b.is_game_over()
        checkmate = b.is_checkmate()
        stalemate = b.is_stalemate()
        threefold_repetition = b.is_threefold_repetition()
        fifty_moves = b.is_fifty_moves()
        insufficient_material = b.is_insufficient_material()
        
        # Last move information for UI highlighting
        last_move = None
        if b.last_move:
            last_move = {
                "from": chess.square_name(b.last_move.from_square),
                "to": chess.square_name(b.last_move.to_square),
                "isKingsStep": b.is_kings_step_move(b.last_move)
            }
        
        return jsonify({
            "success": True,
            "fen": b.fen(),
            "extendedFen": b.get_extended_fen(),
            "turn": "white" if b.turn() else "black",
            "moveInfo": b.get_move_info(),
            "isCheck": b.is_check(),
            "isGameOver": is_game_over,
            "gameOverReason": b.termination_reason,
            "isCheckmate": checkmate,
            "isStalemate": stalemate,
            "isThreefoldRepetition": threefold_repetition,
            "isFiftyMoves": fifty_moves,
            "isInsufficientMaterial": insufficient_material,
            "inCheck": chess.square_name(b.king(b.turn())) if b.is_check() else None,
            "lastMove": last_move
        })
    else:
        return jsonify({"error": "Invalid move"}), 400

@app.route('/api/reset', methods=['POST'])
def reset_game():
    game_state["board"] = TwoHSChessBoard()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
