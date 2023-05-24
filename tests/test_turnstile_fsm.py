from pytest import fixture

from kiwi_cogs import Machine


def check_coin_inserted(context, _):
    return context.get("coin_inserted", False)


def check_turnstile_rotated(context, _):
    return context.get("turnstile_rotated", False)


def accept_coin(context, _):
    context["coin_inserted"] = True
    context["turnstile_rotated"] = False


def lock_turnstile(context, _):
    context["turnstile_rotated"] = True
    context["coin_inserted"] = False


@fixture
def turnstile_config():
    return {
        "name": "turnstile",
        "initial": "locked",
        "context": {},
        "states": {
            "locked": {
                "transitions": [{"target": "unlocked", "cond": check_coin_inserted}],
                "events": {"INSERT_COIN": {"actions": accept_coin}},
            },
            "unlocked": {
                "transitions": [{"target": "locked", "cond": check_turnstile_rotated}],
                "events": {"ROTATE_TURNSTILE": {"actions": lock_turnstile}},
            },
        },
        "guards": {
            "coinInserted": check_coin_inserted,
            "turnstileRotated": check_turnstile_rotated,
        },
        "actions": {"acceptCoin": accept_coin, "lockTurnstile": lock_turnstile},
    }


@fixture
async def turnstile(turnstile_config) -> Machine:
    return await Machine.create(turnstile_config)


async def test_turnstile(turnstile: Machine):
    assert turnstile.initial_state.value == "locked"
    await turnstile.event("INSERT_COIN")
    assert turnstile.state.value == "unlocked"
    await turnstile.event("ROTATE_TURNSTILE")
    assert turnstile.state.value == "locked"
    await turnstile.event("INSERT_COIN")
    assert turnstile.state.value == "unlocked"
    await turnstile.event("ROTATE_TURNSTILE")
    assert turnstile.state.value == "locked"
