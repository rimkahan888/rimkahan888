package main

import (
	"testing"

	"github.com/rimkahan888/rimkahan888/game"
)

func TestGameBasics(t *testing.T) {
	// Test creating a new game
	g := game.NewGame(19)
	if g.Board.Size != 19 {
		t.Errorf("Expected board size 19, got %d", g.Board.Size)
	}
	if g.Board.ToPlay != game.Black {
		t.Errorf("Expected Black to play first, got %v", g.Board.ToPlay)
	}

	// Test placing a stone
	err := g.PlaceStone(3, 3)
	if err != nil {
		t.Errorf("Failed to place stone: %v", err)
	}
	if g.Board.GetStone(game.Position{3, 3}) != game.Black {
		t.Errorf("Expected black stone at (3,3)")
	}
	if g.Board.ToPlay != game.White {
		t.Errorf("Expected turn to switch to White")
	}

	// Test placing on occupied position
	err = g.PlaceStone(3, 3)
	if err == nil {
		t.Errorf("Expected error when placing on occupied position")
	}

	// Test pass functionality
	g.Pass()
	if g.Board.ToPlay != game.Black {
		t.Errorf("Expected turn to switch to Black after pass")
	}
	if g.PassCount != 1 {
		t.Errorf("Expected pass count to be 1, got %d", g.PassCount)
	}

	// Test game end on double pass
	g.Pass()
	if !g.GameOver {
		t.Errorf("Expected game to be over after two passes")
	}
	if g.PassCount != 2 {
		t.Errorf("Expected pass count to be 2, got %d", g.PassCount)
	}
}

func TestBoardOperations(t *testing.T) {
	board := game.NewBoard(9)
	
	// Test valid positions
	if !board.IsValidPosition(game.Position{0, 0}) {
		t.Errorf("Position (0,0) should be valid")
	}
	if !board.IsValidPosition(game.Position{8, 8}) {
		t.Errorf("Position (8,8) should be valid")
	}
	
	// Test invalid positions
	if board.IsValidPosition(game.Position{-1, 0}) {
		t.Errorf("Position (-1,0) should be invalid")
	}
	if board.IsValidPosition(game.Position{9, 5}) {
		t.Errorf("Position (9,5) should be invalid")
	}
	
	// Test stone placement
	pos := game.Position{4, 4}
	board.SetStone(pos, game.Black)
	if board.GetStone(pos) != game.Black {
		t.Errorf("Expected black stone at center")
	}
	
	// Test neighbors
	neighbors := board.GetNeighbors(pos)
	if len(neighbors) != 4 {
		t.Errorf("Expected 4 neighbors for center position, got %d", len(neighbors))
	}
}