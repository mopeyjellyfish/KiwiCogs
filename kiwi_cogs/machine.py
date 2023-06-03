from logging import Logger, getLogger
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, root_validator, validator

from .event import Event
from .exceptions import UnknownTarget
from .state import State
from .utils import parse_target


class Machine(BaseModel):
    name: str
    """The name for the machine"""
    initial: str
    """The name of the initial state"""
    state: Optional[State]
    """The current state for the machine"""
    guards: Optional[Dict[str, Callable]]
    """Possible guards, which are callables"""
    actions: Optional[Dict[str, Callable]]
    """Action side effects for the machine"""
    context: Optional[Dict[str, Any]]
    """The contextual information """
    events: Optional[Union[Dict[str, Event], List[Event]]] = {}
    """The events at the root of the machine"""
    states: Dict[str, State]
    """The possible states for the machine"""
    logger: Logger = getLogger(__name__)
    """The logger for the machine"""

    class Config:
        arbitrary_types_allowed = True

    @validator("states", pre=True)
    def build_states(cls, value: dict, values: Dict[str, Any]) -> Dict[str, State]:
        """Builds the states from the passed in states object.

        :param value: The state configuration dictionary.
        :type value: dict

        :return: The built state objects.
        :rtype: Dict[str, State]
        """
        guards = values.get("guards")
        actions = values.get("actions")
        return {name: State(name=name, actions=actions, guards=guards, **val) for name, val in value.items()}

    @root_validator
    def build_initial_state(cls, values: Dict[str, Any]) -> Dict:
        """Builds the initial state value.

        :param values: The values passed to the Machine constructor.
        :type values: Dict

        :return: The updated values.
        :rtype: Dict
        """
        if states := values.get("states"):
            initial = values["initial"]
            values["state"] = states.get(initial)
        # check for transient state and transition?
        return values

    @classmethod
    async def create(cls: "Machine", config: dict) -> "Machine":  # type: ignore[misc]
        """Creates a new instance of the Machine class.

        :param config: The machine configuration dictionary.
        :type config: dict

        :return: The created Machine instance.
        :rtype: Machine
        """
        machine = cls(**config)  # type: ignore[operator]
        await machine.step()  # make sure all transient states are executed for initial state
        return machine  # type: ignore[no-any-return]

    @validator("events", pre=True)
    def build_events(cls, value: dict) -> Dict[str, Event]:
        """Build the events

        :param value: The events to be built
        :type value: dict

        :returns: The built events as a dictionary
        :rtype: dict
        """
        return {name: Event(name=name, transitions=val) for name, val in value.items()}

    def update_config(self, config: dict) -> None:
        """Updates this instances config with the passed in config.

        :param config: The configuration to update the instance with.
        :type config: dict
        """

    async def event(self, event: str) -> State:
        """Transitions the machine by executing an event

        :param event: The name of the event to trigger
        :type event: str

        :returns: The current state of the machine after the transition
        :rtype: State
        """
        self.logger.info("Machine processing event: %s", event)
        event = self.events.get(event) if event in self.events else self.state.get_event(event)  # type: ignore[union-attr, assignment, operator]
        if event:
            transition = await event.get_transition(self.context, event)  # type: ignore[attr-defined]
            if transition:  # there is a transition
                if transition.target is not None:
                    await self.do_transition(target=transition.target)  # if the transition has a target set the state
                await self.step()  # step through the machine as state changed
        else:
            self.logger.error("Event %s not found", event)

        return self.state  # type: ignore[return-value]

    async def step(self, state: Optional[State] = None) -> State:
        """Step through the machine until no more transitions to move through

        :param state: The state to start the step process from, defaults to None which will use the current state of the machine
        :type state: Optional[State], optional

        :returns: The final state after all possible transitions have been processed
        :rtype: State
        """
        if state is None:
            state = self.state

        transition = await self.state.get_transition(context=self.context)  # type: ignore[union-attr , arg-type]
        if transition and transition.target is not None:
            await self.do_transition(transition.target)
            return await self.step()  # step through the new state

        return state  # type: ignore[return-value]

    async def on_entry(self, context: dict) -> None:
        """Perform any entry actions for the new state

        :param context: The context data for the current state
        :type context: dict
        """
        await self.state.on_entry(context)  # type: ignore[union-attr]

    async def on_exit(self, context: dict) -> None:
        """Perform any exit actions for the current state

        :param context: The context data for the current state
        :type context: dict
        """
        await self.state.on_exit(context)  # type: ignore[union-attr]

    async def update_state(self, target: str) -> bool:
        """Update the current state to the target state

        :raises: UnknownTarget - If the target state can not be found
        """
        target_state, remainder = parse_target(target=target)
        state = self.states.get(target_state)
        if state is None:
            # if the state is target state is None pass to child state to handle
            if await self.state.update_state(target, self.context) is None:  # type: ignore[union-attr, arg-type]
                raise UnknownTarget("Target state can not be found")
            return False
        else:
            if self.state:
                await self.on_exit(self.context)  # type: ignore[arg-type]
            self.state = state
            if remainder and remainder != target_state:
                # consume the rest of the path!
                await self.state.update_state(remainder, self.context)  # type: ignore[arg-type]
            return True

    async def do_transition(self, target: str) -> None:
        """Set a state from a target

        :param target: The name of the state to transition to
        :type target: str
        """
        if await self.update_state(target):
            await self.on_entry(self.context)  # type: ignore[arg-type]

        return None

    async def with_context(self, context: dict) -> State:
        """Update the context and step through the machine

        :param context: The context to update the machine with
        :type context: dict

        :returns: The final state after all possible transitions have been processed
        :rtype: State
        """
        self.context = context  # update the context
        return await self.step()  # step through the machine

    @property
    def initial_state(self) -> State:
        """Get the initial state of the machine

        :returns: The initial state of the machine
        :rtype: State
        """
        return self.states[self.initial]
