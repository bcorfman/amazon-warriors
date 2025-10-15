"""Unit tests for PlayerStateMachine behavior."""

import pytest

from amazonwarriors.input_state import InputState
from amazonwarriors.sprites import AmazonFighter


@pytest.fixture
def player():
    """Create a player with controlled input state."""
    input_state = InputState()
    fighter = AmazonFighter(scale=1.0, input_state=input_state)
    return fighter, input_state


class TestMovementTransitions:
    """Test walking and running transitions."""

    def test_idle_to_walk_on_movement(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        assert sm.Idle.is_active

        # Press movement key (no shift) -> should walk
        inp.move_key_pressed = True
        sm.movement(inp)

        assert sm.Walk.is_active

    def test_idle_to_run_on_movement_with_shift(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        assert sm.Idle.is_active

        # Press movement + shift -> should run
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)

        assert sm.Run.is_active

    def test_walk_to_idle_when_movement_released(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)
        assert sm.Walk.is_active

        # Release movement -> should idle
        inp.move_key_pressed = False
        sm.movement(inp)

        assert sm.Idle.is_active

    def test_walk_to_run_on_shift_press(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)
        assert sm.Walk.is_active

        # Press shift -> should run
        inp.shift_key_pressed = True
        sm.movement(inp)

        assert sm.Run.is_active

    def test_run_to_walk_on_shift_release(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)
        assert sm.Run.is_active

        # Release shift -> should walk
        inp.shift_key_pressed = False
        sm.movement(inp)

        assert sm.Walk.is_active


class TestDiscreteActions:
    """Test jump, attack, and buffering."""

    def test_idle_to_jump(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        assert sm.Idle.is_active

        # Press jump
        sm.handle_action_input("jump")

        assert sm.Jump.is_active

    def test_walk_to_jump(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)
        assert sm.Walk.is_active

        # Jump
        sm.handle_action_input("jump")

        assert sm.Jump.is_active

    def test_idle_to_attack(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        assert sm.Idle.is_active

        # Attack
        sm.handle_action_input("attack_1")

        assert sm.Attack_1.is_active

    def test_attack_during_jump_is_buffered(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Try to attack during jump -> should buffer
        sm.handle_action_input("attack_1")

        # Should still be jumping
        assert sm.Jump.is_active
        # Command should be buffered in queue
        assert len(sm._queue) == 1
        assert sm._queue[0] == "attack_1"

    def test_buffered_attack_executes_after_jump(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Buffer attack during jump
        sm.handle_action_input("attack_1")
        assert sm.Jump.is_active

        # Simulate jump completing and resuming to Idle
        # (In real code, animation completion would trigger this)
        sm.resume()  # Jump completes, uses resume event

        # after_jump hook automatically pumped the queue and transitioned to attack
        assert sm.Attack_1.is_active


class TestReturnToMovement:
    """Test returning to Walk/Run after discrete actions."""

    def test_jump_returns_to_idle_when_no_movement(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump from idle
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Simulate animation completing, should resume to Idle
        sm.resume()
        assert sm.Idle.is_active

    def test_jump_returns_to_walk_when_movement_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Movement key still held -> should resume to walk
        sm.resume()
        assert sm.Walk.is_active

    def test_jump_returns_to_run_when_movement_and_shift_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Movement + shift still held -> should resume to run
        sm.resume()
        assert sm.Run.is_active

    def test_attack_1_returns_to_idle_when_no_movement(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Attack from idle
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Simulate animation completing, should resume to Idle
        sm.resume()
        assert sm.Idle.is_active

    def test_attack_1_returns_to_walk_when_movement_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)

        # Attack
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Movement key still held -> should resume to walk
        sm.resume()
        assert sm.Walk.is_active

    def test_attack_1_returns_to_run_when_movement_and_shift_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Attack
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Movement + shift still held -> should resume to run
        sm.resume()
        assert sm.Run.is_active

    def test_attack_2_returns_to_walk_when_movement_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)

        # Attack_2
        sm.handle_action_input("attack_2")
        assert sm.Attack_2.is_active

        # Movement key still held -> should resume to walk
        sm.resume()
        assert sm.Walk.is_active

    def test_attack_2_returns_to_run_when_movement_and_shift_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Attack_2
        sm.handle_action_input("attack_2")
        assert sm.Attack_2.is_active

        # Movement + shift still held -> should resume to run
        sm.resume()
        assert sm.Run.is_active

    def test_special_returns_to_walk_when_movement_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)

        # Special
        sm.handle_action_input("special")
        assert sm.Special.is_active

        # Movement key still held -> should resume to walk
        sm.resume()
        assert sm.Walk.is_active

    def test_special_returns_to_run_when_movement_and_shift_held(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Special
        sm.handle_action_input("special")
        assert sm.Special.is_active

        # Movement + shift still held -> should resume to run
        sm.resume()
        assert sm.Run.is_active


class TestBufferQueue:
    """Test FIFO buffering of multiple actions."""

    def test_buffer_multiple_attacks(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")

        # Buffer first attack
        sm.handle_action_input("attack_1")

        # Buffer second attack
        sm.handle_action_input("attack_1")

        # Both should be buffered (maxlen=2)
        assert len(sm._queue) == 2

    def test_buffer_fifo_order(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")

        # Buffer different commands
        sm.handle_action_input("attack_1")
        sm.handle_action_input("special")

        # Should be in FIFO order
        assert list(sm._queue) == ["attack_1", "special"]

    def test_attack_during_attack_is_buffered(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Attack_1
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Try to attack_2 during attack_1 -> should buffer
        sm.handle_action_input("attack_2")

        # Should still be in Attack_1
        assert sm.Attack_1.is_active
        # Command should be buffered
        assert len(sm._queue) == 1
        assert sm._queue[0] == "attack_2"

    def test_special_during_jump_is_buffered(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Try to special during jump -> should buffer
        sm.handle_action_input("special")

        # Should still be jumping
        assert sm.Jump.is_active
        # Command should be buffered
        assert len(sm._queue) == 1
        assert sm._queue[0] == "special"


class TestNoAnimationRestart:
    """Test that repeatedly tapping keys doesn't restart animations."""

    def test_tapping_jump_during_jump_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Tap jump again - should buffer, not restart
        sm.handle_action_input("jump")

        # Should still be in Jump (not restarted)
        assert sm.Jump.is_active
        # Should be buffered
        assert len(sm._queue) == 1
        assert sm._queue[0] == "jump"

    def test_tapping_attack_during_attack_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Attack
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Tap attack again - should buffer, not restart
        sm.handle_action_input("attack_1")

        # Should still be in Attack_1 (not restarted)
        assert sm.Attack_1.is_active
        # Should be buffered
        assert len(sm._queue) == 1
        assert sm._queue[0] == "attack_1"

    def test_movement_during_jump_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Jump
        sm.handle_action_input("jump")
        assert sm.Jump.is_active

        # Tap movement keys - should be ignored (no transition from Jump on movement)
        inp.move_key_pressed = True
        sm.movement(inp)

        # Should still be in Jump
        assert sm.Jump.is_active

    def test_shift_during_attack_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Attack
        sm.handle_action_input("attack_1")
        assert sm.Attack_1.is_active

        # Tap shift - should be ignored
        inp.shift_key_pressed = True
        sm.movement(inp)

        # Should still be in Attack_1
        assert sm.Attack_1.is_active

    def test_tapping_shift_during_run_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)
        assert sm.Run.is_active

        # Record that we entered Run (would restart animation)
        enter_count = 0
        original_enter = sm.on_enter_Run

        def counting_enter():
            nonlocal enter_count
            enter_count += 1
            original_enter()

        sm.on_enter_Run = counting_enter

        # Tap shift again (keyboard repeat) - should NOT re-enter Run
        sm.movement(inp)

        # Should still be in Run, not re-entered
        assert sm.Run.is_active
        assert enter_count == 0  # on_enter_Run should not have been called

    def test_tapping_movement_during_run_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start running
        inp.move_key_pressed = True
        inp.shift_key_pressed = True
        sm.movement(inp)
        assert sm.Run.is_active

        # Record that we entered Run
        enter_count = 0
        original_enter = sm.on_enter_Run

        def counting_enter():
            nonlocal enter_count
            enter_count += 1
            original_enter()

        sm.on_enter_Run = counting_enter

        # Tap movement again (keyboard repeat) - should NOT re-enter Run
        sm.movement(inp)

        # Should still be in Run, not re-entered
        assert sm.Run.is_active
        assert enter_count == 0  # on_enter_Run should not have been called

    def test_tapping_movement_during_walk_does_not_restart(self, player):
        fighter, inp = player
        sm = fighter.state_machine

        # Start walking
        inp.move_key_pressed = True
        sm.movement(inp)
        assert sm.Walk.is_active

        # Record that we entered Walk
        enter_count = 0
        original_enter = sm.on_enter_Walk

        def counting_enter():
            nonlocal enter_count
            enter_count += 1
            original_enter()

        sm.on_enter_Walk = counting_enter

        # Tap movement again (keyboard repeat) - should NOT re-enter Walk
        sm.movement(inp)

        # Should still be in Walk, not re-entered
        assert sm.Walk.is_active
        assert enter_count == 0  # on_enter_Walk should not have been called


class TestIdle2Behavior:
    """Test the Idle to Idle_2 transition using weighted transitions."""

    def test_idle_can_transition_to_idle_2(self, player):
        """Test that Idle can occasionally transition to Idle_2 via weighted transition."""
        fighter, inp = player
        sm = fighter.state_machine

        assert sm.Idle.is_active

        # Try many times to trigger Idle_2 (weight=1 out of 20, so ~5% chance)
        # With 200 attempts, we have >99.99% chance of seeing at least one Idle_2
        idle_2_triggered = False
        for _ in range(200):
            sm.idle()
            if sm.Idle_2.is_active:
                idle_2_triggered = True
                break

        assert idle_2_triggered, "Idle_2 should trigger occasionally via weighted transition"

    def test_idle_2_returns_to_idle(self, player):
        """Test that Idle_2 always returns to Idle."""
        fighter, inp = player
        sm = fighter.state_machine

        # Try to get to Idle_2
        for _ in range(200):
            sm.idle()
            if sm.Idle_2.is_active:
                break

        if sm.Idle_2.is_active:
            # Complete Idle_2 animation
            sm.idle_2()

            # Should return to Idle
            assert sm.Idle.is_active
        else:
            # If we couldn't trigger Idle_2 in 200 tries, that's extremely unlikely
            # but not impossible. Skip the test in this case.
            import pytest

            pytest.skip("Could not trigger Idle_2 transition in 200 attempts")
