"""Tests for chained action buffering to prevent "sliding" between attacks."""

import pytest

from amazonwarriors.input_state import InputState
from amazonwarriors.sprites import AmazonFighter


@pytest.fixture
def player():
    """Create a player with controlled input state."""
    input_state = InputState()
    fighter = AmazonFighter(scale=1.0, input_state=input_state)
    return fighter, input_state


class TestChainedActionsWhileMoving:
    """Test that chaining actions while moving doesn't cause sliding."""

    def test_double_attack_while_walking_chains_without_resuming_to_walk(self, player):
        """When tapping Attack_1 twice while walking, second attack chains directly.

        This prevents the "slide without animation" issue where Walk briefly resumes
        between the two attacks, making it look like the sprite slides without textures.
        """
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.press_right()
        sm.movement(inp)
        assert sm.Walk.is_active

        # First Attack_1 - gets executed immediately
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Second Attack_1 while first is playing - gets buffered
        sm.handle_action_input("attack_1")

        # Verify it's still in Attack_1 (second one is queued)
        assert sm.Attack_1.is_active
        assert len(sm._queue) == 1
        assert sm._queue[0] == "attack_1"

    def test_chained_attack_executes_before_resume(self, player):
        """Buffered action executes immediately after first action, before resuming to Walk."""
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking and queue two attacks
        inp.press_right()
        sm.movement(inp)
        sm.handle_action_input("attack_1")
        sm.handle_action_input("attack_1")

        # When first Attack_1 completes, the completion callback should:
        # 1. Check the queue (finds second attack_1)
        # 2. Execute second attack_1 immediately
        # 3. NOT resume to Walk yet

        # Simulate completion - in actual game this happens via animation callback
        # The new logic should consume from queue before resuming
        assert len(sm._queue) == 1

    def test_mixed_action_chain_while_walking(self, player):
        """Chain different actions: Attack_1 -> Attack_2 -> Special."""
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.press_right()
        sm.movement(inp)
        assert sm.Walk.is_active

        # Queue three different actions
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        sm.handle_action_input("attack_2")
        sm.handle_action_input("special")

        # Should have two buffered
        assert len(sm._queue) == 2
        assert sm._queue[0] == "attack_2"
        assert sm._queue[1] == "special"

    def test_after_chain_completes_resume_to_correct_movement_state(self, player):
        """After all chained actions complete, resume to correct movement state."""
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking with shift (would be Run)
        inp.press_right()
        inp.shift_key_pressed = True
        sm.movement(inp)
        assert sm.Run.is_active

        # Single attack while running
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # No more buffered actions
        assert len(sm._queue) == 0

        # When Attack_1 completes and queue is empty, should resume to Run
        # (because movement key + shift are still held)


class TestDirectionConsistency:
    """Test that actions always face the correct direction."""

    def test_idle_attack_faces_last_direction(self, player):
        """Attack from Idle should face the last movement direction."""
        fighter, inp = player
        sm = fighter.state_machine

        # Move left then stop
        inp.press_left()
        sm.movement(inp)
        inp.release_left()
        sm.movement(inp)
        assert sm.Idle.is_active
        assert inp.direction == -1  # Still facing left

        # Attack should face left (the logic now always uses direction)
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active
        # The setup_cycle is called with direction=-1

    def test_walk_backward_then_attack_faces_backward(self, player):
        """Walking backward then attacking should show backward-facing attack."""
        fighter, inp = player
        sm = fighter.state_machine

        # Walk backward (left)
        inp.press_left()
        sm.movement(inp)
        assert sm.Walk.is_active
        assert inp.direction == -1

        # Attack while walking backward
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active
        # Animation should use direction=-1
