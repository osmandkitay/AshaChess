# 2HS Chess: Modern Rules

A chess variant that adds a single elegant principle to chess: All pieces have increased maneuverability, while capturing methods remain classic.

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
- python-chess library (with custom modifications for 2HS rules)
- JavaScript and CSS for the frontend

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/osmandkitay/2chs.git
   cd 2chs
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Project Structure

```
2chs/
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

The project includes a comprehensive test suite that verifies the rules of 2HS Chess, including the custom "King's Step" rule. To run the tests:

```
cd 2chs
python -m tests.run_tests
```

The test suite includes:
- Basic chess rule tests
- King's Step move tests
- Edge cases and special situations
- Pin detection and handling

## License

This project is licensed under the ISC License. See the LICENSE file for details.