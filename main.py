"""Entry point for Amazon Warriors demo."""

from __future__ import annotations

import arcade
from actions import center_window

from amazonwarriors.constants import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
from amazonwarriors.views import DuelView


def main() -> None:
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, visible=False)
    center_window(window)
    window.set_visible(True)
    window.show_view(DuelView())
    arcade.run()


if __name__ == "__main__":
    main()
