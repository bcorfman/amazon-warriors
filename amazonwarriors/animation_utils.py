"""Animation helpers and image loading utilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import arcade
from actions import callback_until, cycle_textures_until, infinite
from PIL import Image, ImageChops

__all__ = [
    "AnimInfo",
    "setup_cycle",
    "load_animation",
]


@dataclass
class AnimInfo:
    fps: int
    frame_count: int
    offset_x: int = 0
    offset_y: int = 0
    x_vel: int = 0
    y_vel: int = 0
    left_frames: list[arcade.Texture] = field(default_factory=list)
    right_frames: list[arcade.Texture] = field(default_factory=list)


def setup_cycle(
    sprite: arcade.Sprite,
    info: AnimInfo,
    direction: int,
    on_cycle_complete: Callable[[], None],
    sprite_tag: str,
) -> None:
    """Schedule a texture cycle for *sprite* and invoke *on_cycle_complete* every loop."""

    cycle_duration = len(info.frames) / info.fps
    cycle_textures_until(
        sprite,
        textures=info.frames,
        direction=direction,
        frames_per_second=info.fps,
        tag=sprite_tag,
    )
    callback_until(
        sprite,
        callback=on_cycle_complete,
        condition=infinite,
        seconds_between_calls=cycle_duration,
        tag=sprite_tag,
    )


def load_animation(
    state: str,
    info: AnimInfo,
    folder: Path,
    flip_vertical: bool = False,
) -> list[arcade.Texture]:
    """Load textures from a sprite sheet, premultiplying alpha, fully in-memory."""

    im = Image.open(folder / f"{state}.png").convert("RGBA")

    # Premultiply alpha to eliminate halo artifacts.
    r, g, b, a = im.split()
    r = ImageChops.multiply(r, a)
    g = ImageChops.multiply(g, a)
    b = ImageChops.multiply(b, a)
    im_pm = Image.merge("RGBA", (r, g, b, a))

    textures: list[arcade.Texture] = []
    frame_w = frame_h = 128
    for idx in range(info.frame_count):
        left = idx * frame_w
        frame_img = im_pm.crop((left, 0, left + frame_w, frame_h))
        tex_name = f"{state}_{idx}"
        textures.append(arcade.Texture(name=tex_name, image=frame_img))

    if flip_vertical:
        textures = [tex.flip_left_right() for tex in textures]

    return textures
