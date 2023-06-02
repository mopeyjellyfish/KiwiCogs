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
