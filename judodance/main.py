"""Practice judo techniques using a dancing pad."""
import argparse
import importlib.resources
import os.path
import pathlib
import random
import sys
import time
from typing import Optional, Set, Final, List, MutableMapping, Union

import pygame
from icontract import require, invariant

import judodance
import judodance.events
from judodance.common import assert_never

assert judodance.__doc__ == __doc__

PACKAGE_DIR = (
    pathlib.Path(str(importlib.resources.files(__package__)))
    if __package__ is not None
    else pathlib.Path(os.path.realpath(__file__)).parent
)


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
    pths = [PACKAGE_DIR / task_database.accomplishment]  # type: List[pathlib.Path]

    for task in task_database.tasks + [task_database.cool_down]:
        pths.append(PACKAGE_DIR / task.announcement)
        pths.append(PACKAGE_DIR / task.expected_position)
        pths.append(PACKAGE_DIR / task.picture)

    for pth in pths:
        if not pth.exists():
            return f"The media file does not exist: {pth}"

    return None


@invariant(lambda self: 0 <= self.game_time <= self.game_end - self.game_start)
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

    #: Timestamp when the game started, seconds since epoch
    game_start: Final[float]

    #: Seconds since the game start
    game_time: float

    #: Timestamp when the game is to end, seconds since epoch
    game_end: Final[float]

    #: Set when the time is up
    game_over: bool

    @require(lambda game_start, game_end: game_start <= game_end)
    def __init__(self, initial_task: Task, game_start: float, game_end: float) -> None:
        """Initialize with the given values and the defaults."""
        self.received_quit = False
        self.task = initial_task
        self.next_reminder = None
        self.active_button_set = set()
        self.accomplished = False
        self.accomplished_played = None

        self.score = 0

        self.game_start = game_start
        self.game_time = 0
        self.game_end = game_end
        self.game_over = False


@require(lambda path: not path.is_absolute())
def play_sound(path: pathlib.Path) -> float:
    """Start playing the sound and returns its length."""
    sound = pygame.mixer.Sound(str(PACKAGE_DIR / path))
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

    elif isinstance(event, judodance.events.GameOver):
        state.game_over = True

    elif isinstance(event, judodance.events.Tick):
        # Handle the time

        if now > state.game_end:
            our_event_queue.append(judodance.events.GameOver())
        else:
            state.game_time = now - state.game_start

            if (
                state.accomplished_played is not None
                and now >= state.accomplished_played
            ):
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
    image_rect = image.get_rect()
    image_width = image_rect.width
    image_height = image_rect.height

    new_image_width = int(surface.get_width() * percentage)
    new_image_height = int(image_height * (new_image_width / image_width))

    return pygame.transform.scale(image, (new_image_width, new_image_height))


@require(lambda percentage: 0 <= percentage <= 1)
def rescale_image_relative_to_surface_height(
    image: pygame.surface.Surface, percentage: float, surface: pygame.surface.Surface
) -> pygame.surface.Surface:
    """Rescale the image as a percentage of the ``surface`` size."""
    image_rect = image.get_rect()
    image_width = image_rect.width
    image_height = image_rect.height

    new_image_height = int(surface.get_height() * percentage)
    new_image_width = int(image_width * (new_image_height / image_height))

    return pygame.transform.scale(image, (new_image_width, new_image_height))


def render_game_over(state: State, surface: pygame.surface.Surface) -> None:
    """Render the "game over" dialogue."""
    oneph = max(1, int(0.01 * surface.get_height()))
    onepw = max(1, int(0.01 * surface.get_height()))

    surface.fill((0, 0, 0))

    font_large = pygame.font.Font(PACKAGE_DIR / "media/freesansbold.ttf", 5 * oneph)
    game_over = font_large.render("Game Over", True, (255, 255, 255))
    game_over_xy = (
        int(surface.get_width() / 2) - int(game_over.get_width() / 2),
        int(surface.get_height() / 2) - int(game_over.get_height() / 2),
    )

    surface.blit(game_over, game_over_xy)

    score = font_large.render(f"Score: {state.score}", True, (255, 255, 255))
    score_xy = (
        int(surface.get_width() / 2) - int(score.get_width() / 2),
        game_over_xy[1] + game_over.get_height() + oneph,
    )
    surface.blit(score, score_xy)

    if state.score < 20:
        medal_pth = "media/medals/bronze.png"
    elif state.score < 30:
        medal_pth = "media/medals/silver.png"
    else:
        medal_pth = "media/medals/gold.png"

    medal = load_image_or_retrieve_from_cache(medal_pth)
    medal_xy = (
        int(surface.get_width() / 2) - int(medal.get_width() / 2),
        score_xy[1] + score.get_height() + oneph,
    )
    surface.blit(medal, medal_xy)

    font_small = pygame.font.Font(PACKAGE_DIR / "media/freesansbold.ttf", 2 * oneph)
    escape = font_small.render('Press ESC or "q" to quit', True, (255, 255, 255))
    surface.blit(
        escape,
        (onepw, surface.get_height() - escape.get_height() - 2 * oneph),
    )


