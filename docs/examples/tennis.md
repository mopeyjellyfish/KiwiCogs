# Tennis Game

## Description

This is a simple tennis game. The game is played by two players. Each player has a score of 0 at the beginning of the game. The first player to score 4 points wins the game.

## States

- `serving`: Normal play
- `deuce`: When both players have a score of 3
- `advantage`: When one player has a score of 4 and the other has a score of 3

```python
import asyncio
import curses
import random

from kiwi_cogs import Machine, StateType


def check_if_score_is_deuce(context, _):
    """Checks if the score is deuce in a tennis game

    :param context: The current context of the game, including the scores of both players
    :type context: dict

    :returns: True if the score is deuce, False otherwise
    :rtype: bool
    """
    return context["player1_score"] >= 3 and context["player2_score"] == context["player1_score"]


def check_if_score_is_advantage(context, _):
    """Checks if the score is advantage for one of the players in a tennis game

    :param context: The current context of the game, including the scores of both players
    :type context: dict

    :returns: True if the score is advantage for one player, False otherwise
    :rtype: bool
    """
    if context["player1_score"] > context["player2_score"]:
        return context["player1_score"] >= 4 and context["player1_score"] - context["player2_score"] == 1
    else:
        return context["player2_score"] >= 4 and context["player2_score"] - context["player1_score"] == 1


def check_if_score_is_game(context, _):
    """Checks if the score is a game for one of the players in a tennis game

    :param context: The current context of the game, including the scores of both players
    :type context: dict

    :returns: True if the score is a game for one player, False otherwise
    :rtype: bool
    """
    if context["player1_score"] > context["player2_score"]:
        return context["player1_score"] >= 4 and context["player1_score"] - context["player2_score"] >= 2
    else:
        return context["player2_score"] >= 4 and context["player2_score"] - context["player1_score"] >= 2


def increment_player1_score(context, _):
    context["player1_score"] += 1


def increment_player2_score(context, _):
    context["player2_score"] += 1


config = {
    "name": "tennis_game",
    "initial": "serving",
    "context": {"player1_score": 0, "player2_score": 0},
    "states": {
        "serving": {
            "transitions": [
                {"target": "deuce", "cond": "isDeuce"},  # use a named guard for transitions
                {"target": "advantage", "cond": "isAdvantage"},
                {"target": "game", "cond": "isGame"},
            ],
            "events": {
                "PLAYER1_SCORES": {"actions": "incPlayer1Score"},  # use a named action for events
                "PLAYER2_SCORES": {"actions": "incPlayer2Score"},
            },
        },
        "deuce": {
            "transitions": [
                {"target": "advantage", "cond": "isAdvantage"},
                {"target": "game", "cond": "isGame"},
            ],
            "events": {
                "PLAYER1_SCORES": {"actions": increment_player1_score},  # use a function for events as well!
                "PLAYER2_SCORES": {"actions": increment_player2_score},
            },
        },
        "advantage": {
            "transitions": [
                {"target": "deuce", "cond": check_if_score_is_deuce},  # Functions can be used as well
                {"target": "game", "cond": check_if_score_is_game},
            ],
            "events": {
                "PLAYER1_SCORES": {"actions": increment_player1_score},
                "PLAYER2_SCORES": {"actions": increment_player2_score},
            },
        },
        "game": {
            "transitions": [
                {
                    "target": "player1_wins",
                    "cond": lambda context, _: context["player1_score"] > context["player2_score"],
                },  # any callable can be used as a condition
                {
                    "target": "player2_wins",
                    "cond": lambda context, _: context["player2_score"] > context["player1_score"],
                },
            ],
        },
        "player1_wins": {"type": "final"},  # final states are used to indicate that the machine is finished
        "player2_wins": {"type": "final"},
    },
    "guards": {  # Register the guards, reusable conditions that can be used in transitions
        "isDeuce": check_if_score_is_deuce,
        "isAdvantage": check_if_score_is_advantage,
        "isGame": check_if_score_is_game,
    },
    "actions": {
        "incPlayer1Score": increment_player1_score,
        "incPlayer2Score": increment_player2_score,
    },
}


async def get_machine():
    return await Machine.create(config)


def print_score(stdscr, state, score1, score2):
    stdscr.clear()

    # Create a new window for the scores, with a border
    score_window = curses.newwin(5, 30, 3, 0)
    score_window.box()

    # Print scores
    score_window.addstr(1, 1, f"State: {state}")
    score_window.addstr(2, 1, f"Player 1: {score1}")
    score_window.addstr(3, 1, f"Player 2: {score2}")

    score_window.refresh()


async def tennis_game(stdscr):
    machine = await get_machine()

    events = ("PLAYER1_SCORES", "PLAYER2_SCORES")
    while machine.state.type != StateType.final:
        score_1 = machine.context["player1_score"]
        score_2 = machine.context["player2_score"]
        state = machine.state.value
        print_score(stdscr, state, score_1, score_2)
        event = random.choice(events)  # randomly select a player to score
        await asyncio.sleep(0.2)
        await machine.event(event)

    score_1 = machine.context["player1_score"]
    score_2 = machine.context["player2_score"]
    state = machine.state.value
    print_score(stdscr, state, score_1, score_2)
    await asyncio.sleep(3)


def run(stdscr):
    asyncio.run(tennis_game(stdscr))


if __name__ == "__main__":
    # Initialize curses
    curses.wrapper(run)
```

Example output:

```bash
┌────────────────────────────┐
│State: player2_wins         │
│Player 1: 3                 │
│Player 2: 5                 │
└────────────────────────────┘
```
