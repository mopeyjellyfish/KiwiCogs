import asyncio

from pytest import fixture

from kiwi_cogs import Machine


async def has_player_won(context, _):
    await asyncio.sleep(0)
    return context["points"] > 99


async def has_player_lost(context, _):
    await asyncio.sleep(0)
    return context["points"] < 0


async def award_points(context, _):
    await asyncio.sleep(0)
    context["points"] = 100


@fixture
def game_config() -> dict:
    return {
        "name": "game",
        "initial": "playing",
        "context": {"points": 0},
        "states": {
            "playing": {
                # // Eventless transition
                # // Will transition to either 'win' or 'lose' immediately upon
                # // entering 'playing' state or receiving AWARD_POINTS event
                # // if the condition is met.
                "transitions": [
                    {"target": "win", "cond": has_player_won},
                    {"target": "lose", "cond": has_player_lost},
                ],
                "events": {
                    # Self transition
                    "AWARD_POINTS": {"actions": award_points}
                },
            },
            "win": {"type": "final"},
            "lose": {"type": "final"},
        },
        "guards": {"didPlayerWin": has_player_won, "didPlayerLose": has_player_lost},
        "actions": {"addPoints": award_points},
    }


@fixture
async def async_game_machine(game_config) -> Machine:
    return await Machine.create(game_config)


async def test_async_machine(async_game_machine: Machine):
    assert async_game_machine.initial_state.value == "playing"
    await async_game_machine.event("AWARD_POINTS")
    assert async_game_machine.state.value == "win"
