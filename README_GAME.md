# Go Game (Weiqi/Baduk)

A complete implementation of the ancient board game Go (also known as Weiqi or Baduk) built with Go programming language and styled with Tailwind CSS.

![Go Game Screenshot](https://github.com/user-attachments/assets/5591a69e-d574-48f6-9e66-66f4388755f4)

## Features

- **Full 19x19 Go Board**: Traditional board size with proper grid layout
- **Complete Game Logic**: 
  - Stone placement with validation
  - Capture detection and removal
  - Liberty checking (prevents suicidal moves)
  - Turn-based gameplay
  - Pass functionality
  - Game end detection (double pass)
  - Basic scoring with komi
- **Modern Web Interface**: 
  - Responsive design with Tailwind CSS
  - Real-time game state updates
  - Interactive board with click-to-place
  - Game status tracking
  - Capture counting
- **RESTful API**: JSON endpoints for all game operations

## How to Play

1. **Objective**: Surround territory and capture opponent stones
2. **Placing Stones**: Click on any empty intersection to place a stone
3. **Capturing**: Surround opponent stones to remove them from the board
4. **Liberties**: Stones must have at least one adjacent empty space (liberty)
5. **Passing**: Click "Pass" when you don't want to make a move
6. **Game End**: Game ends when both players pass consecutively

## Technical Stack

- **Backend**: Go (Golang) with standard library HTTP server
- **Frontend**: HTML5, JavaScript, CSS
- **Styling**: Tailwind CSS (via CDN)
- **Architecture**: Single-page application with RESTful API

## Running the Game

1. **Prerequisites**: Go 1.19+ installed

2. **Clone and run**:
   ```bash
   git clone https://github.com/rimkahan888/rimkahan888.git
   cd rimkahan888
   go run .
   ```

3. **Open your browser**: Navigate to `http://localhost:8080`

## API Endpoints

- `GET /` - Game interface
- `GET /api/game-state` - Current game state (JSON)
- `POST /api/place-stone` - Place a stone `{"row": 3, "col": 3}`
- `POST /api/pass` - Pass current turn
- `POST /api/new-game` - Start new game

## Game Rules Implemented

- ✅ Basic stone placement
- ✅ Turn alternation (Black plays first)
- ✅ Capture by surrounding (removing stones without liberties)
- ✅ Suicide rule (cannot place stones without liberties unless capturing)
- ✅ Pass functionality
- ✅ Game end on double pass
- ✅ Basic territory scoring with komi (7 points for White)
- ❌ Ko rule (not implemented - would prevent immediate recapture)
- ❌ Advanced scoring (Chinese/Japanese rules)

## Testing

Run the test suite:
```bash
go test -v
```

## Project Structure

```
.
├── main.go              # Web server and HTTP handlers
├── main_test.go         # Test suite
├── game/
│   ├── board.go         # Board representation and basic operations
│   └── game.go          # Game logic, rules, and state management
└── README.md
```

## Development

The game implements core Go rules with a focus on simplicity and clarity. The codebase is well-structured with separation between game logic and web interface, making it easy to extend or modify rules.

To add new features:
1. Extend the game logic in `game/` package
2. Add corresponding API endpoints in `main.go`
3. Update the frontend JavaScript for new functionality
4. Add tests for new features

## License

This project is open source and available under the MIT License.