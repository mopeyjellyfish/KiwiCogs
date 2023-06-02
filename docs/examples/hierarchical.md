# Hierarchical State Machine

This example shows how to create a hierarchical state machine. The machine is a traffic light with a pedestrian crossing. The pedestrian crossing has a countdown timer. When the timer reaches zero, the pedestrian crossing changes to red and the traffic light changes to green.

```python
import asyncio
import random

from kiwi_cogs import Machine


def is_walking(context, _):
    return context["speed"] <= 11


def is_running(context, _):
    return context["speed"] > 11


walk_states = {
    "initial": "start",
    "states": {
        "start": {
            "transitions": [  # resolved in order
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


config = {
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


async def run():
    machine = await Machine.create(config)
    print(f"Light is: {machine.state.name}")
    while True:
        await machine.event("TIMER")
        print(f"Light is: {machine.state.name}")
        if machine.state.name == "red":
            value = machine.state.value["red"]
            print(f"Pedestrian: {value}")
            await machine.event("CROSSED")
            value = machine.state.value["red"]
            print(f"Pedestrian: {value}")
            await machine.event("PED_COUNTDOWN")
            value = machine.state.value["red"]
            print(f"Pedestrian: {value}")
            await machine.event("PED_COUNTDOWN")
            value = machine.state.value["red"]
            print(f"Pedestrian: {value}")

            # 10 percent chance of power outage
            if random.random() > 0.9:
                await machine.event("POWER_OUTAGE")
                print(f"Power outage! {machine.state.name}")
                print(f"Battery: {machine.state.value}")
                await asyncio.sleep(3)
                await machine.event("POWER_RESTORED")
            else:
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())
```

Example output:

```bash
Light is: green
Light is: yellow
Light is: red
Pedestrian: {'walk': 'walking'}
Pedestrian: {'walk': 'crossed'}
Pedestrian: wait
Pedestrian: stop
Light is: green
Light is: yellow
Light is: red
Pedestrian: {'walk': 'walking'}
Pedestrian: {'walk': 'crossed'}
Pedestrian: wait
Pedestrian: stop
Light is: green
Light is: yellow
Light is: red
Pedestrian: {'walk': 'walking'}
Pedestrian: {'walk': 'crossed'}
Pedestrian: wait
Pedestrian: stop
Light is: green
Light is: yellow
Light is: red
Pedestrian: {'walk': 'walking'}
Pedestrian: {'walk': 'crossed'}
Pedestrian: wait
Pedestrian: stop
```
