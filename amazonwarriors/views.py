"""Arcade View classes for the demo."""

from __future__ import annotations

import arcade
from actions import Action

from .constants import BACKGROUND_COLOR, SCREEN_WIDTH
from .input_state import InputState
from .sprites import AmazonEnemy, AmazonFighter

__all__ = ["DuelView"]


class DuelView(arcade.View):
    figure_scale = 2

    def __init__(self):
        super().__init__()
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        # Input state with clear interface (no runtime attribute checking needed)
        self.input_state = InputState()

        # Create player with access to input state
        self.player = AmazonFighter(scale=self.figure_scale, input_state=self.input_state)
        self.enemy = AmazonEnemy(scale=self.figure_scale)

    def on_show_view(self):
        arcade.set_background_color(BACKGROUND_COLOR)
        self.setup()

    def setup(self):
        self.player.center_x = SCREEN_WIDTH // 4
        self.player.center_y = 66 * self.figure_scale
        self.player_list.append(self.player)

        enemy = AmazonEnemy(scale=self.figure_scale)
        enemy.center_x = 3 * SCREEN_WIDTH // 4
        enemy.center_y = 66 * self.figure_scale
        self.enemy_list.append(enemy)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()

        # Track continuous movement input and fire movement event
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.input_state.move_key_pressed = True
            self.player.state_machine.movement(self.input_state)
        elif key == arcade.key.LSHIFT:
            self.input_state.shift_key_pressed = True
            self.player.state_machine.movement(self.input_state)

        # Handle discrete actions - use handle_action_input which buffers automatically
        elif key == arcade.key.SPACE:
            self.player.state_machine.handle_action_input("jump")

        elif key == arcade.key.LCTRL:
            self.player.state_machine.handle_action_input("attack_1")

    def on_key_release(self, key, modifiers):
        # Track continuous movement input and fire movement event
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.input_state.move_key_pressed = False
            self.player.state_machine.movement(self.input_state)
        elif key == arcade.key.LSHIFT:
            self.input_state.shift_key_pressed = False
            self.player.state_machine.movement(self.input_state)

    # Update / draw
    def on_update(self, dt):
        Action.update_all(dt)
        self.player_list.update(dt)
        self.enemy_list.update(dt)

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.enemy_list.draw()
