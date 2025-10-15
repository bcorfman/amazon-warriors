"""State machine definitions for Amazon fighter/enemy sprites."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

import arcade
from actions import Action
from statemachine import State, StateMachine

from .animation_utils import setup_cycle

__all__ = [
    "DuelContext",
    "PlayerStateMachine",
    "EnemyStateMachine",
]


class DuelContext:
    """Container joining a sprite instance, state machine, and input state.

    Provides clear interface without runtime attribute checking.
    """

    def __init__(self, figure: arcade.Sprite, input_state=None):
        self.figure = figure
        # Input state for player, None for enemy (enemies don't use input)
        self.input_state = input_state


def auto_state_handlers(sprite_tag: str):
    """Decorator to auto-generate enter/exit methods for each State attr."""

    def decorator(cls):
        states = [name for name in dir(cls) if isinstance(getattr(cls, name), State)]

        for state_name in states:
            state_key = state_name.replace("_", " ").title().replace(" ", "_")

            # on_enter_*
            enter_name = f"on_enter_{state_name}"
            if not hasattr(cls, enter_name):

                def make_enter(s_name: str, s_key: str):
                    def _enter(self):
                        transition_method: Callable[[], None] = getattr(self, s_name.lower())
                        setup_cycle(
                            sprite=self.ctx.figure,
                            info=self.ctx.figure.state_info[s_key],
                            on_cycle_complete=lambda: transition_method(),
                            sprite_tag=sprite_tag,
                        )

                    return _enter

                setattr(cls, enter_name, make_enter(state_name, state_key))

            # on_exit_*
            exit_name = f"on_exit_{state_name}"
            if not hasattr(cls, exit_name):

                def _exit(self):  # noqa: D401
                    Action.stop_actions_for_target(self.ctx.figure, sprite_tag)

                setattr(cls, exit_name, _exit)

        return cls

    return decorator


@auto_state_handlers("player")
class PlayerStateMachine(StateMachine):
    allow_event_without_transition = True  # Don't raise exception if event can't transition

    # State definitions
    Idle = State(initial=True)
    Idle_2 = State()
    Walk = State()
    Run = State()
    Jump = State()
    Attack_1 = State()
    Attack_2 = State()
    Special = State()
    Hurt = State()
    Dead = State()

    # High-level events driven by guards
    movement = (
        Idle.to(Walk, cond="move and not shift")
        | Idle.to(Run, cond="move and shift")
        | Idle.to(Idle, unless="move")
        | Walk.to(Run, cond="move and shift")  # Still moving, shift pressed
        | Walk.to(Idle, unless="move")  # Movement released
        | Run.to(Walk, cond="move and not shift")  # Still moving, shift released
        | Run.to(Idle, unless="move")  # Movement released
    )

    # Action event: Transitions from movement states to discrete actions (Jump, Attack, Special)
    # Note: If already in a discrete action state, handle_action_input() will buffer the command
    # rather than firing this event, preventing animation restarts
    action = (
        Idle.to(Jump, cond="cmd_jump")
        | Walk.to(Jump, cond="cmd_jump")
        | Run.to(Jump, cond="cmd_jump")
        | Idle.to(Attack_1, cond="cmd_attack_1")
        | Walk.to(Attack_1, cond="cmd_attack_1")
        | Run.to(Attack_1, cond="cmd_attack_1")
        | Idle.to(Attack_2, cond="cmd_attack_2")
        | Walk.to(Attack_2, cond="cmd_attack_2")
        | Run.to(Attack_2, cond="cmd_attack_2")
        | Idle.to(Special, cond="cmd_special")
        | Walk.to(Special, cond="cmd_special")
        | Run.to(Special, cond="cmd_special")
    )

    # Auto-cycle transitions (called when animations complete)
    # These are required by the auto_state_handlers decorator
    # Idle has ~5% chance (weight=1 out of 20 total) to go to Idle_2, ~95% chance to loop
    # Note: For duration-based cooldowns, use callback_until from ArcadeActions with duration parameter
    # instead of manual time.time() checks - keeps code event-driven and elegant
    idle = Idle.to(Idle_2, weight=10) | Idle.to(Idle, weight=90)
    idle_2 = Idle_2.to(Idle)  # Idle_2 returns to Idle
    run = Run.to(Run)  # Run loops
    walk = Walk.to(Walk)  # Walk loops

    # Resume logic after discrete animations: respect Shift key for Run vs Walk
    resume = (
        Jump.to(Run, cond="move and shift")
        | Jump.to(Walk, cond="move and not shift")
        | Jump.to(Idle, unless="move")
        | Attack_1.to(Run, cond="move and shift")
        | Attack_1.to(Walk, cond="move and not shift")
        | Attack_1.to(Idle, unless="move")
        | Attack_2.to(Run, cond="move and shift")
        | Attack_2.to(Walk, cond="move and not shift")
        | Attack_2.to(Idle, unless="move")
        | Special.to(Run, cond="move and shift")
        | Special.to(Walk, cond="move and not shift")
        | Special.to(Idle, unless="move")
    )

    # Hurt and dead states (currently unused but must be reachable)
    hurt = Hurt.to(Dead)
    dead = Dead.to(Idle)
    # Make hurt reachable (though not currently used in gameplay)
    _connect_hurt = Idle.to(Hurt)

    def __init__(self, ctx: DuelContext):
        self.ctx = ctx
        self._queue = deque(maxlen=2)  # Buffer max 2 actions (deque[str])
        super().__init__()
        # Ignore events that have no valid transition in current state (e.g., movement during Jump)
        self.allow_event_without_transition = True

    # Guard conditions for events --------------------------------------------
    # These properties are evaluated by the state machine to determine which
    # transitions are valid based on current input state

    @property
    def move(self):
        return self.ctx.input_state.move

    @property
    def shift(self):
        return self.ctx.input_state.shift

    @property
    def any(self):
        return True

    # Command guards (check but DON'T consume - consumption happens in on_enter_*)
    def _check_cmd(self, name: str) -> bool:
        return self.ctx.input_state.latest_cmd == name

    def _consume_cmd(self):
        """Consume the command after successful transition."""
        self.ctx.input_state.latest_cmd = None

    @property
    def cmd_jump(self):
        return self._check_cmd("jump")

    @property
    def cmd_attack_1(self):
        return self._check_cmd("attack_1")

    @property
    def cmd_attack_2(self):
        return self._check_cmd("attack_2")

    @property
    def cmd_special(self):
        return self._check_cmd("special")

    @property
    def moving(self):
        """True when a left/right movement key is currently held down."""
        return self.move

    def _get_movement_state(self):
        """Determine which movement state to return to based on input.

        Uses clear interface from input_state - no runtime attribute checking.
        """
        if self.ctx.input_state is None:
            # No input state (e.g., for enemies or tests)
            return self.Idle

        # Use the clear interface method from InputState
        return self.ctx.input_state.get_desired_movement_state(self.Idle, self.Walk, self.Run)

    def _is_non_interruptible(self) -> bool:
        """Check if currently in a non-interruptible state.

        Non-interruptible states are: Jump, Attack_1, Attack_2, Special
        These animations must complete before accepting new action commands.
        """
        return self.Jump.is_active or self.Attack_1.is_active or self.Attack_2.is_active or self.Special.is_active

    def handle_action_input(self, cmd: str):
        """Handle an action input command, buffering if in non-interruptible state.

        This is the public API for triggering actions - it handles buffering automatically.
        If currently in a non-interruptible state (Jump, Attack, Special), the command is
        buffered for execution after the current animation completes.

        Args:
            cmd: Command string (e.g., "jump", "attack_1", "attack_2", "special")
        """
        # Check if current state is non-interruptible
        if self._is_non_interruptible():
            self._queue.append(cmd)
        else:
            # Normal action - fire the event
            self.ctx.input_state.latest_cmd = cmd
            self.action(self.ctx.input_state)

    # Custom handlers for Jump to choose destination based on movement key state
    def on_enter_Jump(self):
        """Setup jump animation, will return to Idle, Walk, or Run when complete."""
        self._consume_cmd()  # Consume the command that triggered this transition

        def on_jump_complete():
            self.resume()  # Use resume event to decide Idle/Walk/Run based on keys

        setup_cycle(
            sprite=self.ctx.figure,
            info=self.ctx.figure.state_info["Jump"],
            on_cycle_complete=on_jump_complete,
            sprite_tag="player",
        )

    # Custom handlers for Attack_1
    def on_enter_Attack_1(self):
        """Setup attack animation, will return to Idle, Walk, or Run when complete."""
        self._consume_cmd()  # Consume the command that triggered this transition

        def on_attack_complete():
            self.resume()  # Use resume event to decide Idle/Walk/Run based on keys

        setup_cycle(
            sprite=self.ctx.figure,
            info=self.ctx.figure.state_info["Attack_1"],
            on_cycle_complete=on_attack_complete,
            sprite_tag="player",
        )

    # Custom handlers for Attack_2
    def on_enter_Attack_2(self):
        """Setup attack_2 animation, will return to Idle, Walk, or Run when complete."""
        self._consume_cmd()  # Consume the command that triggered this transition

        def on_attack_complete():
            self.resume()  # Use resume event to decide Idle/Walk/Run based on keys

        setup_cycle(
            sprite=self.ctx.figure,
            info=self.ctx.figure.state_info["Attack_2"],
            on_cycle_complete=on_attack_complete,
            sprite_tag="player",
        )

    # Custom handlers for Special
    def on_enter_Special(self):
        """Setup special animation, will return to Idle, Walk, or Run when complete."""
        self._consume_cmd()  # Consume the command that triggered this transition

        def on_attack_complete():
            self.resume()  # Use resume event to decide Idle/Walk/Run based on keys

        setup_cycle(
            sprite=self.ctx.figure,
            info=self.ctx.figure.state_info["Special"],
            on_cycle_complete=on_attack_complete,
            sprite_tag="player",
        )

    # after_* hooks to drain buffer once an animation completes
    def after_jump(self):
        self._pump_queue()

    def after_attack_1(self):
        self._pump_queue()

    def after_attack_2(self):
        self._pump_queue()

    def after_special(self):
        self._pump_queue()

    def after_resume(self):
        """After resuming from a discrete action, pump the queue to execute buffered actions."""
        self._pump_queue()

    def _pump_queue(self):
        """Execute the next buffered action from the queue."""
        if self._queue:
            cmd = self._queue.popleft()
            self.ctx.input_state.latest_cmd = cmd
            self.action(self.ctx.input_state)


@auto_state_handlers("enemy")
class EnemyStateMachine(StateMachine):
    Idle = State(initial=True)
    Idle_2 = State()
    Attack_1 = State()
    Attack_2 = State()
    Jump = State()
    Run = State()
    Special = State()
    Walk = State()
    # Hurt = State()
    # Dead = State()

    idle = (
        Idle.to(Attack_1, weight=5)
        | Idle.to(Attack_2, weight=5)
        | Idle.to(Idle_2, weight=10)
        | Idle.to(Run, weight=15)
        | Idle.to(Special, weight=5)
        | Idle.to(Walk, weight=20)
        | Idle.to(Idle, weight=40)
    )

    attack_1 = (
        Attack_1.to(Attack_1, weight=10)
        | Attack_1.to(Attack_2, weight=10)
        | Attack_1.to(Special, weight=10)
        | Attack_1.to(Run, weight=15)
        | Attack_1.to(Walk, weight=25)
        | Attack_1.to(Idle, weight=30)
    )

    attack_2 = (
        Attack_2.to(Attack_1, weight=10)
        | Attack_2.to(Attack_2, weight=10)
        | Attack_2.to(Special, weight=10)
        | Attack_2.to(Run, weight=15)
        | Attack_2.to(Walk, weight=25)
        | Attack_2.to(Idle, weight=30)
    )

    special = Special.to(Walk, weight=20) | Special.to(Idle, weight=80)

    jump = (
        Jump.to(Attack_1, weight=10)
        | Jump.to(Attack_2, weight=10)
        | Jump.to(Special, weight=10)
        | Jump.to(Run, weight=15)
        | Jump.to(Walk, weight=25)
        | Jump.to(Idle, weight=30)
    )

    run = Run.to(Jump, weight=20) | Run.to(Run, weight=40) | Run.to(Walk, weight=20) | Run.to(Idle, weight=20)

    walk = (
        Walk.to(Attack_1, weight=5)
        | Walk.to(Attack_2, weight=10)
        | Walk.to(Special, weight=5)
        | Walk.to(Run, weight=25)
        | Walk.to(Walk, weight=35)
        | Walk.to(Idle, weight=15)
    )

    idle_2 = Idle_2.to(Idle)

    def __init__(self, ctx: DuelContext):
        self.ctx = ctx
        super().__init__()
