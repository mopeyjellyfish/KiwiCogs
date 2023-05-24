import asyncio

from pytest import fixture, raises

from kiwi_cogs import Machine, UnknownAction, UnknownGuard, UnknownTarget


@fixture
def traffic_light_config() -> dict:
    return {
        "name": "lights",
        "initial": "green",
        "states": {
            "green": {
                "events": {"NEXT": {"target": "yellow"}},
            },
            "yellow": {"events": {"NEXT": {"target": "red"}}},
            "red": {"events": {"NEXT": {"target": "green"}}},
        },
    }


async def entered(_):
    print("entered state!")


async def log(_):
    print("LOG!")


def exited(_):
    print("exited!")


def is_adult(context, _):
    age = context.get("age")
    return age is not None and age >= 18


def is_child(context, _):
    age = context.get("age")
    return age is not None and age < 18


def log_age(context):
    age = context.get("age")
    print(f"User is {age} old!")


def age_determined(context):
    age = context.get("age")
    print(f"Users age has been determined as: {age}")


@fixture
def transient_config() -> dict:
    return {
        "name": "age",
        "context": {"age": None},  # age unknown
        "initial": "unknown",
        "states": {
            "unknown": {
                "transitions": [
                    {"target": "adult", "cond": is_adult},
                    {"target": "child", "cond": is_child},
                ],
                "entry": [log, entered],
                "exit": age_determined,
            },
            "adult": {"type": "final", "entry": log_age},
            "child": {"type": "final", "entry": log_age},
        },
    }


@fixture
def bad_transient_config() -> dict:
    return {
        "name": "age",
        "initial": "unknown",
        "states": {
            "unknown": {
                "events": {"GO": {"target": "go"}},
                "entry": entered,
                "exit": [log, exited],
            },
            "go": {"transitions": {"target": "bad"}},
            "good": {"type": "final"},
        },
    }


@fixture
def bad_action_config() -> dict:
    return {
        "name": "game",
        "initial": "playing",
        "context": {"points": 0},
        "states": {
            "playing": {
                # Event less transition
                # Will transition to either 'win' or 'lose' immediately upon
                # entering 'playing' state or receiving AWARD_POINTS event
                # if the condition is met.
                "transitions": [
                    {"target": "win", "cond": "didPlayerWin"},
                    {"target": "lose", "cond": "didPlayerLose"},
                ],
                "events": {
                    # Self transition
                    "AWARD_POINTS": {"actions": [do_something_else, "BadAction"]}
                },
            },
            "win": {"type": "final"},
            "lose": {"type": "final"},
        },
        "guards": {"didPlayerWin": has_player_won, "didPlayerLose": has_player_lost},
        "actions": {"addPoints": award_points},
    }


@fixture
def bad_guard_config() -> dict:
    return {
        "name": "game",
        "initial": "playing",
        "context": {"points": 0},
        "states": {
            "playing": {
                # Event less transition
                # Will transition to either 'win' or 'lose' immediately upon
                # entering 'playing' state or receiving AWARD_POINTS event
                # if the condition is met.
                "transitions": [
                    {"target": "win", "cond": "unknownCond"},
                    {"target": "lose", "cond": "unknownCond"},
                ],
                "events": {
                    # Self transition
                    "AWARD_POINTS": {"actions": [do_something_else, "addPoints"]}
                },
            },
            "win": {"type": "final"},
            "lose": {"type": "final"},
        },
        "guards": {"didPlayerWin": has_player_won, "didPlayerLose": has_player_lost},
        "actions": {"addPoints": award_points},
    }


def has_player_won(context, _):
    return context["points"] > 99


def has_player_lost(context, _):
    return context["points"] < 0


def award_points(context, _):
    context["points"] = 100


async def do_something_else(context, _):
    await asyncio.sleep(0)


