"""Define the actions."""
import abc
import enum
from typing import Set, Union

from icontract import DBC


class Action(DBC):
    """Represent an abstract action in the game."""

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Tick(Action):
    """Mark a tick in the (irregular) game clock."""

    def __str__(self) -> str:
        return self.__class__.__name__


class Quit(Action):
    """Exit the game."""

    def __str__(self) -> str:
        return self.__class__.__name__


class Button(enum.Enum):
    """Represent abstract buttons, not necessarily tied to a concrete joystick."""

    CROSS = 0
    UP = 1
    CIRCLE = 2
    RIGHT = 3
    SQUARE = 4
    DOWN = 5
    TRIANGLE = 6
    LEFT = 7


class Pressed(Action):
    """Capture the change in active (pressed) buttons."""

    def __init__(self, active_button_set: Set[Button]) -> None:
        """Initialize with the given values."""
        self.active_button_set = active_button_set

    def __str__(self) -> str:
        buttons_joined = ", ".join(button.name for button in self.active_button_set)
        return f"{self.__class__.__name__}({buttons_joined})"


ActionUnion = Union[Tick, Quit, Pressed]
