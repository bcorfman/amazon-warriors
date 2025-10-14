"""State machine definitions for Amazon fighter/enemy sprites."""

from __future__ import annotations

from collections.abc import Callable

import arcade
from actions import Action
from statemachine import State, StateMachine

from .animation_utils import setup_cycle

__all__ = [
    "DuelContext",
    "auto_state_handlers",
    "PlayerStateMachine",
    "EnemyStateMachine",
]


class DuelContext:
    """Simple container joining a sprite instance and its state machine."""

    def __init__(self, figure: arcade.Sprite):
        self.figure = figure


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

    idle = Idle.to(Idle_2, weight=50) | Idle.to(Idle, weight=50)
    idle_2 = (
        Idle_2.to(Idle)
        | Idle_2.to(Jump, weight=0)
        | Idle_2.to(Run, weight=0)
        | Idle_2.to(Walk, weight=0)
        | Idle_2.to(Attack_1, weight=0)
        | Idle_2.to(Attack_2, weight=0)
        | Idle_2.to(Special, weight=0)
    )
    jump = Jump.to(Run)
    run = Run.to(Jump)
    walk = Walk.to(Run)
    attack_1 = Attack_1.to(Run)
    attack_2 = Attack_2.to(Run)
    special = Special.to(Run)

    def __init__(self, ctx: DuelContext):
        self.ctx = ctx
        super().__init__()


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
