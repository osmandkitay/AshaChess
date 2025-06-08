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
        
    def legal_moves(self):
        """Get all legal moves for the current position, including custom King's Step moves."""
        current_fen = self.board.fen()
        
        # Use cached result if available and the position hasn't changed
        if self._legal_moves_cache is not None and self._last_fen == current_fen:
            return self._legal_moves_cache
            
        # If king is in check, use only standard legal moves
        # This ensures checkmate is properly detected and only moves that resolve check are allowed
        if self.board.is_check():
            self._legal_moves_cache = list(self.board.legal_moves)
            self._last_fen = current_fen
            return self._legal_moves_cache
            
        # For non-check positions, add King's Step moves
        standard_moves = list(self.board.legal_moves)
        current_color = self.board.turn
        custom_moves = []

        # Add King's Step only for non-king, non-queen pieces of current player
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if (
                piece is None or
                piece.piece_type in [chess.KING, chess.QUEEN] or
                piece.color != current_color
            ):
                continue

            for dx, dy in self.kings_step_directions:
                file_idx = chess.square_file(square)
                rank_idx = chess.square_rank(square)
                target_file = file_idx + dx
                target_rank = rank_idx + dy

                if 0 <= target_file <= 7 and 0 <= target_rank <= 7:
                    target_square = chess.square(target_file, target_rank)
                    # King's Step cannot capture
                    if self.board.piece_at(target_square) is None:
                        move = chess.Move(square, target_square)
                        # Skip if this is already a standard legal move
                        if any(std_move.from_square == square and std_move.to_square == target_square for std_move in standard_moves):
                            continue
                            
                        # Check if this move would leave the king in check
                        # Save current position
                        backup_board = self.board.copy()
                        
                        # Try the move
                        self.board.push(move)
                        
                        # Check if the king is in check after the move
                        is_check = self.board.is_check()
                        
                        # Restore the position
                        self.board = backup_board
                        
                        # If the move doesn't leave the king in check, it's valid
                        if not is_check:
                            custom_moves.append(move)
        
        # Store the result in cache
        self._legal_moves_cache = standard_moves + custom_moves
        self._last_fen = current_fen
        return self._legal_moves_cache

    def would_be_in_check_after_move(self, move, color):
        """Check if a move would leave the king in check."""
        # For regular chess moves, we can rely on python-chess's legality check
        # But for King's Step and other custom moves, we need to verify directly
        
        # For standard legal moves, we trust python-chess to handle pins correctly
        if move in self.board.legal_moves:
            return False
            
        # For custom moves or to double-check standard moves, simulate the move
        # and check if it would leave the king in check
        self.board.push(move)
        is_check = self.board.is_check()
        self.board.pop()
        return is_check

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

    def is_pinned_against_king(self, square):
        """Check if a piece is pinned against the king, and in which direction.
        
        Returns a tuple (is_pinned, file_dir, rank_dir) where file_dir and rank_dir
        indicate the direction from the king to the pinning piece.
        """
        piece = self.board.piece_at(square)
        if piece is None:
            return False, 0, 0
            
        color = piece.color
        king_square = self.board.king(color)
        
        # Get the direction from king to piece
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        piece_file = chess.square_file(square)
        piece_rank = chess.square_rank(square)
        
        print(f"DEBUG-PIN: Checking if piece at {chess.square_name(square)} is pinned against king at {chess.square_name(king_square)}")
        print(f"DEBUG-PIN: King position: file={king_file}, rank={king_rank}")
        print(f"DEBUG-PIN: Piece position: file={piece_file}, rank={piece_rank}")
        
        # If the piece is not on the same rank, file, or diagonal as the king,
        # it cannot be pinned
        is_on_same_line = False
        file_dir = 0
        rank_dir = 0
        
        # Check if they're on the same file
        if king_file == piece_file:
            is_on_same_line = True
            rank_dir = 1 if king_rank < piece_rank else -1
            print(f"DEBUG-PIN: Piece is on same file as king, rank_dir={rank_dir}")
            
        # Check if they're on the same rank
        elif king_rank == piece_rank:
            is_on_same_line = True
            file_dir = 1 if king_file < piece_file else -1
            print(f"DEBUG-PIN: Piece is on same rank as king, file_dir={file_dir}")
            
        # Check if they're on the same diagonal
        elif abs(king_file - piece_file) == abs(king_rank - piece_rank):
            is_on_same_line = True
            file_dir = 1 if king_file < piece_file else -1
            rank_dir = 1 if king_rank < piece_rank else -1
            print(f"DEBUG-PIN: Piece is on same diagonal as king, file_dir={file_dir}, rank_dir={rank_dir}")
            
        # If not on the same line, not pinned
        if not is_on_same_line:
            print(f"DEBUG-PIN: Piece is not on same line as king, not pinned")
            return False, 0, 0
            
        # Look for a potential attacker beyond the piece
        current_file = piece_file + file_dir
        current_rank = piece_rank + rank_dir
        
        print(f"DEBUG-PIN: Looking for attacker beyond piece in direction file_dir={file_dir}, rank_dir={rank_dir}")
        
        while 0 <= current_file <= 7 and 0 <= current_rank <= 7:
            current_square = chess.square(current_file, current_rank)
            current_piece = self.board.piece_at(current_square)
            
            if current_piece is not None:
                print(f"DEBUG-PIN: Found piece {current_piece.symbol()} at {chess.square_name(current_square)}")
                
                # If we hit an opponent's piece, check if it can attack along this line
                if current_piece.color != color:
                    if file_dir != 0 and rank_dir != 0:  # Diagonal
                        if current_piece.piece_type in [chess.BISHOP, chess.QUEEN]:
                            print(f"DEBUG-PIN: Found diagonal attacker at {chess.square_name(current_square)}")
                            return True, file_dir, rank_dir
                    elif file_dir != 0 or rank_dir != 0:  # Rank or file
                        if current_piece.piece_type in [chess.ROOK, chess.QUEEN]:
                            print(f"DEBUG-PIN: Found rank/file attacker at {chess.square_name(current_square)}")
                            return True, file_dir, rank_dir
                            
                # If we hit any other piece first, the piece is not pinned
                print(f"DEBUG-PIN: Found non-attacking piece first, not pinned")
                break
                
            current_file += file_dir
            current_rank += rank_dir
            
        print(f"DEBUG-PIN: No attacker found, not pinned")
        return False, 0, 0
    
    def is_move_valid(self, move):
        """Check if a move is valid in the current position."""
        # If game is over, no moves are valid
        if self.is_game_over():
            return False
            
        try:
            m = chess.Move.from_uci(move)
        except ValueError:
            return False
            
        # First, let's check if this is a standard move
        is_standard_move = m in self.board.legal_moves
        
        # If it's a standard move, it's valid
        if is_standard_move:
            return True
            
        # If not a standard move, check if it's a valid King's Step move
        # Get the piece at the source square
        piece = self.board.piece_at(m.from_square)
        
        # If no piece or wrong color, invalid move
        if piece is None or piece.color != self.board.turn:
            return False
            
        # King's Step is not valid for king or queen (they already have full movement)
        if piece.piece_type in [chess.KING, chess.QUEEN]:
            return False
            
        # Calculate file and rank differences
        from_file = chess.square_file(m.from_square)
        from_rank = chess.square_rank(m.from_square)
        to_file = chess.square_file(m.to_square)
        to_rank = chess.square_rank(m.to_square)
        
        # Check if the move is a King's Step (one square in any direction)
        file_diff = abs(from_file - to_file)
        rank_diff = abs(from_rank - to_rank)
        is_kings_step = file_diff <= 1 and rank_diff <= 1 and not (file_diff == 0 and rank_diff == 0)
        
        # King's Step cannot capture
        if self.board.piece_at(m.to_square) is not None:
            return False
            
        # If not a King's Step, invalid move
        if not is_kings_step:
            return False
        
        print(f"DEBUG-MOVE: Checking if move {m.uci()} is valid")
        
        # Check if the piece is pinned
        is_pinned, pin_file_dir, pin_rank_dir = self.is_pinned_against_king(m.from_square)
        print(f"DEBUG-MOVE: Piece pinned: {is_pinned}, pin_file_dir: {pin_file_dir}, pin_rank_dir: {pin_rank_dir}")
        
        # If the piece is pinned, it can only move along the pin line
        if is_pinned:
            # Get king position
            color = piece.color
            king_square = self.board.king(color)
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            
            # For a pinned piece to move legally, the target square must be
            # on the same line as the king and the piece's current position
            
            # Check if the target square is on the same line as the king and the piece
            if pin_file_dir == 0:  # Vertical pin
                # Must stay on the same file
                if to_file != from_file:
                    print(f"DEBUG-MOVE: Invalid move - vertical pin but changing file")
                    return False
            elif pin_rank_dir == 0:  # Horizontal pin
                # Must stay on the same rank
                if to_rank != from_rank:
                    print(f"DEBUG-MOVE: Invalid move - horizontal pin but changing rank")
                    return False
            else:  # Diagonal pin
                # Must move diagonally with the same ratio as the pin
                file_change = to_file - from_file
                rank_change = to_rank - from_rank
                
                # Must maintain diagonal movement (equal file and rank changes)
                if abs(file_change) != abs(rank_change):
                    print(f"DEBUG-MOVE: Invalid move - diagonal pin but not moving diagonally")
                    return False
                    
                # Must maintain the same diagonal direction as the pin
                move_file_dir = 1 if file_change > 0 else -1
                move_rank_dir = 1 if rank_change > 0 else -1
                
                # The directions must match the pin direction
                if move_file_dir != pin_file_dir or move_rank_dir != pin_rank_dir:
                    print(f"DEBUG-MOVE: Invalid move - diagonal pin but wrong direction")
                    return False
                    
            print(f"DEBUG-MOVE: Valid move along pin line")
        
        print(f"DEBUG-MOVE: Move {m.uci()} is valid")
        return True

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
            self._legal_moves_cache = None
            self._last_fen = None
            
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
        # Use only standard legal moves for checkmate detection to ensure accuracy
        return self.board.is_check() and len(list(self.board.legal_moves)) == 0

    def is_stalemate(self):
        """Check if the current position is stalemate."""
        # A position is stalemate when the king is not in check and there are no legal moves
        return not self.board.is_check() and len(self.legal_moves()) == 0

    def is_insufficient_material(self):
        """Check if there's insufficient material to checkmate."""
        # Implement a more sophisticated check for insufficient material
        # that accounts for the custom "King's Step" rule
        white_pieces = [self.board.piece_at(sq) for sq in chess.SQUARES 
                       if self.board.piece_at(sq) and self.board.piece_at(sq).color == chess.WHITE]
        black_pieces = [self.board.piece_at(sq) for sq in chess.SQUARES 
                       if self.board.piece_at(sq) and self.board.piece_at(sq).color == chess.BLACK]
        
        # Kings only
        if len(white_pieces) == 1 and len(black_pieces) == 1:
            return True
        
        # King and bishop vs king
        if (len(white_pieces) == 2 and len(black_pieces) == 1 and 
            any(p.piece_type == chess.BISHOP for p in white_pieces)):
            return True
        if (len(white_pieces) == 1 and len(black_pieces) == 2 and 
            any(p.piece_type == chess.BISHOP for p in black_pieces)):
            return True
        
        # King and knight vs king
        if (len(white_pieces) == 2 and len(black_pieces) == 1 and 
            any(p.piece_type == chess.KNIGHT for p in white_pieces)):
            return True
        if (len(white_pieces) == 1 and len(black_pieces) == 2 and 
            any(p.piece_type == chess.KNIGHT for p in black_pieces)):
            return True
        
        return False

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

    def is_piece_pinned(self, square):
        """Check if a piece is pinned against the king.
        
        A piece is pinned if removing it would place the king in check.
        """
        piece = self.board.piece_at(square)
        if piece is None:
            return False
            
        color = piece.color
        king_square = self.board.king(color)
        
        # Save current board state
        board_copy = self.board.copy()
        
        # Remove the piece and see if the king is now attacked
        self.board.remove_piece_at(square)
        is_pinned = self.board.is_attacked_by(not color, king_square)
        
        # Restore the board
        self.board = board_copy
        
        return is_pinned
        
    def get_pin_direction_and_attacker(self, square):
        """Get the direction of the pin and the attacker's square for a pinned piece.
        
        Returns a tuple (file_dir, rank_dir, attacker_square) or None if not pinned.
        """
        piece = self.board.piece_at(square)
        if piece is None:
            return None
            
        color = piece.color
        king_square = self.board.king(color)
        
        # If not pinned, return None
        if not self.is_piece_pinned(square):
            return None
            
        # Calculate king's position
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        piece_file = chess.square_file(square)
        piece_rank = chess.square_rank(square)
        
        # Determine the direction from king to piece
        file_dir = 0
        rank_dir = 0
        
        # Horizontal pin
        if king_rank == piece_rank:
            file_dir = 1 if king_file < piece_file else -1
            
        # Vertical pin
        elif king_file == piece_file:
            rank_dir = 1 if king_rank < piece_rank else -1
            
        # Diagonal pin
        elif abs(king_file - piece_file) == abs(king_rank - piece_rank):
            file_dir = 1 if king_file < piece_file else -1
            rank_dir = 1 if king_rank < piece_rank else -1
        
        # Look for the attacker in the direction from the piece away from the king
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
