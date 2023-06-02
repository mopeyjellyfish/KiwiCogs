# kiwi-cogs

[![Release](https://img.shields.io/github/v/release/mopeyjellyfish/KiwiCogs)](https://img.shields.io/github/v/release/mopeyjellyfish/KiwiCogs)
[![Build](https://github.com/mopeyjellyfish/KiwiCogs/actions/workflows/main.yml/badge.svg)](https://github.com/mopeyjellyfish/KiwiCogs/actions/workflows/main.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/kiwi-cogs.svg)](https://pypi.org/project/kiwi-cogs)
[![codecov](https://codecov.io/gh/mopeyjellyfish/KiwiCogs/branch/main/graph/badge.svg)](https://codecov.io/gh/mopeyjellyfish/KiwiCogs)

A simple and easy to use state machine library

- **Github repository**: <https://github.com/mopeyjellyfish/KiwiCogs/>
- **Documentation** <https://mopeyjellyfish.github.io/KiwiCogs/>

## Installation

### Pip

```bash
pip install -U kiwi-cogs
```

### Poetry

```bash
poetry add kiwi-cogs
```

## Quick start

### Events

Events can be used to transition between states, they can be used to trigger actions or to change the state of the machine. These events can be triggered externally from the machine when something happens.

```python
from kiwi_cogs import Machine

light_config = {
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

light_machine await Machine.create(light_config)
assert traffic_light.initial_state.value == "green"
yellow_state = await traffic_light.event("NEXT")
assert yellow_state.value == "yellow"
red_state = await traffic_light.event("NEXT")
assert red_state.value == "red"
green_state = await traffic_light.event("NEXT")
assert green_state.value == "green"
```

### Transitions

Example of how to transition between states based on conditions in the state, here is how to determine if a user is an adult or a child based on their age using some external context which changes independently of the state machine:

```python
from kiwi_cogs import Machine

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


age_config = {
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


age_machine await Machine.create(age_config)
assert age_machine.state.value == "unknown"
context = {"age": 18}
await age_machine.with_context(context=context)
assert age_machine.state.value == "adult"
```

### Hierarchical machine

Example of how to create a hierarchical state machine, this is useful for creating a state machine which has multiple sub-machines which can be used to model complex behaviour. Often times there are multiple steps within a given parent state, for example when modelling a crossing for pedestrians.

```python
from kiwi_cogs import Machine

def is_walking(context, _):
    return context["speed"] <= 11


def is_running(context, _):
    return context["speed"] > 11


walk_states = {
        "initial": "start",
        "states": {
            "start": {
                "transitions": [ # resolved in order
                    {"target": "walking", "cond": is_walking},
                    {"target": "running", "cond": is_running},
                ],
            },
            "walking": {"events": {"CROSSED": {"target": "crossed"}}},
            "running": {"events": {"CROSSED": {"target": "crossed"}}},
            "crossed": {},
        },
    }


pedestrian_states = {
        "initial": "walk",
        "states": {
            "walk": {"events": {"PED_COUNTDOWN": {"target": "wait"}}, **walk_states},
            "wait": {"events": {"PED_COUNTDOWN": {"target": "stop"}}},
            "stop": {},
            "blinking": {},
        },
    }


crossing_config = {
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
        },
    }
```

Example usage:

```python
from kiwi_cogs import Machine

crossing = await Machine.create(crossing_config)

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
```
