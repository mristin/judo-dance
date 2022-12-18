"""Practice judo techniques using a dancing pad."""
import argparse
import importlib.resources
import os.path
import pathlib
import random
import sys
import time
from typing import Optional, Set, Final, List

import pygame
from icontract import require

import judodance
import judodance.events
from judodance.common import assert_never

assert judodance.__doc__ == __doc__


class Task:
    """Represent a game task to be accomplished."""

    #: Relative path to the picture representing the task in the package data
    expected_position: Final[pathlib.Path]

    #: Relative path to the audio file announcing the task in the package data
    announcement: Final[pathlib.Path]

    #: Set of buttons which need to be active to accomplish the task.
    #:
    #: Empty means back to the cool down position.
    expected_buttons: Final[Set[judodance.events.Button]]

    #: Relative path to the picture illustrating the task in more abstract terms
    picture: Final[pathlib.Path]

    #: Number of points that accomplishing this task brings
    score_delta: Final[int]

    @require(lambda picture: not picture.is_absolute())
    @require(lambda announcement: not announcement.is_absolute())
    def __init__(
        self,
        expected_position: pathlib.Path,
        announcement: pathlib.Path,
        expected_buttons: Set[judodance.events.Button],
        picture: pathlib.Path,
        score_delta: int,
    ) -> None:
        """Initialize with the given values."""
        self.expected_position = expected_position
        self.announcement = announcement
        self.expected_buttons = expected_buttons
        self.picture = picture
        self.score_delta = score_delta


class TaskDatabase:
    """Organize the task transition."""

    #: The list of tasks excluding the cool down
    tasks: Final[List[Task]]

    #: The "idle" task, *i.e.*, "go back to field 1"
    cool_down: Task

    #: Relative path to the accomplishment sound
    accomplishment: Final[pathlib.Path]

    #: How long to wait to play the reminder after announcing the task
    reminder_slack: Final[float]

    @require(lambda tasks, cool_down: cool_down not in tasks)
    @require(lambda accomplishment: not accomplishment.is_absolute())
    def __init__(
        self, tasks: List[Task], cool_down: Task, accomplishment: pathlib.Path
    ) -> None:
        """Initialize with the given values."""
        self.tasks = tasks
        self.cool_down = cool_down
        self.accomplishment = accomplishment

        self.reminder_slack = 5


