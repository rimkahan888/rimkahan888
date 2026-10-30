package game

import (
	"fmt"
)

// Stone represents a stone on the board
type Stone int

const (
	Empty Stone = iota
	Black
	White
)

func (s Stone) String() string {
	switch s {
	case Empty:
		return "."
	case Black:
		return "●"
	case White:
		return "○"
	default:
		return "?"
	}
}

// Position represents a position on the board
type Position struct {
	Row, Col int
}

// Board represents the Go board
type Board struct {
	Size   int
	Grid   [][]Stone
	Moves  []Move
	ToPlay Stone
}

// Move represents a move in the game
type Move struct {
	Player   Stone
	Position Position
	Pass     bool
}

// NewBoard creates a new Go board
func NewBoard(size int) *Board {
	if size < 5 || size > 25 {
		size = 19 // Default to 19x19
	}
	
	grid := make([][]Stone, size)
	for i := range grid {
		grid[i] = make([]Stone, size)
	}
	
	return &Board{
		Size:   size,
		Grid:   grid,
		Moves:  make([]Move, 0),
		ToPlay: Black, // Black plays first
	}
}

// IsValidPosition checks if a position is valid on the board
func (b *Board) IsValidPosition(pos Position) bool {
	return pos.Row >= 0 && pos.Row < b.Size && pos.Col >= 0 && pos.Col < b.Size
}

// GetStone returns the stone at the given position
func (b *Board) GetStone(pos Position) Stone {
	if !b.IsValidPosition(pos) {
		return Empty
	}
	return b.Grid[pos.Row][pos.Col]
}

// SetStone places a stone at the given position
func (b *Board) SetStone(pos Position, stone Stone) {
	if b.IsValidPosition(pos) {
		b.Grid[pos.Row][pos.Col] = stone
	}
}

// GetNeighbors returns the neighboring positions
func (b *Board) GetNeighbors(pos Position) []Position {
	neighbors := []Position{}
	directions := []Position{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	
	for _, dir := range directions {
		neighbor := Position{pos.Row + dir.Row, pos.Col + dir.Col}
		if b.IsValidPosition(neighbor) {
			neighbors = append(neighbors, neighbor)
		}
	}
	
	return neighbors
}

// String returns a string representation of the board
func (b *Board) String() string {
	result := "  "
	for i := 0; i < b.Size; i++ {
		result += fmt.Sprintf("%2d", i)
	}
	result += "\n"
	
	for i := 0; i < b.Size; i++ {
		result += fmt.Sprintf("%2d", i)
		for j := 0; j < b.Size; j++ {
			result += fmt.Sprintf(" %s", b.Grid[i][j])
		}
		result += "\n"
	}
	
	return result
}