"""State machine definitions for Amazon fighter/enemy sprites."""

from __future__ import annotations

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
    Hurt = State()
    Dead = State()

    # unlike enemy state transitions, player transitions are controlled by the user
    # via the keyboard, so we don't need to use weights
    idle = (
        Idle.to(Idle_2)
        | Idle_2.to(Jump)
        | Idle_2.to(Run)
        | Idle_2.to(Walk)
        | Idle_2.to(Attack_1)
        | Idle_2.to(Attack_2)
        | Idle_2.to(Special)
        | Idle_2.to(Hurt)
    )
    idle_2 = (
        Idle_2.to(Idle)
        | Idle_2.to(Jump)
        | Idle_2.to(Run)
        | Idle_2.to(Walk)
        | Idle_2.to(Attack_1)
        | Idle_2.to(Attack_2)
        | Idle_2.to(Special)
        | Idle_2.to(Hurt)
    )
    jump = (
        Jump.to(Idle)
        | Jump.to(Jump)
        | Jump.to(Run)
        | Jump.to(Walk)
        | Jump.to(Attack_1)
        | Jump.to(Attack_2)
        | Jump.to(Special)
        | Jump.to(Hurt)
    )
    run = (
        Run.to(Idle)
        | Run.to(Jump)
        | Run.to(Run)
        | Run.to(Walk)
        | Run.to(Attack_1)
        | Run.to(Attack_2)
        | Run.to(Special)
        | Run.to(Hurt)
    )
    walk = (
        Walk.to(Idle)
        | Walk.to(Jump)
        | Walk.to(Run)
        | Walk.to(Walk)
        | Walk.to(Attack_1)
        | Walk.to(Attack_2)
        | Walk.to(Special)
        | Walk.to(Hurt)
    )
    attack_1 = (
        Attack_1.to(Idle)
        | Attack_1.to(Jump)
        | Attack_1.to(Run)
        | Attack_1.to(Walk)
        | Attack_1.to(Attack_1)
        | Attack_1.to(Attack_2)
        | Attack_1.to(Special)
        | Attack_1.to(Hurt)
    )
    attack_2 = (
        Attack_2.to(Idle)
        | Attack_2.to(Jump)
        | Attack_2.to(Run)
        | Attack_2.to(Walk)
        | Attack_2.to(Attack_1)
        | Attack_2.to(Attack_2)
        | Attack_2.to(Special)
        | Attack_2.to(Hurt)
    )
    special = Special.to(Walk) | Special.to(Idle)
    hurt = Hurt.to(Dead)
    dead = Dead.to(Idle)

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
