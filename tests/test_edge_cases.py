import unittest
import chess
import sys
import os

# Add parent directory to path to import TwoHSChessBoard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import TwoHSChessBoard

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and special situations in 2HS Chess."""
    
    def setUp(self):
        """Set up a fresh board for each test."""
        self.board = TwoHSChessBoard()
    
    def test_castling(self):
        """Test that castling still works correctly."""
        # Set up a position where castling is possible
        self.board = TwoHSChessBoard("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        
        # White can castle kingside
        self.assertTrue(self.board.is_move_valid("e1g1"))
        self.board.make_move("e1g1")
        
        # Check castling result
        self.assertIsNone(self.board.board.piece_at(chess.E1))
        self.assertIsNone(self.board.board.piece_at(chess.H1))
        self.assertEqual(self.board.board.piece_at(chess.G1).piece_type, chess.KING)
        self.assertEqual(self.board.board.piece_at(chess.F1).piece_type, chess.ROOK)
        
        # Black can castle queenside
        self.assertTrue(self.board.is_move_valid("e8c8"))
        self.board.make_move("e8c8")
        
        # Check castling result
        self.assertIsNone(self.board.board.piece_at(chess.E8))
        self.assertIsNone(self.board.board.piece_at(chess.A8))
        self.assertEqual(self.board.board.piece_at(chess.C8).piece_type, chess.KING)
        self.assertEqual(self.board.board.piece_at(chess.D8).piece_type, chess.ROOK)
    
    def test_en_passant(self):
        """Test that en passant capture works correctly."""
        # Set up a position for en passant
        self.board = TwoHSChessBoard("rnbqkbnr/pppp1ppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1")
        
        # Black moves pawn two squares forward
        self.board.make_move("e7e5")
        
        # White can capture en passant
        self.assertTrue(self.board.is_move_valid("d4e5"))
        self.board.make_move("d4e5")
        
        # Check en passant result
        self.assertIsNone(self.board.board.piece_at(chess.D4))
        self.assertIsNone(self.board.board.piece_at(chess.E5))
        self.assertEqual(self.board.board.piece_at(chess.E5).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.E5).color, chess.WHITE)
    
    def test_promotion(self):
        """Test that pawn promotion works correctly."""
        # Set up a position for promotion
        self.board = TwoHSChessBoard("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        
        # Move white pawn to promotion square
        self.board = TwoHSChessBoard("rnbqkbnr/ppppppPp/8/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 0 1")
        
        # Promote to queen
        self.assertTrue(self.board.is_move_valid("g7g8q"))
        self.board.make_move("g7g8q")
        
        # Check promotion result
        self.assertIsNone(self.board.board.piece_at(chess.G7))
        self.assertEqual(self.board.board.piece_at(chess.G8).piece_type, chess.QUEEN)
        self.assertEqual(self.board.board.piece_at(chess.G8).color, chess.WHITE)
    
    def test_stalemate(self):
        """Test stalemate detection."""
        # Set up a stalemate position
        self.board = TwoHSChessBoard("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        
        # Should be stalemate
        self.assertTrue(self.board.is_stalemate())
        self.assertTrue(self.board.is_game_over())
        self.assertFalse(self.board.is_checkmate())
    
    def test_fifty_moves_rule(self):
        """Test fifty moves rule detection."""
        # Set up a position close to fifty moves
        self.board = TwoHSChessBoard("k7/8/8/8/8/8/8/K7 w - - 99 50")
        
        # Not yet fifty moves
        self.assertFalse(self.board.is_fifty_moves())
        
        # Make one more move
        self.board.make_move("a1b1")
        
        # Now it should be fifty moves
        self.assertTrue(self.board.is_fifty_moves())
        self.assertTrue(self.board.is_game_over())
    
    def test_threefold_repetition(self):
        """Test threefold repetition detection."""
        # Start with a fresh board
        self.board = TwoHSChessBoard()
        
        # Make some knight moves back and forth
        moves = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
        for move in moves:
            self.board.make_move(move)
        
        # Should be threefold repetition
        self.assertTrue(self.board.is_threefold_repetition())
        self.assertTrue(self.board.is_game_over())
    
    def test_kings_step_border_cases(self):
        """Test King's Step moves at the borders of the board."""
        # Move pawn to edge first
        self.board.make_move("h2h4")
        self.board.make_move("e7e5")
        
        # Move pawn to h5
        self.board.make_move("h4h5")
        self.board.make_move("e5e4")
        
        # Try King's Step from edge - should be possible to move left
        self.assertTrue(self.board.is_move_valid("h5g4"))
        self.board.make_move("h5g4")
        
        # Check that the pawn moved
        self.assertIsNone(self.board.board.piece_at(chess.H5))
        self.assertEqual(self.board.board.piece_at(chess.G4).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.G4).color, chess.WHITE)
    
    def test_pins_with_kings_step(self):
        """Test more complex pin scenarios with King's Step."""
        # Set up a complex pin position
        self.board = TwoHSChessBoard("rnbqk1nr/pppp1ppp/8/4p3/8/2N5/PPPPBPPP/R1BQK1NR b KQkq - 0 1")
        
        # Black to move, make a regular move
        self.board.make_move("f8c5")  # Bishop to c5
        
        # White moves pawn
        self.board.make_move("d2d3")
        
        # Now black's bishop pins white's knight to king
        # Knight can only move along the pin line (diagonally)
        
        # Try to move knight with King's Step to d5 (not along pin line) - should be invalid
        self.assertFalse(self.board.is_move_valid("c3d5"))
        
        # Try to move knight with King's Step to b4 (along pin line) - should be valid
        self.assertTrue(self.board.is_move_valid("c3b4"))
        
    def test_pinned_pawn_blocking_queen(self):
        """Test that a pawn pinned by a queen cannot move."""
        # Set up the position from the screenshot where black's pawn can't move
        # White queen at h1, black king at e8, black pawn at f6 (pinned along the diagonal)
        self.board = TwoHSChessBoard("rnbqk2r/pppp1ppp/5p2/8/8/8/PPPPPP1P/RNBQK2Q b kq - 0 1")
        
        # Test the position to ensure queen is attacking along the diagonal
        king_square = self.board.king(chess.BLACK)
        self.assertEqual(king_square, chess.E8)
        self.assertEqual(self.board.board.piece_at(chess.F6).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.F6).color, chess.BLACK)
        self.assertEqual(self.board.board.piece_at(chess.H1).piece_type, chess.QUEEN)
        self.assertEqual(self.board.board.piece_at(chess.H1).color, chess.WHITE)
        
        # Pawn at f6 should not be able to move with standard move
        self.assertFalse(self.board.is_move_valid("f6f5"))
        
        # Pawn at f6 should not be able to use King's Step to move diagonally
        self.assertFalse(self.board.is_move_valid("f6e5"))
        self.assertFalse(self.board.is_move_valid("f6g5"))
        
        # Pawn at f6 should not be able to use King's Step to move horizontally
        self.assertFalse(self.board.is_move_valid("f6e6"))
        self.assertFalse(self.board.is_move_valid("f6g6"))

if __name__ == "__main__":
    unittest.main() 