# noinspection SpellCheckingInspection
def create_task_database() -> TaskDatabase:
    """Initialize the task database."""
    tai_otoshi_rechts = Task(
        expected_position=pathlib.Path("media/tasks/tai_otoshi_rechts/keypad.png"),
        announcement=pathlib.Path("media/tasks/tai_otoshi_rechts/announcement.ogg"),
        expected_buttons={
            judodance.events.Button.CROSS,
            judodance.events.Button.CIRCLE,
        },
        picture=pathlib.Path("media/tasks/tai_otoshi_rechts/picture.png"),
        score_delta=1,
    )

    tai_otoshi_links = Task(
        expected_position=pathlib.Path("media/tasks/tai_otoshi_links/keypad.png"),
        announcement=pathlib.Path("media/tasks/tai_otoshi_links/announcement.ogg"),
        expected_buttons={
            judodance.events.Button.CROSS,
            judodance.events.Button.CIRCLE,
        },
        picture=pathlib.Path("media/tasks/tai_otoshi_links/picture.png"),
        score_delta=1,
    )

    uki_goshi_rechts = Task(
        expected_position=pathlib.Path("media/tasks/uki_goshi_rechts/keypad.png"),
        announcement=pathlib.Path("media/tasks/uki_goshi_rechts/announcement.ogg"),
        expected_buttons={judodance.events.Button.CROSS, judodance.events.Button.UP},
        picture=pathlib.Path("media/tasks/uki_goshi_rechts/picture.png"),
        score_delta=1,
    )

    uki_goshi_links = Task(
        expected_position=pathlib.Path("media/tasks/uki_goshi_links/keypad.png"),
        announcement=pathlib.Path("media/tasks/uki_goshi_links/announcement.ogg"),
        expected_buttons={judodance.events.Button.UP, judodance.events.Button.CIRCLE},
        picture=pathlib.Path("media/tasks/uki_goshi_links/picture.png"),
        score_delta=1,
    )

    osoto_otoshi_rechts = Task(
        expected_position=pathlib.Path("media/tasks/osoto_otoshi_rechts/keypad.png"),
        announcement=pathlib.Path("media/tasks/osoto_otoshi_rechts/announcement.ogg"),
        expected_buttons={judodance.events.Button.UP, judodance.events.Button.CROSS},
        picture=pathlib.Path("media/tasks/osoto_otoshi_rechts/picture.png"),
        score_delta=1,
    )

    osoto_otoshi_links = Task(
        expected_position=pathlib.Path("media/tasks/osoto_otoshi_links/keypad.png"),
        announcement=pathlib.Path("media/tasks/osoto_otoshi_links/announcement.ogg"),
        expected_buttons={judodance.events.Button.UP, judodance.events.Button.CIRCLE},
        picture=pathlib.Path("media/tasks/osoto_otoshi_links/picture.png"),
        score_delta=1,
    )

    cool_down = Task(
        expected_position=pathlib.Path("media/tasks/cool_down/keypad.png"),
        announcement=pathlib.Path("media/tasks/cool_down/announcement.ogg"),
        expected_buttons=set(),
        picture=pathlib.Path("media/tasks/cool_down/picture.png"),
        score_delta=0,
    )

    return TaskDatabase(
        [
            tai_otoshi_rechts,
            tai_otoshi_links,
            uki_goshi_rechts,
            uki_goshi_links,
            osoto_otoshi_rechts,
            osoto_otoshi_links,
        ],
        cool_down=cool_down,
        accomplishment=pathlib.Path("media/tasks/accomplishment.ogg"),
    )


def check_all_files_exist(task_database: TaskDatabase) -> Optional[str]:
    """Check that all files exist, and return an error, if any."""
    package_dir = importlib.resources.files(__package__)

    pths = [
        str(package_dir.joinpath(str(task_database.accomplishment)))
    ]  # type: List[str]

    for task in task_database.tasks + [task_database.cool_down]:
        pths.append(str(package_dir.joinpath(str(task.announcement))))
        pths.append(str(package_dir.joinpath(str(task.expected_position))))
        pths.append(str(package_dir.joinpath(str(task.picture))))

    for pth in pths:
        if not os.path.exists(pth):
            return f"The media file does not exist: {pth}"

    return None


class State:
    """Capture the global state of the game."""

    #: Set if we received the signal to quit the game
    received_quit: bool

    #: Indicate the current task
    task: Task

    #: Seconds since epoch to be reminded the next time about the task
    next_reminder: Optional[float]

    #: Currently pressed buttons
    active_button_set: Set[judodance.events.Button]

    #: Set if the task has been accomplished
    accomplished: bool

    #: Seconds since epoch when the task will be accomplished and the next task picked
    accomplished_played: Optional[float]

    def __init__(self, initial_task: Task) -> None:
        """Initialize with the default values."""
        self.received_quit = False
        self.task = initial_task
        self.next_reminder = None
        self.active_button_set = set()
        self.accomplished = False
        self.accomplished_played = None

        self.score = 0


@require(lambda path: not path.is_absolute())
def play_sound(path: pathlib.Path) -> float:
    """Start playing the sound and returns its length."""
    sound = pygame.mixer.Sound(
        str(importlib.resources.files(__package__).joinpath(str(path)))
    )
    sound.play()
    return sound.get_length()


