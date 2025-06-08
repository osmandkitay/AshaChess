import unittest
import chess
import sys
import os

# Add parent directory to path to import TwoHSChessBoard
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import TwoHSChessBoard

class TestKingsStep(unittest.TestCase):
    """Test the King's Step rule specific to 2HS Chess."""
    
    def setUp(self):
        """Set up a fresh board for each test."""
        self.board = TwoHSChessBoard()
    
    def test_pawn_kings_step(self):
        """Test that pawns can make King's Step moves."""
        # Pawns should be able to move diagonally backwards (King's Step)
        # Move white pawn e2-e4 first
        self.board.make_move("e2e4")
        
        # Now move black pawn e7-e5
        self.board.make_move("e7e5")
        
        # Move white pawn e4-d3 (diagonal backwards left - King's Step)
        self.assertTrue(self.board.is_move_valid("e4d3"))
        self.board.make_move("e4d3")
        
        # Check that the pawn moved
        self.assertIsNone(self.board.board.piece_at(chess.E4))
        self.assertEqual(self.board.board.piece_at(chess.D3).piece_type, chess.PAWN)
        self.assertEqual(self.board.board.piece_at(chess.D3).color, chess.WHITE)
        
        # Check if this was a King's Step move
        self.assertTrue(self.board.is_kings_step_move(chess.Move.from_uci("e4d3")))
    
    def test_knight_kings_step(self):
        """Test that knights can make King's Step moves."""
        # Knights should be able to move one square (King's Step)
        # Move white knight to g1-f3 first (standard move)
        self.board.make_move("g1f3")
        
        # Move black pawn
        self.board.make_move("e7e5")
        
        # Move white knight f3-g3 (King's Step, one square right)
        self.assertTrue(self.board.is_move_valid("f3g3"))
        self.board.make_move("f3g3")
        
        # Check that the knight moved
        self.assertIsNone(self.board.board.piece_at(chess.F3))
        self.assertEqual(self.board.board.piece_at(chess.G3).piece_type, chess.KNIGHT)
        self.assertEqual(self.board.board.piece_at(chess.G3).color, chess.WHITE)
        
        # Check if this was a King's Step move
        self.assertTrue(self.board.is_kings_step_move(chess.Move.from_uci("f3g3")))
    
    def test_bishop_kings_step(self):
        """Test that bishops can make King's Step moves."""
        # Set up a position where bishop can use King's Step
        self.board.make_move("e2e4")  # Pawn move to open bishop
        self.board.make_move("e7e5")  # Black pawn
        
        # Move white bishop to f1-b5 (standard diagonal move)
        self.board.make_move("f1b5")
        
        # Black pawn move
        self.board.make_move("a7a6")
        
        # Move white bishop b5-b4 (King's Step, one square down)
        self.assertTrue(self.board.is_move_valid("b5b4"))
        self.board.make_move("b5b4")
        
        # Check that the bishop moved
        self.assertIsNone(self.board.board.piece_at(chess.B5))
        self.assertEqual(self.board.board.piece_at(chess.B4).piece_type, chess.BISHOP)
        self.assertEqual(self.board.board.piece_at(chess.B4).color, chess.WHITE)
        
        # Check if this was a King's Step move
        self.assertTrue(self.board.is_kings_step_move(chess.Move.from_uci("b5b4")))
    
    def test_rook_kings_step(self):
        """Test that rooks can make King's Step moves."""
        # Set up a position where rook can use King's Step
        self.board.make_move("a2a4")  # Pawn move
        self.board.make_move("a7a5")  # Black pawn
        
        # Move white rook to a1-a3 (standard rook move)
        self.board.make_move("a1a3")
        
        # Black pawn move
        self.board.make_move("h7h6")
        
        # Move white rook a3-b2 (King's Step, diagonal)
        self.assertTrue(self.board.is_move_valid("a3b2"))
        self.board.make_move("a3b2")
        
        # Check that the rook moved
        self.assertIsNone(self.board.board.piece_at(chess.A3))
        self.assertEqual(self.board.board.piece_at(chess.B2).piece_type, chess.ROOK)
        self.assertEqual(self.board.board.piece_at(chess.B2).color, chess.WHITE)
        
        # Check if this was a King's Step move
        self.assertTrue(self.board.is_kings_step_move(chess.Move.from_uci("a3b2")))
    
    def test_kings_step_cannot_capture(self):
        """Test that King's Step moves cannot capture pieces."""
        # Set up a position with a possible capture via King's Step
        self.board = TwoHSChessBoard("rnbqkbnr/pppp1ppp/8/4p3/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2")
        
        # White pawn at d4 cannot capture black pawn at e5 with King's Step
        # This would be a diagonal move for the pawn, which is normally a capturing move
        # But King's Step cannot capture, so this should be invalid
        self.assertFalse(self.board.is_move_valid("d4e5"))
    
    def test_king_queen_no_kings_step(self):
        """Test that kings and queens cannot make King's Step moves."""
        # Kings and queens already have full movement, so they shouldn't have King's Step
        
        # Set up a position where a king might use King's Step
        self.board.make_move("e2e4")  # White pawn
        self.board.make_move("e7e5")  # Black pawn
        
        # Move white king to e1-e2 (standard king move)
        self.board.make_move("e1e2")
        
        # Move black pawn
        self.board.make_move("d7d5")
        
        # Try to move white king e2-d3 (this is already a standard king move)
        self.board.make_move("e2d3")
        
        # Check if this was a King's Step move (should be false, as kings use standard moves)
        self.assertFalse(self.board.is_kings_step_move(chess.Move.from_uci("e2d3")))
        
        # Set up a position where a queen might use King's Step
        self.board = TwoHSChessBoard()
        self.board.make_move("e2e4")  # White pawn
        self.board.make_move("e7e5")  # Black pawn
        
        # Move white queen to d1-h5 (standard queen diagonal move)
        self.board.make_move("d1h5")
        
        # Move black pawn
        self.board.make_move("d7d5")
        
        # Try to move white queen h5-g4 (this is already a standard queen move)
        self.board.make_move("h5g4")
        
        # Check if this was a King's Step move (should be false, as queens use standard moves)
        self.assertFalse(self.board.is_kings_step_move(chess.Move.from_uci("h5g4")))
    
    def test_pinned_pieces_kings_step(self):
        """Test that pinned pieces cannot make King's Step moves that expose the king to check."""
        # Set up a position with a pinned piece
        self.board = TwoHSChessBoard("rnbqk1nr/pppp1ppp/8/4p3/4P3/8/PPPPBPPP/RNBQK1NR b KQkq - 0 2")
        
        # Black's pawn at e5 is pinned by white's bishop at e2
        # Trying to move it with King's Step should be invalid
        
        # Try moving the pinned pawn e5-d4 (King's Step, diagonal forward)
        self.assertFalse(self.board.is_move_valid("e5d4"))
        
        # But the pawn can still move e5-e4 (standard move along the pin line)
        self.assertTrue(self.board.is_move_valid("e5e4"))

if __name__ == "__main__":
    unittest.main() 