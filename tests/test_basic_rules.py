import unittest
import chess
import sys
import os

# Add parent directory to path to import TwoHSChessBoard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import TwoHSChessBoard

class TestBasicRules(unittest.TestCase):
    """Test basic chess rules to ensure they still work correctly."""
    
    def setUp(self):
        """Set up a fresh board for each test."""
        self.board = TwoHSChessBoard()
    
    def test_initial_position(self):
        """Test that the initial position is set up correctly."""
        # Check starting position
        self.assertEqual(self.board.fen(), TwoHSChessBoard.VARIANT_STARTING_FEN)
        # White to move
        self.assertTrue(self.board.turn())
        # Kings in correct position
        self.assertEqual(chess.square_rank(self.board.king(chess.WHITE)), 0)
        self.assertEqual(chess.square_file(self.board.king(chess.WHITE)), 4)
        self.assertEqual(chess.square_rank(self.board.king(chess.BLACK)), 7)
        self.assertEqual(chess.square_file(self.board.king(chess.BLACK)), 4)
    
    def test_standard_pawn_moves(self):
        """Test standard pawn moves still work correctly."""
        # e2-e4 should be a valid move
        e2e4 = chess.Move.from_uci("e2e4")
        self.assertTrue(self.board.is_move_valid("e2e4"))
        self.board.make_move("e2e4")
        
        # Check that e2-e4 was executed
        self.assertIsNone(self.board.board.piece_at(chess.E2))
        self.assertEqual(self.board.board.piece_at(chess.E4).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.E4).color, chess.WHITE)
        
        # Black's turn
        self.assertFalse(self.board.turn())
        
        # Test pawn capture
        # Set up a position with a pawn capture
        self.board = TwoHSChessBoard("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        
        # White pawn can capture black pawn
        self.assertTrue(self.board.is_move_valid("e4f5"))
        self.board.make_move("e4f5")
        
        # Check capture was executed
        self.assertIsNone(self.board.board.piece_at(chess.E4))
        self.assertEqual(self.board.board.piece_at(chess.F5).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.F5).color, chess.WHITE)
    
    def test_check_and_checkmate(self):
        """Test check and checkmate detection."""
        # Set up a simple check position
        self.board = TwoHSChessBoard("4k3/8/8/8/8/8/8/4Q3 b - - 0 1")  # Queen directly checks king
        
        # King should be in check
        self.assertTrue(self.board.is_check())
        
        # King can escape (has legal moves)
        self.assertFalse(self.board.is_checkmate())
        
        # Test basic game over functionality (main purpose was to test consistency)
        # The key fix was making is_checkmate() and is_stalemate() both use self.legal_moves()
        self.assertFalse(self.board.is_game_over())  # Not game over when king can escape

if __name__ == "__main__":
    unittest.main() 