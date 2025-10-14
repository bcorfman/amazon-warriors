"""Arcade View classes for the demo."""

from __future__ import annotations

import arcade
from actions import Action

from .constants import BACKGROUND_COLOR, SCREEN_WIDTH
from .sprites import AmazonEnemy, AmazonFighter

__all__ = ["DuelView"]


class DuelView(arcade.View):
    def __init__(self):
        super().__init__()
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

    def on_show_view(self):
        arcade.set_background_color(BACKGROUND_COLOR)
        self.setup()

    def setup(self):
        figure_scale = 2
        player = AmazonFighter(scale=figure_scale)
        player.center_x = SCREEN_WIDTH // 4
        player.center_y = 66 * figure_scale
        self.player_list.append(player)

        enemy = AmazonEnemy(scale=figure_scale)
        enemy.center_x = 3 * SCREEN_WIDTH // 4
        enemy.center_y = 66 * figure_scale
        self.enemy_list.append(enemy)

    # Input passes to player sprite
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()
        if self.player_list:
            self.player_list[0].on_input(key, True)

    def on_key_release(self, key, modifiers):
        if self.player_list:
            self.player_list[0].on_input(key, False)

    # Update / draw
    def on_update(self, dt):
        Action.update_all(dt)
        self.player_list.update(dt)
        self.enemy_list.update(dt)

    def on_draw(self):
        self.clear()
        self.player_list.draw()
        self.enemy_list.draw()