def handle(
    state: State,
    our_event_queue: List[judodance.events.EventUnion],
    task_database: TaskDatabase,
) -> None:
    """Consume the first action in the queue."""
    if len(our_event_queue) == 0:
        return

    now = time.time()
    event = our_event_queue.pop(0)

    if isinstance(event, judodance.events.ReceivedQuit):
        state.received_quit = True

    elif isinstance(event, judodance.events.NeedToAnnounce):
        # Announce only the techniques; it's too boring to hear the "cool down" sound
        # all the time
        if state.task is not task_database.cool_down:
            announcement_length = play_sound(state.task.announcement)
            state.next_reminder = (
                now + announcement_length + task_database.reminder_slack
            )
        else:
            state.next_reminder = now + task_database.reminder_slack

    elif isinstance(event, judodance.events.ButtonsChanged):
        state.active_button_set = event.active_button_set.copy()

    elif isinstance(event, judodance.events.Accomplished):
        if state.task is not task_database.cool_down:
            accomplished_sound_length = play_sound(task_database.accomplishment)
            state.accomplished_played = now + accomplished_sound_length
        else:
            our_event_queue.append(judodance.events.TaskDone())

    elif isinstance(event, judodance.events.TaskDone):
        # Pick the next task
        if state.task is task_database.cool_down:
            state.task = random.choice(task_database.tasks)
        else:
            state.score += state.task.score_delta
            state.task = task_database.cool_down

        state.accomplished = False
        state.next_reminder = None
        state.accomplished_played = None

        our_event_queue.append(judodance.events.NeedToAnnounce())

    elif isinstance(event, judodance.events.Tick):
        # Handle the time

        if state.accomplished_played is not None and now >= state.accomplished_played:
            our_event_queue.append(judodance.events.TaskDone())

        elif state.next_reminder is not None and now >= state.next_reminder:
            announcement_length = play_sound(state.task.announcement)
            state.next_reminder = (
                now + announcement_length + +task_database.reminder_slack
            )
        else:
            # No side effect based on time
            pass

        # If the player jumped to the button *before* the announcement, we still
        # want to react to the correct position. That is, we can not react only on
        # change of buttons, but need to constantly check if the task has not been
        # accomplished.
        if (
            state.active_button_set == state.task.expected_buttons
            and not state.accomplished
        ):
            state.accomplished = True
            state.next_reminder = None
            our_event_queue.append(judodance.events.Accomplished())

    else:
        assert_never(event)


@require(lambda percentage: 0 <= percentage <= 1)
def rescale_image_relative_to_surface_width(
    image: pygame.surface.Surface, percentage: float, surface: pygame.surface.Surface
) -> pygame.surface.Surface:
    """Rescale the image as a percentage of the ``surface`` size."""
    surface_width = surface.get_width()

    image_rect = image.get_rect()
    image_width = image_rect.width
    image_height = image_rect.height

    new_image_width = int(surface_width * percentage)
    new_image_height = int(image_height * (new_image_width / image_width))

    return pygame.transform.scale(image, (new_image_width, new_image_height))


@require(lambda percentage: 0 <= percentage <= 1)
def rescale_image_relative_to_surface_height(
    image: pygame.surface.Surface, percentage: float, surface: pygame.surface.Surface
) -> pygame.surface.Surface:
    """Rescale the image as a percentage of the ``surface`` size."""
    surface_width = surface.get_width()

    image_rect = image.get_rect()
    image_width = image_rect.width
    image_height = image_rect.height

    new_image_height = int(surface.get_height() * percentage)
    new_image_width = int(image_width * (new_image_height / image_height))

    return pygame.transform.scale(image, (new_image_width, new_image_height))


