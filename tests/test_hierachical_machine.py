from pytest import fixture

from kiwi_cogs import Machine


def is_walking(context, _):
    return context["speed"] <= 11


def is_running(context, _):
    return context["speed"] > 11


@fixture
def walk_states():
    return {
        "initial": "start",
        "states": {
            "start": {
                "transitions": [
                    {"target": "walking", "cond": is_walking},
                    {"target": "running", "cond": is_running},
                ],
            },
            "walking": {"events": {"CROSSED": {"target": "crossed"}}},
            "running": {"events": {"CROSSED": {"target": "crossed"}}},
            "crossed": {},
        },
    }


@fixture
def pedestrian_states(walk_states):
    return {
        "initial": "walk",
        "states": {
            "walk": {"events": {"PED_COUNTDOWN": {"target": "wait"}}, **walk_states},
            "wait": {"events": {"PED_COUNTDOWN": {"target": "stop"}}},
            "stop": {},
            "blinking": {},
        },
    }


@fixture
def crossing_config(pedestrian_states):
    return {
        "name": "light",
        "initial": "green",
        "context": {"speed": 10},
        "states": {
            "green": {"events": {"TIMER": {"target": "yellow"}}},
            "yellow": {"events": {"TIMER": {"target": "red"}}},
            "red": {"events": {"TIMER": {"target": "green"}}, **pedestrian_states},
        },
        "events": {
            "POWER_OUTAGE": {"target": ".red.blinking"},
            "POWER_RESTORED": {"target": ".red"},
            "POWER_CROSSED": {"target": ".red.walk.crossed"},
        },
    }


@fixture
async def crossing(crossing_config: dict) -> Machine:
    return await Machine.create(crossing_config)


async def test_crossing(crossing: Machine):
    assert crossing.initial_state.value == "green"
    assert crossing.state.type == "atomic"
    await crossing.event("TIMER")
    assert crossing.state.value == "yellow"
    assert crossing.state.type == "atomic"
    await crossing.event("TIMER")
    assert crossing.state.value == {"red": {"walk": "walking"}}
    await crossing.event("CROSSED")
    assert crossing.state.value == {"red": {"walk": "crossed"}}
    assert crossing.state.type == "compound"
    await crossing.event("PED_COUNTDOWN")
    assert crossing.state.value == {"red": "wait"}
    await crossing.event("PED_COUNTDOWN")
    assert crossing.state.value == {"red": "stop"}
    await crossing.event("TIMER")
    assert crossing.initial_state.value == "green"
    assert crossing.state.type == "atomic"
    await crossing.event("POWER_OUTAGE")
    assert crossing.state.value == {"red": "blinking"}
    await crossing.event("POWER_RESTORED")
    assert crossing.state.value == {"red": {"walk": "walking"}}
    await crossing.event("POWER_CROSSED")
    assert crossing.state.value == {"red": {"walk": "crossed"}}
