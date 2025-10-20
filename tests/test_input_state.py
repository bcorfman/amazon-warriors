import pytest

from amazonwarriors.input_state import InputState


class DummyState:  # lightweight sentinel "state" objects
    pass


IDLE = DummyState()
WALK = DummyState()
RUN = DummyState()


@pytest.mark.parametrize(
    "left, right, shift, expected",
    [
        (False, False, False, IDLE),  # 1) No movement key
        (False, True, False, WALK),  # 2) Move right without Shift -> Walk
        (True, False, False, WALK),  # 3) Move left without Shift -> Walk
        (False, True, True, RUN),  # 4) Move right + Shift -> Run
        (True, False, True, RUN),  # 5) Move left + Shift -> Run
    ],
)
def test_get_desired_movement_state(left, right, shift, expected):
    state = InputState(shift_key_pressed=shift)
    if left:
        state.press_left()
    if right:
        state.press_right()
    result = state.get_desired_movement_state(IDLE, WALK, RUN)
    assert result is expected


def test_move_and_shift_properties_toggle():
    state = InputState()  # defaults are False
    assert not state.move
    assert not state.shift

    # Press right to enable movement
    state.press_right()
    state.shift_key_pressed = True
    assert state.move
    assert state.shift


def test_latest_cmd_default_and_update():
    state = InputState()
    assert state.latest_cmd is None  # default

    state.latest_cmd = "jump"
    assert state.latest_cmd == "jump"


def test_direction_default_and_update():
    state = InputState()
    assert state.direction == 1  # default is right/forward

    state.direction = -1  # left/backward
    assert state.direction == -1

    state.direction = 0  # neutral
    assert state.direction == 0


def test_press_left_sets_direction():
    state = InputState()
    state.press_left()
    assert state.direction == -1
    assert state.move is True


def test_press_right_sets_direction():
    state = InputState()
    state.press_right()
    assert state.direction == 1
    assert state.move is True


def test_release_stops_movement():
    state = InputState()
    state.press_right()
    assert state.move is True

    state.release_right()
    assert state.move is False
    assert state.direction == 1  # Maintains last direction


def test_direction_priority_right_over_left():
    state = InputState()
    state.press_left()
    assert state.direction == -1

    # Press right while left is held - right takes precedence
    state.press_right()
    assert state.direction == 1

    # Release right - should revert to left
    state.release_right()
    assert state.direction == -1
