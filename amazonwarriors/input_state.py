"""Input state container for clean interface between View and StateMachine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputState:
    """Container for current input state.

    Provides a clear interface without runtime attribute checking.
    All fields always exist with default values.
    """

    shift_key_pressed: bool = False
    # Direction: -1 = left/backward, 0 = none, +1 = right/forward
    direction: int = 1
    # Latest discrete command pressed this frame (e.g. "jump", "attack_1")
    latest_cmd: str | None = None

    # Track which arrow keys are currently held down (internal state)
    _left_pressed: bool = False
    _right_pressed: bool = False

    # Guard-friendly helpers used directly by the state machine
    @property
    def move(self) -> bool:
        """True if any movement key is currently pressed."""
        return self._left_pressed or self._right_pressed

    @property
    def move_key_pressed(self) -> bool:
        """Alias for move property for compatibility."""
        return self.move

    @property
    def shift(self) -> bool:
        return self.shift_key_pressed

    def press_left(self):
        """Handle left arrow key press."""
        self._left_pressed = True
        self._update_direction()

    def release_left(self):
        """Handle left arrow key release."""
        self._left_pressed = False
        self._update_direction()

    def press_right(self):
        """Handle right arrow key press."""
        self._right_pressed = True
        self._update_direction()

    def release_right(self):
        """Handle right arrow key release."""
        self._right_pressed = False
        self._update_direction()

    def _update_direction(self):
        """Update direction based on currently pressed arrow keys.

        Direction priority: if both left and right are pressed, right takes precedence.
        If only one is pressed, use that direction.
        If neither is pressed, maintain last direction.
        """
        if self._right_pressed:
            self.direction = 1  # Right/forward
        elif self._left_pressed:
            self.direction = -1  # Left/backward
        # If neither pressed, keep previous direction

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
