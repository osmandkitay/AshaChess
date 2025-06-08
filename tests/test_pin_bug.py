import unittest
import chess
import sys
import os

# Add parent directory to path to import TwoHSChessBoard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import TwoHSChessBoard

class TestPinBug(unittest.TestCase):
    """Test for bug where a pinned pawn can still move."""
    
    def test_pinned_pawn_along_diagonal(self):
        """Test that a pawn pinned along a diagonal by a queen cannot move."""
        # Set up a clearer position where a pawn is pinned along a diagonal
        # White queen at h1, black king at a8, black pawn at d5
        # This creates a pin along the a8-h1 diagonal
        fen = "k7/8/8/3p4/8/8/8/7Q b - - 0 1"
        board = TwoHSChessBoard(fen)
        
        # Verify the position
        self.assertEqual(board.board.piece_at(chess.A8).piece_type, chess.KING)
        self.assertEqual(board.board.piece_at(chess.A8).color, chess.BLACK)
        self.assertEqual(board.board.piece_at(chess.D5).piece_type, chess.PAWN)
        self.assertEqual(board.board.piece_at(chess.D5).color, chess.BLACK)
        self.assertEqual(board.board.piece_at(chess.H1).piece_type, chess.QUEEN)
        self.assertEqual(board.board.piece_at(chess.H1).color, chess.WHITE)
        
        # Verify this is truly a pin by removing the pawn and checking if the king is attacked
        board_copy = board.board.copy()
        board.board.remove_piece_at(chess.D5)
        king_attacked = board.board.is_attacked_by(chess.WHITE, chess.A8)
        board.board = board_copy
        self.assertTrue(king_attacked, "King should be attacked when pawn is removed")
        
        # The pawn should not be able to move non-diagonally (not along pin line)
        self.assertFalse(board.is_move_valid("d5d4"), "Pinned pawn should not be able to move vertically")
        
        # The pawn should not be able to move diagonally in the wrong direction
        # c4 and e4 are off the pin line
        self.assertFalse(board.is_move_valid("d5c4"), "Pinned pawn should not be able to move diagonally in wrong direction")
        self.assertFalse(board.is_move_valid("d5e4"), "Pinned pawn should not be able to move diagonally in wrong direction")
        
        # But the pawn should be able to move along the pin line in the right direction
        # c6 (moving away from the queen) and e4 (moving towards the queen) are on the pin line
        self.assertTrue(board.is_move_valid("d5c6"), "Pinned pawn should be able to move along the pin line")
        self.assertTrue(board.is_move_valid("d5e4"), "Pinned pawn should be able to move along the pin line")
        
    def test_pinned_pawn_along_file(self):
        """Test that a pawn pinned along a file by a rook cannot move."""
        # Set up a simple position where a pawn is pinned along a file
        # White rook at e1, black king at e8, black pawn at e5 pinned along the file
        fen = "4k3/8/8/4p3/8/8/8/4R3 b - - 0 1"
        board = TwoHSChessBoard(fen)
        
        # Verify the position
        self.assertEqual(board.board.piece_at(chess.E8).piece_type, chess.KING)
        self.assertEqual(board.board.piece_at(chess.E8).color, chess.BLACK)
        self.assertEqual(board.board.piece_at(chess.E5).piece_type, chess.PAWN)
        self.assertEqual(board.board.piece_at(chess.E5).color, chess.BLACK)
        self.assertEqual(board.board.piece_at(chess.E1).piece_type, chess.ROOK)
        self.assertEqual(board.board.piece_at(chess.E1).color, chess.WHITE)
        
        # Verify this is truly a pin by removing the pawn and checking if the king is attacked
        board_copy = board.board.copy()
        board.board.remove_piece_at(chess.E5)
        king_attacked = board.board.is_attacked_by(chess.WHITE, chess.E8)
        board.board = board_copy
        self.assertTrue(king_attacked, "King should be attacked when pawn is removed")
        
        # The pawn should not be able to move horizontally with King's Step (not along pin line)
        self.assertFalse(board.is_move_valid("e5d5"), "Pinned pawn should not be able to move horizontally with King's Step")
        self.assertFalse(board.is_move_valid("e5f5"), "Pinned pawn should not be able to move horizontally with King's Step")
        
        # The pawn should not be able to move diagonally with King's Step (not along pin line)
        self.assertFalse(board.is_move_valid("e5d4"), "Pinned pawn should not be able to move diagonally with King's Step")
        self.assertFalse(board.is_move_valid("e5f4"), "Pinned pawn should not be able to move diagonally with King's Step")
        
        # But the pawn should be able to move forward along the pin line
        self.assertTrue(board.is_move_valid("e5e4"), "Pinned pawn should be able to move along the pin line")
        
    def test_debug_pin_detection(self):
        """Debug test to understand pin detection in python-chess."""
        # Set up a very clear diagonal pin position
        # White Queen on a1, Black King on h8, Black Pawn on d4
        fen = "7k/8/8/8/3p4/8/8/Q7 b - - 0 1"
        
        # Create a standard python-chess board for comparison
        std_board = chess.Board(fen)
        # Create our custom board
        custom_board = TwoHSChessBoard(fen)
        
        # Verify that this is truly a pin position
        # If we remove the pawn, the king should be attacked by the queen
        std_board.remove_piece_at(chess.D4)
        king_attacked = std_board.is_attacked_by(chess.WHITE, chess.H8)
        print(f"King attacked with pawn removed: {king_attacked}")
        
        # Restore the position
        std_board.set_fen(fen)
        
        # Check if the pawn is in the standard legal moves
        pawn_move = chess.Move.from_uci("d4d3")
        print("Standard chess legal moves:", [move.uci() for move in std_board.legal_moves])
        
        # Is this move legal according to python-chess?
        is_legal = pawn_move in std_board.legal_moves
        print(f"Move {pawn_move.uci()} is legal according to python-chess: {is_legal}")
        
        # Manually verify what happens if we make this move
        std_board.push(pawn_move)
        king_in_check = std_board.is_check()
        std_board.pop()
        
        print(f"Moving pawn {pawn_move.uci()} leaves king in check: {king_in_check}")
        
        # Debug our custom move validation
        move_str = "d4d3"
        # Check direct validation
        direct_valid = custom_board.is_move_valid(move_str)
        print(f"Direct validation of {move_str}: {direct_valid}")
        
        # Test our move simulation approach
        m = chess.Move.from_uci(move_str)
        backup_board = custom_board.board.copy()
        custom_board.board.push(m)
        is_check = custom_board.board.is_check()
        custom_board.board = backup_board
        print(f"Move {move_str} would leave king in check: {is_check}")
        
        # Now check a King's Step move
        king_step_move = "d4c3"  # This would be a King's Step diagonally
        m = chess.Move.from_uci(king_step_move)
        backup_board = custom_board.board.copy()
        custom_board.board.push(m)
        is_check_kings_step = custom_board.board.is_check()
        custom_board.board = backup_board
        print(f"King's Step move {king_step_move} would leave king in check: {is_check_kings_step}")
        
        # Verify that our simulation approach is working
        self.assertEqual(is_check, king_in_check, "Our simulation should match python-chess's check detection")
        
    def test_python_chess_check_detection(self):
        """Test to verify if python-chess correctly detects checks when a pinned piece moves."""
        # Create a simple position with a clear pin
        # White rook at e1, black king at e8, black pawn at e5
        fen = "4k3/8/8/4p3/8/8/8/4R3 b - - 0 1"
        std_board = chess.Board(fen)
        
        # Verify that the king is in check if the pawn moves horizontally
        pawn_move = chess.Move.from_uci("e5d5")
        
        # Is this move legal according to python-chess?
        is_legal = pawn_move in std_board.legal_moves
        print(f"Move {pawn_move.uci()} is legal according to python-chess: {is_legal}")
        
        # If we make the move, will the king be in check?
        std_board.push(pawn_move)
        is_check = std_board.is_check()
        std_board.pop()
        print(f"After moving pawn {pawn_move.uci()}, king in check: {is_check}")
        
        # Verify that removing the pawn exposes the king to the rook
        std_board.remove_piece_at(chess.E5)
        king_attacked = std_board.is_attacked_by(chess.WHITE, chess.E8)
        print(f"King attacked with pawn removed: {king_attacked}")
        
        # Create another position with a clear diagonal pin
        # White queen at a1, black king at h8, black pawn at d4
        fen = "7k/8/8/8/3p4/8/8/Q7 b - - 0 1"
        std_board = chess.Board(fen)
        
        # Try moving the pawn vertically (should be illegal)
        pawn_move = chess.Move.from_uci("d4d3")
        is_legal = pawn_move in std_board.legal_moves
        print(f"Move {pawn_move.uci()} is legal according to python-chess: {is_legal}")
        
        # If we make the move, will the king be in check?
        std_board.push(pawn_move)
        is_check = std_board.is_check()
        std_board.pop()
        print(f"After moving pawn {pawn_move.uci()}, king in check: {is_check}")
        
        # Verify that removing the pawn exposes the king to the queen
        std_board.remove_piece_at(chess.D4)
        king_attacked = std_board.is_attacked_by(chess.WHITE, chess.H8)
        print(f"King attacked with pawn removed: {king_attacked}")
        
        # The issue might be that python-chess's check detection doesn't recognize
        # that after a piece moves, it no longer blocks a check. Let's test this theory
        # by calling is_attacked_by directly
        
        # For the vertical pin
        fen = "4k3/8/8/4p3/8/8/8/4R3 b - - 0 1"
        std_board = chess.Board(fen)
        
        # Simulate the pawn moved to d5
        std_board.remove_piece_at(chess.E5)
        std_board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))
        
        # Is the king attacked now?
        king_attacked = std_board.is_attacked_by(chess.WHITE, chess.E8)
        print(f"King attacked after pawn moved horizontally: {king_attacked}")
        
        # For the diagonal pin
        fen = "7k/8/8/8/3p4/8/8/Q7 b - - 0 1"
        std_board = chess.Board(fen)
        
        # Simulate the pawn moved to d3
        std_board.remove_piece_at(chess.D4)
        std_board.set_piece_at(chess.D3, chess.Piece(chess.PAWN, chess.BLACK))
        
        # Is the king attacked now?
        king_attacked = std_board.is_attacked_by(chess.WHITE, chess.H8)
        print(f"King attacked after pawn moved vertically: {king_attacked}")
        
        # This test should help us understand if python-chess's check detection
        # is working as expected for pinned pieces
        
if __name__ == "__main__":
    unittest.main() 