def render_game(state: State, surface: pygame.surface.Surface) -> None:
    """Render the game on the screen."""
    surface.fill((0, 0, 0))

    oneph = max(1, int(0.01 * surface.get_height()))
    onepw = max(1, int(0.01 * surface.get_height()))

    position = load_image_or_retrieve_from_cache(state.task.expected_position)

    position = rescale_image_relative_to_surface_width(position, 0.4, surface)

    surface.blit(position, (onepw, oneph))

    picture = load_image_or_retrieve_from_cache(state.task.picture)

    if picture.get_height() > picture.get_width():
        picture = rescale_image_relative_to_surface_height(picture, 0.7, surface)
    else:
        picture = rescale_image_relative_to_surface_width(picture, 0.4, surface)

    picture_xy = (position.get_width() + 3 * onepw, oneph)
    surface.blit(picture, picture_xy)

    font_large = pygame.font.Font(PACKAGE_DIR / "media/freesansbold.ttf", 5 * oneph)
    score = font_large.render(f"Score: {state.score}", True, (255, 255, 255))
    score_xy = (position.get_width() + 3 * onepw, picture.get_height() + 3 * oneph)
    surface.blit(score, score_xy)

    game_time_fraction = state.game_time / (state.game_end - state.game_start)
    if game_time_fraction < 1 / 5:
        hourglass_pth = "media/hourglass/frame_01.png"
    elif game_time_fraction < 2 / 5:
        hourglass_pth = "media/hourglass/frame_02.png"
    elif game_time_fraction < 3 / 5:
        hourglass_pth = "media/hourglass/frame_03.png"
    elif game_time_fraction < 4 / 5:
        hourglass_pth = "media/hourglass/frame_04.png"
    else:
        hourglass_pth = "media/hourglass/frame_05.png"

    hourglass = load_image_or_retrieve_from_cache(hourglass_pth)
    hourglass = rescale_image_relative_to_surface_width(hourglass, 0.3, surface)

    hourglass_xy = (picture_xy[0] + picture.get_width() + onepw, picture_xy[1])
    surface.blit(hourglass, hourglass_xy)

    font_small = pygame.font.Font(PACKAGE_DIR / "media/freesansbold.ttf", 2 * oneph)
    escape = font_small.render('Press ESC or "q" to quit', True, (255, 255, 255))
    surface.blit(
        escape,
        (onepw, surface.get_height() - escape.get_height() - 2 * oneph),
    )


IMAGE_CACHE = dict()  # type: MutableMapping[str, pygame.surface.Surface]


@require(lambda path: not os.path.isabs(str(path)))
def load_image_or_retrieve_from_cache(
    path: Union[str, os.PathLike[str]]
) -> pygame.surface.Surface:
    """Load the image or retrieve it from the memory cache."""
    image = IMAGE_CACHE.get(str(path), None)
    if image is not None:
        return image

    image = pygame.image.load(str(PACKAGE_DIR / path))
    IMAGE_CACHE[str(path)] = image
    return image


def render(state: State, surface: pygame.surface.Surface) -> None:
    """Render the state on the screen."""
    if state.game_over:
        render_game_over(state, surface)
    else:
        render_game(state, surface)


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

    # noinspection PyUnusedLocal
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

    now = time.time()

    game_duration = 120  # in seconds

    state = State(
        initial_task=random.choice(task_database.tasks),
        game_start=now,
        game_end=now + game_duration,
    )

    our_event_queue = [
        judodance.events.NeedToAnnounce()
    ]  # type: List[judodance.events.EventUnion]

    # Reuse the tick object so that we don't have to create it every time
    tick_event = judodance.events.Tick()

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

            our_event_queue.append(tick_event)

            while len(our_event_queue) > 0:
                handle(state, our_event_queue, task_database)

            render(state, surface)
            pygame.display.flip()
    finally:
        pygame.joystick.quit()
        pygame.quit()

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="judo-dance")


if __name__ == "__main__":
    sys.exit(main(prog="judo-dance"))
