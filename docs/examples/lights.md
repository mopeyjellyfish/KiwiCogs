# Light machine

This machine is a simple example of a traffic light, it has three states: green, yellow and red. It has a single event: NEXT, which transitions the light to the next state.

```python
import asyncio

from kiwi_cogs import Machine

config = {
    "name": "lights",  # the name of this machine
    "initial": "green",  # the initial state when the machine is created
    "states": {  # the possible states of the machine
        "green": {
            "events": {"NEXT": {"target": "yellow"}},  # when this event is triggered, transition to yellow
        },
        "yellow": {"events": {"NEXT": {"target": "red"}}},
        "red": {"events": {"NEXT": {"target": "green"}}},
    },
}


async def run():
    machine = await Machine.create(config)
    for _ in range(10):
        print(f"Light is: {machine.state.name}")
        await machine.event("NEXT")


asyncio.run(run())
```

Example output:

```bash
Light is: green
Light is: yellow
Light is: red
Light is: green
Light is: yellow
Light is: red
Light is: green
Light is: yellow
Light is: red
Light is: green
```