@fixture
def simple_game_config() -> dict:
    return {
        "name": "game",
        "initial": "playing",
        "context": {"points": 0},
        "states": {
            "playing": {
                # Event less transition
                # Will transition to either 'win' or 'lose' immediately upon
                # entering 'playing' state or receiving AWARD_POINTS event
                # if the condition is met.
                "transitions": [
                    {"target": "win", "cond": "didPlayerWin"},
                    {"target": "lose", "cond": "didPlayerLose"},
                ],
                "events": {
                    # Self transition
                    "AWARD_POINTS": {"actions": "addPoints"}
                },
            },
            "win": {"type": "final"},
            "lose": {"type": "final"},
        },
        "guards": {"didPlayerWin": has_player_won, "didPlayerLose": has_player_lost},
        "actions": {"addPoints": award_points},
    }


@fixture
async def traffic_light(traffic_light_config) -> Machine:
    return await Machine.create(traffic_light_config)


@fixture
async def age_machine(transient_config) -> Machine:
    return await Machine.create(transient_config)


@fixture
async def game_machine(simple_game_config) -> Machine:
    return await Machine.create(simple_game_config)


@fixture
async def bad_transient_machine(bad_transient_config) -> Machine:
    return await Machine.create(bad_transient_config)


def test_machine_configuration(traffic_light: Machine):
    assert traffic_light.name == "lights"
    assert traffic_light.initial == "green"
    assert traffic_light.states


async def test_machine(traffic_light: Machine):
    assert traffic_light.initial_state.value == "green"

    yellow_state = await traffic_light.event("NEXT")

    assert yellow_state.value == "yellow"

    red_state = await traffic_light.event("NEXT")

    assert red_state.value == "red"

    green_state = await traffic_light.event("NEXT")

    assert green_state.value == "green"


def test_machine_initial_state(traffic_light: Machine):
    assert traffic_light.initial_state.value == "green"


async def test_transient_machine_adult(age_machine: Machine):
    assert age_machine.state.value == "unknown"
    context = {"age": 18}
    await age_machine.with_context(context=context)
    assert age_machine.state.value == "adult"


async def test_transient_machine_child(age_machine: Machine):
    assert age_machine.state.value == "unknown"
    context = {"age": 10}
    await age_machine.with_context(context=context)
    assert age_machine.state.value == "child"


async def test_game_machine(game_machine: Machine):
    assert game_machine.initial_state.value == "playing"
    await game_machine.event("AWARD_POINTS")
    assert game_machine.state.value == "win"


async def test_bad_transient_transitions(bad_transient_machine):
    with raises(UnknownTarget):
        await bad_transient_machine.event("GO")


@fixture
def multi_transition_event() -> dict:
    return {
        "name": "game",
        "initial": "playing",
        "context": {"points": 0},
        "states": {
            "playing": {
                "events": {
                    # Self transition
                    "AWARD_POINTS": {"actions": award_points},
                    # Transitions to one of the following
                    "DECLARE_WIN": [
                        {"target": "win", "cond": has_player_won},
                        {"target": "lose", "cond": has_player_lost},
                    ],
                }
            },
            "win": {},
            "lose": {},
        },
        "guards": {"didPlayerWin": has_player_won, "didPlayerLose": has_player_lost},
        "actions": {"addPoints": award_points},
    }


@fixture
async def multi_transition_event_machine(multi_transition_event) -> Machine:
    return await Machine.create(multi_transition_event)


async def test_event_multi_transition_events(multi_transition_event_machine: Machine):
    assert multi_transition_event_machine.initial_state.value == "playing"
    await multi_transition_event_machine.event("AWARD_POINTS")
    assert multi_transition_event_machine.state.value == "playing"
    assert multi_transition_event_machine.state.type == "atomic"
    await multi_transition_event_machine.event("DECLARE_WIN")
    assert multi_transition_event_machine.state.value == "win"
    assert multi_transition_event_machine.state.type == "final"
    await multi_transition_event_machine.event("UNKNOWN_EVENT")
    assert multi_transition_event_machine.state.value == "win"
    assert multi_transition_event_machine.state.type == "final"


async def test_bad_action_config(bad_action_config):
    with raises(UnknownAction):
        await Machine.create(bad_action_config)


async def test_bad_cond_config(bad_guard_config):
    with raises(UnknownGuard):
        await Machine.create(bad_guard_config)
