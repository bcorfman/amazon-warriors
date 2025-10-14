"""Sprite classes for the Amazon Warriors demo."""

from __future__ import annotations

from pathlib import Path

import arcade

from .animation_utils import AnimInfo, load_animation
from .constants import ENEMY_ASSETS_ROOT, PLAYER_ASSETS_ROOT
from .state_machines import DuelContext, EnemyStateMachine, PlayerStateMachine

__all__ = [
    "BaseAmazon",
    "AmazonFighter",
    "AmazonEnemy",
]


class BaseAmazon(arcade.Sprite):
    """Shared sprite-loading and animation logic for player & enemy."""

    def __init__(
        self,
        state_info: dict[str, AnimInfo],
        sprites_dir: Path,
        scale: float = 1.0,
        flip_vertical: bool = False,
    ) -> None:
        # Load frames for each state
        self.state_info = state_info
        for state, info in self.state_info.items():
            self.state_info[state].frames = load_animation(state, info, sprites_dir, flip_vertical)

        super().__init__(
            self.state_info["Idle"].frames,
            scale=scale,
            hit_box_algorithm="None",
        )


class AmazonFighter(BaseAmazon):
    """Player-controlled Amazon sprite."""

    PLAYER_ANIM_INFO: dict[str, AnimInfo] = {
        "Attack_1": AnimInfo(fps=10, frame_count=5),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=4),
        "Idle": AnimInfo(fps=1, frame_count=1),
        "Idle_2": AnimInfo(fps=10, frame_count=5),
        "Jump": AnimInfo(fps=10, frame_count=12),
        "Run": AnimInfo(fps=10, frame_count=10),
        "Special": AnimInfo(fps=10, frame_count=5),
        "Walk": AnimInfo(fps=10, frame_count=10),
    }

    def __init__(self, scale: float = 1.0):
        super().__init__(self.PLAYER_ANIM_INFO, PLAYER_ASSETS_ROOT, scale)
        self.ctx = DuelContext(self)
        self.state_machine = PlayerStateMachine(self.ctx)

    # Example input handling method (kept minimal)
    def on_input(self, key: int, pressed: bool):
        sm = self.state_machine
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            if pressed and sm.idle.is_active:
                sm.run()
            elif not pressed and sm.run.is_active:
                sm.idle()
        elif key == arcade.key.SPACE and pressed:
            sm.jump()
        elif key == arcade.key.LCTRL and pressed:
            sm.attack()


class AmazonEnemy(BaseAmazon):
    """AI-controlled enemy Amazon sprite."""

    ENEMY_ANIM_INFO: dict[str, AnimInfo] = {
        "Attack_1": AnimInfo(fps=10, frame_count=5),
        "Attack_2": AnimInfo(fps=10, frame_count=3),
        "Dead": AnimInfo(fps=10, frame_count=4),
        "Hurt": AnimInfo(fps=10, frame_count=4),
        "Idle": AnimInfo(fps=1, frame_count=1),
        "Idle_2": AnimInfo(fps=1, frame_count=6),
        "Jump": AnimInfo(fps=10, frame_count=11),
        "Run": AnimInfo(fps=10, frame_count=10),
        "Special": AnimInfo(fps=10, frame_count=5),
        "Walk": AnimInfo(fps=10, frame_count=10),
    }

    def __init__(self, scale: float = 1.0):
        super().__init__(self.ENEMY_ANIM_INFO, ENEMY_ASSETS_ROOT, scale, flip_vertical=True)
        self.ctx = DuelContext(self)
        self.state_machine = EnemyStateMachine(self.ctx)
