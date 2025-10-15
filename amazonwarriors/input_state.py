"""Input state container for clean interface between View and StateMachine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputState:
    """Container for current input state.

    Provides a clear interface without runtime attribute checking.
    All fields always exist with default values.
    """

    move_key_pressed: bool = False
    shift_key_pressed: bool = False
    # Latest discrete command pressed this frame (e.g. "jump", "attack_1")
    latest_cmd: str | None = None

    # Guard-friendly helpers used directly by the state machine
    @property
    def move(self) -> bool:
        return self.move_key_pressed

    @property
    def shift(self) -> bool:
        return self.shift_key_pressed

    def get_desired_movement_state(self, idle_state, walk_state, run_state):
        """Determine which movement state should be active based on input.

        Args:
            idle_state: State object for Idle
            walk_state: State object for Walk
            run_state: State object for Run

        Returns:
            The appropriate state based on input flags
        """
        if self.move_key_pressed:
            if self.shift_key_pressed:
                return run_state  # Move + Shift = Run
            else:
                return walk_state  # Move only = Walk
        return idle_state  # No movement = Idle
