# ASHA CHESS: Modern Rules

A chess variant that adds a single elegant principle to chess: All pieces have increased maneuverability, while capturing methods remain classic.

## ASHA CHESS: A Manifesto for a New Era

Today, the grand game of chess is suffocating. Its infinite possibilities are chained by rote memorization, its soul traded for the cold precision of scripted openings. We watch the world's greatest players, and too often, we see not human creativity, but the ghost of an AI, their moves echoing the predictability of a machine. The very essence of chess—the clash of unique minds—is fading.

It has been said that "chess is a mirror to life," and traditional chess was a perfect reflection of its time: a world of rigid hierarchies, where each piece had a strictly defined role. But our world has changed.

The modern era, born from the fires of revolution and built on the ideals of democracy and universal rights, presents us with a new paradigm. It suggests, even if only as a beautiful illusion, that all individuals possess a fundamental freedom of movement. ASHA CHESS embraces this with a postmodern touch, asking a simple yet profound question: What if every piece on the board was granted the right to move like a king?

In ASHA CHESS, we do not erase tradition; we build upon it. The "King's Step"—a single-square move in any direction—is now bestowed upon Pawns, Knights, Bishops, and Rooks. However, their methods of capture remain classic, tied to their unique histories. This creates a breathtaking new dynamic. A Bishop, no longer confined to a single color, can now step onto a neighboring square, reflecting a world where even the most rigid dogmas can evolve. The Pawn, once a fated foot soldier, becomes an unpredictable force, capable of both subtle repositioning and sudden threats.

Our goal is to resurrect the spirit of players like Mikhail Tal, Rashid Nezhmetdinov, and Joseph Blackburne—artists who played with character, whose moves were a signature of their very being. We should not see AI-approved lines when we look at Magnus Carlsen; we should see Magnus. Chess must be a canvas for grand strategies and profound, personal expression.

I am not a grandmaster, but a deep lover of the game, and I despise an opponent who merely recites from a book. ASHA CHESS is my proposal to restore the game's depth and dynamism. I do not claim to have uncovered its full potential; that is a journey we must take together. This is an invitation to experiment, to criticize, and to play.

For too long, the art of chess has resembled a Renaissance painting—a masterpiece, yes, but one forever bound by the fixed algorithms of perspective and form.

Together, let's usher in its next great movement.

*By Osman Derviş Kıtay [@AiDervish](https://x.com/AiDervish)*

## Game Rules

### Main Principle: "King's Step" (For Movement Only)

New Ability: Pawns, Knights, Bishops, and Rooks gain a new ability called the "King's Step" in addition to their classic movements.

Rule Definition: The "King's Step" is a one-square movement in any direction (horizontal, vertical, diagonal).

Most Important Rule: This "King's Step" move CANNOT be used to capture opponent pieces. This ability is only for changing position, setting up defenses, or moving to a new attack position.

### Capturing Rules

Capturing actions remain UNCHANGED. A piece can capture an opponent's piece only using its traditional attack method:

- Pawn: Can only capture pieces diagonally forward
- Knight: Can only capture pieces at the end of its "L" move
- Bishop: Can only capture by moving diagonally
- Rook: Can only capture by moving horizontally or vertically

### Unchanged Rules

- Queen and King: Their movements and capturing methods are identical to traditional chess
- Other Rules: Castling, Check, Checkmate, Stalemate, Promotion, and other chess rules remain valid

## How to Play

In the game interface:
- Valid movement squares are highlighted in green
- Valid capturing squares are highlighted in orange
- Pieces in check are highlighted in red

## Python Web Implementation

This implementation uses:
- Python with Flask for the backend
- python-chess library (with custom modifications for ASHA CHESS rules)
- JavaScript and CSS for the frontend

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/osmandkitay/ASHA-CHESS.git
   cd ASHA-CHESS
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Open your browser and navigate 
   ```

### Project Structure

```
ASHA-CHESS/
├── app.py              # Main Flask application with chess logic
├── run.py              # Script to run the server
├── requirements.txt    # Python dependencies
├── static/             # Static files
│   ├── css/            # Stylesheets
│   │   └── style.css   # Main stylesheet
│   └── js/             # JavaScript files
│       └── chess.js    # Frontend chess logic
└── templates/          # HTML templates
    └── index.html      # Main game page
```

### Testing

The project includes a comprehensive test suite that verifies the rules of ASHA CHESS, including the custom "King's Step" rule. To run the tests:

```
cd ASHA-CHESS
python -m tests.run_tests
```

The test suite includes:
- Basic chess rule tests
- King's Step move tests
- Edge cases and special situations
- Pin detection and handling

## License

This project is licensed under the ISC License. See the LICENSE file for details.