def render(state: State, surface: pygame.surface.Surface) -> None:
    """Render the game on the screen."""
    package_dir = importlib.resources.files(__package__)

    surface.fill((0, 0, 0))

    position = pygame.image.load(
        str(package_dir.joinpath(str(state.task.expected_position)))
    )
    position = rescale_image_relative_to_surface_width(position, 0.4, surface)

    surface.blit(position, (10, 10))

    picture = pygame.image.load(str(package_dir.joinpath(str(state.task.picture))))

    if picture.get_height() > picture.get_width():
        picture = rescale_image_relative_to_surface_height(picture, 0.7, surface)
    else:
        picture = rescale_image_relative_to_surface_width(picture, 0.4, surface)

    surface.blit(picture, (position.get_width() + 60, 10))

    # noinspection SpellCheckingInspection
    font_large = pygame.font.Font("freesansbold.ttf", 64)
    score = font_large.render(f"Score: {state.score}", True, (255, 255, 255))
    surface.blit(score, (position.get_width() + 60, picture.get_height() + 60))

    # noinspection SpellCheckingInspection
    font_small = pygame.font.Font("freesansbold.ttf", 32)
    escape = font_small.render('Press ESC or "q" to quit', True, (255, 255, 255))
    surface.blit(
        escape,
        (10, surface.get_height() - escape.get_height() - 20),
    )

    pygame.display.flip()


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument(
        "--version", help="show the current version and exit", action="store_true"
    )

    parser.add_argument(
        "--list_joysticks", help="List joystick GUIDs and exit", action="store_true"
    )
    if len(joysticks) >= 1:
        parser.add_argument(
            "--joystick",
            help="Joystick to use for the game",
            choices=[joystick.get_guid() for joystick in joysticks],
            default=joysticks[0].get_guid(),
        )

    # NOTE (mristin, 2022-12-16):
    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(judodance.__version__)
        return 0

    if "--list_joysticks" in sys.argv and "--help" not in sys.argv:
        for joystick in joysticks:
            print(f"Joystick {joystick.get_name()}, GUID: {joystick.get_guid()}")
        return 0

    args = parser.parse_args()

    active_joystick = None  # type: Optional[pygame.joystick.Joystick]
    if len(joysticks) == 0:
        print(
            "There are no joysticks plugged in. Judo-dance requires a joystick.",
            file=sys.stderr,
        )
        return 1

    else:
        active_joystick = next(
            joystick for joystick in joysticks if joystick.get_guid() == args.joystick
        )

    assert active_joystick is not None
    print(
        f"Using the joystick: {active_joystick.get_name()} {active_joystick.get_guid()}"
    )

    # NOTE (mristin, 2022-12-16):
    # We have to think a bit better about how to deal with keyboard and joystick input.
    # For rapid development, we simply map the buttons of our concrete dance mat to
    # button numbers.
    button_map = {
        6: judodance.events.Button.CROSS,
        2: judodance.events.Button.UP,
        7: judodance.events.Button.CIRCLE,
        3: judodance.events.Button.RIGHT,
        5: judodance.events.Button.SQUARE,
        1: judodance.events.Button.DOWN,
        4: judodance.events.Button.TRIANGLE,
        0: judodance.events.Button.LEFT,
    }

    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.init()

    pygame.display.set_caption("Judo Dance")
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    task_database = create_task_database()
    error = check_all_files_exist(task_database)
    if error is not None:
        print(error, file=sys.stderr)
        return 1

    state = State(initial_task=random.choice(task_database.tasks))

    our_event_queue = [
        judodance.events.NeedToAnnounce()
    ]  # type: List[judodance.events.EventUnion]

    try:
        while not state.received_quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    our_event_queue.append(judodance.events.ReceivedQuit())

                elif (
                    event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP)
                    and joysticks[event.instance_id] is active_joystick
                ):
                    # List all the active buttons on this event
                    active_button_set = set()  # type: Set[judodance.events.Button]
                    for button_index in range(active_joystick.get_numbuttons()):
                        button_active = active_joystick.get_button(button_index) > 0

                        if button_active:
                            button_in_action = button_map.get(button_index, None)
                            if button_in_action is not None:
                                active_button_set.add(button_in_action)
                            else:
                                # Ignore unmapped buttons
                                pass

                    our_event_queue.append(
                        judodance.events.ButtonsChanged(active_button_set)
                    )

                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_q,
                ):
                    our_event_queue.append(judodance.events.ReceivedQuit())

                else:
                    # Ignore the event that we do not handle
                    pass

            our_event_queue.append(judodance.events.Tick())

            while len(our_event_queue) > 0:
                handle(state, our_event_queue, task_database)

            render(state, surface)
    finally:
        pygame.joystick.quit()
        pygame.quit()

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="judo-dance")


if __name__ == "__main__":
    sys.exit(main(prog="judo-dance"))
