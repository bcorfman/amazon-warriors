"""Tests for backward movement restrictions.

Only Walk and Attack_1 are allowed when moving backward (left).
Run, Jump, Attack_2, and Special require forward movement (right).
"""

import pytest

from amazonwarriors.input_state import InputState
from amazonwarriors.sprites import AmazonFighter


@pytest.fixture
def player():
    """Create a player with controlled input state."""
    input_state = InputState()
    fighter = AmazonFighter(scale=1.0, input_state=input_state)
    return fighter, input_state


class TestBackwardMovementRestrictions:
    """Test that certain actions are restricted when moving backward."""

    def test_cannot_run_backward(self, player):
        """Pressing shift while moving left should only walk, not run."""
        fighter, inp = player
        sm = fighter.state_machine

        # Move left with shift held
        inp.press_left()
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Should walk, not run
        assert sm.Walk.is_active
        assert not sm.Run.is_active

    def test_can_walk_backward(self, player):
        """Walking backward (left) should work normally."""
        fighter, inp = player
        sm = fighter.state_machine

        # Move left without shift
        inp.press_left()
        sm.movement(inp)

        assert sm.Walk.is_active

    def test_cannot_jump_backward_from_idle(self, player):
        """Jumping while facing left from idle should be blocked."""
        fighter, inp = player
        sm = fighter.state_machine

        # Face left, then try to jump
        inp.press_left()
        sm.movement(inp)
        inp.release_left()
        sm.movement(inp)

        # Now try to jump (direction is still -1)
        sm.handle_action_input("jump")

        # Should stay idle, not jump
        assert sm.Idle.is_active
        assert not sm.Jump.is_active

    def test_cannot_jump_backward_from_walk(self, player):
        """Jumping while walking backward should be blocked."""
        fighter, inp = player
        sm = fighter.state_machine

        # Walk left
        inp.press_left()
        sm.movement(inp)
        assert sm.Walk.is_active

        # Try to jump
        sm.handle_action_input("jump")

        # Should stay walking, not jump
        assert sm.Walk.is_active
        assert not sm.Jump.is_active

    def test_can_attack_1_backward(self, player):
        """Attack_1 should work in any direction."""
        fighter, inp = player
        sm = fighter.state_machine

        # Face left
        inp.press_left()
        sm.movement(inp)
        inp.release_left()
        sm.movement(inp)

        # Attack_1 should work
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

    def test_can_attack_2_backward(self, player):
        """Attack_2 while facing left should be blocked."""
        fighter, inp = player
        sm = fighter.state_machine

        # Face left
        inp.press_left()
        sm.movement(inp)
        inp.release_left()
        sm.movement(inp)

        # Attack_2 should work
        sm.handle_action_input("attack_2")
        assert sm.Attack_2.is_active

    def test_cannot_special_backward(self, player):
        """Special while facing left should be blocked."""
        fighter, inp = player
        sm = fighter.state_machine

        # Face left
        inp.press_left()
        sm.movement(inp)
        inp.release_left()
        sm.movement(inp)

        # Special should work
        sm.handle_action_input("special")
        assert sm.Special.is_active


class TestForwardMovementStillWorks:
    """Verify forward movement still works as expected."""

    def test_can_run_forward(self, player):
        """Running forward should work."""
        fighter, inp = player
        sm = fighter.state_machine

        inp.press_right()
        inp.shift_key_pressed = True
        sm.movement(inp)

        assert sm.Run.is_active

    def test_can_jump_forward(self, player):
        """Jumping forward should work."""
        fighter, inp = player
        sm = fighter.state_machine

        inp.press_right()
        sm.movement(inp)

        sm.handle_action_input("jump")
        assert sm.Jump.is_active

    def test_can_attack_2_forward(self, player):
        """Attack_2 forward should work."""
        fighter, inp = player
        sm = fighter.state_machine

        inp.press_right()
        sm.movement(inp)

        sm.handle_action_input("attack_2")
        assert sm.Attack_2.is_active

    def test_can_special_forward(self, player):
        """Special forward should work."""
        fighter, inp = player
        sm = fighter.state_machine

        inp.press_right()
        sm.movement(inp)

        sm.handle_action_input("special")
        assert sm.Special.is_active


class TestDirectionSwitching:
    """Test switching directions during different states."""

    def test_running_forward_then_switching_to_backward_with_shift_becomes_walk(self, player):
        """When running forward and switching to backward while holding shift, should walk."""
        fighter, inp = player
        sm = fighter.state_machine

        # Start running forward
        inp.press_right()
        inp.shift_key_pressed = True
        sm.movement(inp)
        assert sm.Run.is_active

        # Switch to backward while keeping shift held
        inp.release_right()
        inp.press_left()
        # shift is still True
        sm.movement(inp)

        # Should walk, not run (because moving backward)
        assert sm.Walk.is_active
        assert not sm.Run.is_active
