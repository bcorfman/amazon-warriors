"""Tests for DuelView with isolated module stubbing.

This module uses pytest fixtures to stub arcade/actions/PIL modules
only for tests in this file, preventing interference with other tests.
"""

import importlib
import sys
import types
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def stub_modules():
    """Stub heavy dependencies for view tests only."""
    # Save original modules if they exist
    original_modules = {}
    modules_to_stub = ["arcade", "actions", "PIL", "PIL.Image", "PIL.ImageChops", "statemachine"]

    for mod_name in modules_to_stub:
        if mod_name in sys.modules:
            original_modules[mod_name] = sys.modules[mod_name]

    # Create arcade stub
    arcade_stub = types.ModuleType("arcade")
    arcade_stub.key = SimpleNamespace(LEFT=1, RIGHT=2, LSHIFT=3, SPACE=4, LCTRL=5, ESCAPE=6)

    class _FakeSpriteList(list):
        def update(self, *_args, **_kwargs):
            pass

        def draw(self):
            pass

    class _FakeSprite:
        def __init__(self, *args, **kwargs):
            self.texture = None

        def update(self, *args, **kwargs):
            pass

        def draw(self, *args, **kwargs):
            pass

    class _FakeView:
        def __init__(self):
            self.window = None

        def clear(self):
            pass

    arcade_stub.SpriteList = _FakeSpriteList
    arcade_stub.Sprite = _FakeSprite
    arcade_stub.View = _FakeView
    arcade_stub.Texture = type("Texture", (), {})
    arcade_stub.load_texture = lambda *a, **k: None
    arcade_stub.color = SimpleNamespace(DARK_MIDNIGHT_BLUE=(0, 0, 0))
    arcade_stub.set_background_color = lambda *a, **k: None

    # Create actions stub
    actions_stub = types.ModuleType("actions")

    def _noop_update_all(_dt):
        _noop_update_all.called = True  # type: ignore[attr-defined]

    _noop_update_all.called = False  # type: ignore[attr-defined]

    class _DummyAction:
        @staticmethod
        def stop_actions_for_target(*_args, **_kwargs):
            pass

        @staticmethod
        def update_all(dt):
            _noop_update_all(dt)

    actions_stub.update_all = _noop_update_all
    actions_stub.Action = _DummyAction
    actions_stub.callback_until = lambda *a, **k: None
    actions_stub.cycle_textures_until = lambda *a, **k: None
    actions_stub.infinite = lambda: False

    # Create PIL stubs
    pil_stub = types.ModuleType("PIL")
    pil_image_stub = types.ModuleType("PIL.Image")
    pil_imagechops_stub = types.ModuleType("PIL.ImageChops")
    pil_image_stub.open = lambda *a, **k: None
    pil_imagechops_stub.difference = lambda *a, **k: None
    pil_stub.Image = pil_image_stub
    pil_stub.ImageChops = pil_imagechops_stub

    # Create statemachine stub
    statemachine_stub = types.ModuleType("statemachine")

    class _DummyState:
        def __init__(self, *args, **kwargs):
            self.is_active = False

        def to(self, *args, **kwargs):
            return self

        def __or__(self, other):
            return self

    class _DummyStateMachine:
        def __init__(self, *args, **kwargs):
            pass

    statemachine_stub.State = _DummyState
    statemachine_stub.StateMachine = _DummyStateMachine

    # Install stubs
    sys.modules["arcade"] = arcade_stub
    sys.modules["actions"] = actions_stub
    sys.modules["PIL"] = pil_stub
    sys.modules["PIL.Image"] = pil_image_stub
    sys.modules["PIL.ImageChops"] = pil_imagechops_stub
    sys.modules["statemachine"] = statemachine_stub

    # Force reload of amazonwarriors modules to pick up stubbed dependencies
    for mod_name in [
        "amazonwarriors.views",
        "amazonwarriors.sprites",
        "amazonwarriors.state_machines",
        "amazonwarriors.animation_utils",
    ]:
        sys.modules.pop(mod_name, None)

    # Patch load_animation before importing views
    anim_utils = importlib.import_module("amazonwarriors.animation_utils")
    original_load_animation = anim_utils.load_animation

    def _dummy_load_animation(state, info, sprites_dir):
        return [None]  # Return fake texture list

    anim_utils.load_animation = _dummy_load_animation  # type: ignore[attr-defined]

    views = importlib.import_module("amazonwarriors.views")
    # Patch Action directly on views to use our stub
    views.Action = _DummyAction  # type: ignore[attr-defined]

    # Stub sprite classes
    class _DummyStateMachine:
        def __init__(self):
            self.movement_calls: list = []
            self.action_calls: list = []

        def movement(self, input_state):
            self.movement_calls.append(input_state)

        def handle_action_input(self, cmd):
            self.action_calls.append(cmd)

    class _DummySprite:
        def __init__(self, *_, **kwargs):
            self.state_machine = _DummyStateMachine()
            self.scale = kwargs.get("scale", 1)
            self.input_state = kwargs.get("input_state")
            self.center_x = 0
            self.center_y = 0

    views.AmazonFighter = _DummySprite  # type: ignore[attr-defined]
    views.AmazonEnemy = _DummySprite  # type: ignore[attr-defined]

    # Store refs for tests
    stub_refs = SimpleNamespace(
        views=views,
        arcade=arcade_stub,
        Action=_DummyAction,
        noop_update_all=_noop_update_all,
    )

    yield stub_refs

    # Cleanup: restore original modules
    anim_utils.load_animation = original_load_animation  # type: ignore[attr-defined]

    for mod_name in modules_to_stub:
        if mod_name in original_modules:
            sys.modules[mod_name] = original_modules[mod_name]
        else:
            sys.modules.pop(mod_name, None)

    # Force reload of amazonwarriors modules to pick up real dependencies
    for mod_name in [
        "amazonwarriors.animation_utils",
        "amazonwarriors.state_machines",
        "amazonwarriors.sprites",
        "amazonwarriors.views",
    ]:
        sys.modules.pop(mod_name, None)


