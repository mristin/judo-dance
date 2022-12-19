"""Define the actions."""
import abc
import enum
from typing import Set, Union

from icontract import DBC


class Event(DBC):
    """Represent an abstract event in the game."""

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Tick(Event):
    """Mark a tick in the (irregular) game clock."""

    def __str__(self) -> str:
        return self.__class__.__name__


class ReceivedQuit(Event):
    """Signal that we have to exit the game."""

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


class ButtonsChanged(Event):
    """Capture the change in active (pressed) buttons."""

    def __init__(self, active_button_set: Set[Button]) -> None:
        """Initialize with the given values."""
        self.active_button_set = active_button_set

    def __str__(self) -> str:
        buttons_joined = ", ".join(button.name for button in self.active_button_set)
        return f"{self.__class__.__name__}({buttons_joined})"


class Accomplished(Event):
    """Signal that the task has been accomplished."""

    def __str__(self) -> str:
        return self.__class__.__name__


class TaskDone(Event):
    """Signal that the task has been completely completed including all the effects."""

    def __str__(self) -> str:
        return self.__class__.__name__


class NeedToAnnounce(Event):
    """Signal that we need to announce the task."""

    def __str__(self) -> str:
        return self.__class__.__name__


class GameOver(Event):
    """Signal that the time is up."""

    def __str__(self) -> str:
        return self.__class__.__name__


EventUnion = Union[
    Tick, ReceivedQuit, ButtonsChanged, Accomplished, TaskDone, NeedToAnnounce, GameOver
]
