from pytest import fixture

from kiwi_cogs import Machine


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


@fixture
def tennis_config():
    return {
        "name": "tennis_game",
        "initial": "serving",
        "context": {"player1_score": 0, "player2_score": 0},
        "states": {
            "serving": {
                "transitions": [
                    {"target": "deuce", "cond": check_if_score_is_deuce},
                    {"target": "advantage", "cond": check_if_score_is_advantage},
                    {"target": "game", "cond": check_if_score_is_game},
                ],
                "events": {
                    "PLAYER1_SCORES": {"actions": increment_player1_score},
                    "PLAYER2_SCORES": {"actions": increment_player2_score},
                },
            },
            "deuce": {
                "transitions": [
                    {"target": "advantage", "cond": check_if_score_is_advantage},
                    {"target": "game", "cond": check_if_score_is_game},
                ],
                "events": {
                    "PLAYER1_SCORES": {"actions": increment_player1_score},
                    "PLAYER2_SCORES": {"actions": increment_player2_score},
                },
            },
            "advantage": {
                "transitions": [
                    {"target": "deuce", "cond": check_if_score_is_deuce},
                    {"target": "game", "cond": check_if_score_is_game},
                ],
                "events": {
                    "PLAYER1_SCORES": {"actions": increment_player1_score},
                    "PLAYER2_SCORES": {"actions": increment_player2_score},
                },
            },
            "game": {"type": "final"},
        },
        "guards": {
            "isDeuce": check_if_score_is_deuce,
            "isAdvantage": check_if_score_is_advantage,
            "isGame": check_if_score_is_game,
        },
        "actions": {
            "incPlayer1Score": increment_player1_score,
            "incPlayer2Score": increment_player2_score,
        },
    }


@fixture
async def tennis_machine(tennis_config):
    return await Machine.create(tennis_config)


async def test_tennis_deuce(tennis_machine):
    assert tennis_machine.initial_state.value == "serving"
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    assert tennis_machine.state.value == "deuce"


async def test_tennis_adv(tennis_machine):
    assert tennis_machine.initial_state.value == "serving"
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    assert tennis_machine.state.value == "advantage"


async def test_tennis_game(tennis_machine):
    assert tennis_machine.initial_state.value == "serving"
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER2_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    await tennis_machine.event("PLAYER1_SCORES")
    assert tennis_machine.state.value == "game"
