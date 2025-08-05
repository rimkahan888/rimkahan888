package game

import (
	"errors"
)

// Game represents a Go game
type Game struct {
	Board          *Board
	BlackCaptures  int
	WhiteCaptures  int
	PassCount      int
	GameOver       bool
	Winner         Stone
	LastMove       *Move
}

// NewGame creates a new Go game
func NewGame(size int) *Game {
	return &Game{
		Board:         NewBoard(size),
		BlackCaptures: 0,
		WhiteCaptures: 0,
		PassCount:     0,
		GameOver:      false,
		Winner:        Empty,
	}
}

// PlaceStone attempts to place a stone at the given position
func (g *Game) PlaceStone(row, col int) error {
	if g.GameOver {
		return errors.New("game is over")
	}
	
	pos := Position{Row: row, Col: col}
	
	// Check if position is valid
	if !g.Board.IsValidPosition(pos) {
		return errors.New("invalid position")
	}
	
	// Check if position is empty
	if g.Board.GetStone(pos) != Empty {
		return errors.New("position already occupied")
	}
	
	// Temporarily place the stone
	g.Board.SetStone(pos, g.Board.ToPlay)
	
	// Check for captures
	captured := g.checkCaptures(pos)
	
	// Check if the move is suicidal
	if len(captured) == 0 && !g.hasLiberties(pos) {
		// Undo the temporary placement
		g.Board.SetStone(pos, Empty)
		return errors.New("suicidal move not allowed")
	}
	
	// Apply captures
	for _, capturedPos := range captured {
		g.Board.SetStone(capturedPos, Empty)
		if g.Board.ToPlay == Black {
			g.BlackCaptures++
		} else {
			g.WhiteCaptures++
		}
	}
	
	// Record the move
	move := Move{
		Player:   g.Board.ToPlay,
		Position: pos,
		Pass:     false,
	}
	g.Board.Moves = append(g.Board.Moves, move)
	g.LastMove = &move
	
	// Switch players
	g.switchPlayer()
	g.PassCount = 0
	
	return nil
}

// Pass allows a player to pass their turn
func (g *Game) Pass() {
	if g.GameOver {
		return
	}
	
	move := Move{
		Player:   g.Board.ToPlay,
		Position: Position{-1, -1},
		Pass:     true,
	}
	g.Board.Moves = append(g.Board.Moves, move)
	g.LastMove = &move
	
	g.PassCount++
	
	// Game ends if both players pass consecutively
	if g.PassCount >= 2 {
		g.GameOver = true
		g.determineWinner()
	}
	
	g.switchPlayer()
}

// switchPlayer switches the current player
func (g *Game) switchPlayer() {
	if g.Board.ToPlay == Black {
		g.Board.ToPlay = White
	} else {
		g.Board.ToPlay = Black
	}
}

// checkCaptures checks for captured groups and returns their positions
func (g *Game) checkCaptures(lastPlaced Position) []Position {
	captured := []Position{}
	opponent := g.getOpponent(g.Board.ToPlay)
	
	// Check all neighboring positions for opponent stones
	for _, neighbor := range g.Board.GetNeighbors(lastPlaced) {
		if g.Board.GetStone(neighbor) == opponent {
			group := g.getGroup(neighbor)
			if !g.groupHasLiberties(group) {
				captured = append(captured, group...)
			}
		}
	}
	
	return captured
}

// hasLiberties checks if a stone at the given position has liberties
func (g *Game) hasLiberties(pos Position) bool {
	group := g.getGroup(pos)
	return g.groupHasLiberties(group)
}

// getGroup returns all stones connected to the stone at the given position
func (g *Game) getGroup(pos Position) []Position {
	if !g.Board.IsValidPosition(pos) || g.Board.GetStone(pos) == Empty {
		return []Position{}
	}
	
	color := g.Board.GetStone(pos)
	visited := make(map[Position]bool)
	group := []Position{}
	stack := []Position{pos}
	
	for len(stack) > 0 {
		current := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		
		if visited[current] {
			continue
		}
		
		visited[current] = true
		group = append(group, current)
		
		// Add neighbors of the same color to the stack
		for _, neighbor := range g.Board.GetNeighbors(current) {
			if !visited[neighbor] && g.Board.GetStone(neighbor) == color {
				stack = append(stack, neighbor)
			}
		}
	}
	
	return group
}

// groupHasLiberties checks if a group of stones has any liberties
func (g *Game) groupHasLiberties(group []Position) bool {
	for _, pos := range group {
		for _, neighbor := range g.Board.GetNeighbors(pos) {
			if g.Board.GetStone(neighbor) == Empty {
				return true
			}
		}
	}
	return false
}

// getOpponent returns the opponent's stone color
func (g *Game) getOpponent(player Stone) Stone {
	if player == Black {
		return White
	}
	return Black
}

// determineWinner determines the winner of the game (simplified scoring)
func (g *Game) determineWinner() {
	// Simple scoring: count stones + captures
	blackStones := 0
	whiteStones := 0
	
	for i := 0; i < g.Board.Size; i++ {
		for j := 0; j < g.Board.Size; j++ {
			stone := g.Board.GetStone(Position{i, j})
			if stone == Black {
				blackStones++
			} else if stone == White {
				whiteStones++
			}
		}
	}
	
	blackScore := blackStones + g.BlackCaptures
	whiteScore := whiteStones + g.WhiteCaptures + 7 // Komi for white (rounded)
	
	if blackScore > whiteScore {
		g.Winner = Black
	} else {
		g.Winner = White
	}
}

// NewGameFromSize creates a new game with the specified board size
func NewGameFromSize(size int) *Game {
	return NewGame(size)
}