def test_move_key_press_and_release(stub_modules):
    views = stub_modules.views
    view = views.DuelView()
    view.window = SimpleNamespace(close=lambda: setattr(view.window, "closed", True))

    # Simulate LEFT key press
    view.on_key_press(views.arcade.key.LEFT, 0)
    assert view.input_state.move_key_pressed is True
    assert view.input_state.direction == -1  # Left = backward
    assert len(view.player.state_machine.movement_calls) == 1

    # Simulate LEFT key release
    view.on_key_release(views.arcade.key.LEFT, 0)
    assert view.input_state.move_key_pressed is False
    assert view.input_state.direction == -1  # Maintains last direction
    assert len(view.player.state_machine.movement_calls) == 2


def test_shift_key_press_and_release(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    view.on_key_press(views.arcade.key.LSHIFT, 0)
    assert view.input_state.shift_key_pressed is True

    view.on_key_release(views.arcade.key.LSHIFT, 0)
    assert view.input_state.shift_key_pressed is False


def test_discrete_action_jump_and_attack(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    view.on_key_press(views.arcade.key.SPACE, 0)
    assert view.player.state_machine.action_calls == ["jump"]

    view.on_key_press(views.arcade.key.LCTRL, 0)
    assert view.player.state_machine.action_calls == ["jump", "attack_1"]


def test_escape_closes_window(stub_modules):
    views = stub_modules.views
    view = views.DuelView()
    view.window = SimpleNamespace(close=lambda: setattr(view.window, "closed", True))

    view.on_key_press(views.arcade.key.ESCAPE, 0)
    assert getattr(view.window, "closed", False) is True


def test_on_update_calls_action_update_all(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    stub_modules.noop_update_all.called = False  # type: ignore[attr-defined]
    view.on_update(0.1)
    assert stub_modules.noop_update_all.called is True  # type: ignore[attr-defined]


def test_setup_initialises_sprites(stub_modules):
    views = stub_modules.views
    view = views.DuelView()
    view.setup()

    # One player + one enemy in lists after setup()
    assert len(view.player_list) == 1
    assert len(view.enemy_list) == 1


def test_right_key_sets_forward_direction(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    view.on_key_press(views.arcade.key.RIGHT, 0)
    assert view.input_state.direction == 1  # Right = forward
    assert view.input_state.move_key_pressed is True


def test_direction_priority_when_both_keys_pressed(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    # Press left first
    view.on_key_press(views.arcade.key.LEFT, 0)
    assert view.input_state.direction == -1

    # Then press right while left is held - right takes precedence
    view.on_key_press(views.arcade.key.RIGHT, 0)
    assert view.input_state.direction == 1  # Right wins
    assert view.input_state.move_key_pressed is True

    # Release right - should switch back to left
    view.on_key_release(views.arcade.key.RIGHT, 0)
    assert view.input_state.direction == -1  # Back to left
    assert view.input_state.move_key_pressed is True  # Still moving


def test_switching_directions(stub_modules):
    views = stub_modules.views
    view = views.DuelView()

    # Start moving right
    view.on_key_press(views.arcade.key.RIGHT, 0)
    assert view.input_state.direction == 1

    # Release and press left
    view.on_key_release(views.arcade.key.RIGHT, 0)
    view.on_key_press(views.arcade.key.LEFT, 0)
    assert view.input_state.direction == -1
