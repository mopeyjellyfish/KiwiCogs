import asyncio
from enum import Enum
from logging import Logger, getLogger
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, root_validator, validator

from .event import Event
from .transition import Transition
from .utils import parse_target

ALWAYS = "always"


class StateType(str, Enum):
    atomic = "atomic"
    compound = "compound"
    final = "final"
    transient = "transient"


class State(BaseModel):
    type: Optional[StateType]  # noqa: A003
    """The type of state this is"""
    name: str
    """The name for this state"""
    state: Optional["State"] = None
    """The sub-state for this state"""
    entry: List[Callable] = []
    """Callables to call when entering this state"""
    exit: List[Callable] = []  # noqa: A003
    """Callables to call when exiting this state"""
    parent: Optional[str] = "."
    """The parent of this state"""
    initial: Optional[str] = None
    """The name of the initial sub-state for this state"""
    guards: Optional[Dict[str, Callable]]
    """Possible guards, which are callables"""
    actions: Optional[Dict[str, Callable]]
    """Action side effects for the machine"""
    transitions: List[Transition] = []
    """Transient transitions to call when stepping through the state"""
    states: Optional[Dict[str, "State"]] = {}
    """All possible state for this state"""
    events: Optional[Union[Dict[str, Event], List[Event]]] = {}
    """Possible events to execute for this state"""
    logger: Logger = getLogger(__name__)

    class Config:
        arbitrary_types_allowed = True

    @validator("states", pre=True)
    def build_states(cls, value: dict, values: dict) -> Dict[str, "State"]:
        """Build the states from the passed in states object

        :param value: The states object to be built
        :type value: dict

        :returns: The built states as a dictionary
        :rtype: dict
        """
        current_name = values.get("name")
        parent_name = values.get("parent")
        guards = values.get("guards")
        actions = values.get("actions")
        formatted_parent = f"{parent_name}{'.' if parent_name != '.' else ''}{current_name}"

        return {
            name: State(
                name=name,
                guards=guards,
                actions=actions,
                parent=formatted_parent,
                **val,
            )
            for name, val in value.items()
        }

    @root_validator
    def build_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Builds the type based on the values passed in

        - Compound is defined as having sub-states.
        - Atomic is defined as having events but no sub-states
        - Transient is defined as only having transitions
        - Final is defined as having no further state changes
        """
        states = values.get("states")
        transitions = values.get("transitions")
        events = values.get("events")
        _type = None
        if states:
            _type = StateType.compound
        elif events:
            _type = StateType.atomic
        elif transitions:
            _type = StateType.transient
        else:
            _type = StateType.final

        values["type"] = _type
        return values

    @validator("events", pre=True)
    def build_events(cls, value: dict, values: Dict[str, Any]) -> Dict[str, Event]:
        """Build the events

        :param value: The events to be built
        :type value: dict

        :returns: The built events as a dictionary
        :rtype: dict
        """
        guards = values.get("guards")
        actions = values.get("actions")
        return {name: Event(name=name, guards=guards, actions=actions, transitions=val) for name, val in value.items()}

    @validator("transitions", pre=True)
    def build_transitions(cls, value: Optional[list], values: dict) -> List[Transition]:
        """Build the always transient transitions

        :param value: The transitions to be built
        :type value: Optional[list]

        :returns: The built transitions as a list
        :rtype: list
        """
        guards = values.get("guards")
        actions = values.get("actions")
        if isinstance(value, dict):
            return [Transition(target=value["target"], guards=guards, actions_map=actions)]
        else:
            return [Transition(guards=guards, actions_map=actions, **transition) for transition in value]  # type: ignore[union-attr]

    @validator("entry", pre=True)
    def build_entry(cls, value: Optional[list]) -> List[Callable]:
        """Setup the entry callables

        :param value: The callables to be set up
        :type value: Optional[list]

        :returns: The set up callables as a list
        :rtype: list
        """
        return [value] if callable(value) else value  # type: ignore[return-value, list-item]

    @validator("exit", pre=True)
    def build_exit(cls, value: Optional[list]) -> List[Callable]:
        """Setup the exit callables

        :param value: The callables to be set up
        :type value: Optional[list]

        :returns: The set up callables as a list
        :rtype: list
        """
        return [value] if callable(value) else value  # type: ignore[return-value, list-item]

    @property
    def value(self) -> Union[str, Dict[str, Any]]:
        """Return the value of the state

        :returns: The name of the state
        :rtype: str
        """
        return {self.name: self.state.value} if self.state else self.name

    def get_event(self, name: str) -> Optional[Event]:
        """Return event for the name

        :param name: The name of the event to return
        :type name: str

        :returns: The event with the given name
        :rtype: Event
        """
        self.logger.info("State %s finding event %s", self.name, name)
        event = self.events.get(name)  # type: ignore[union-attr]
        if event is None and self.state:  # this state does not have the event!
            # check the current child state of for this event
            self.logger.info("%s found event %s", self.name, name)
            event = self.state.get_event(name=name)
        else:
            self.logger.info("State %s found event %s", self.name, name)
        return event

    async def on_entry(self, context: dict) -> None:
        """Called when the state is entered

            - Handle compound states
            - Call `on_entry`

        :param context: A dictionary that contains the current context of the system
        :type context: dict
        """
        self.logger.info("Entering %s state in %s parent", self.name, self.parent)
        await self._process_callables(self.entry, context)  # state entered so process entry handlers
        if self.states and not self.state:  # if there sub-states they should be processed!
            self.state = self.states.get(str(self.initial))  # set the initial state

            # call the state's on_entry to setup any further sub-states
            await self.state.on_entry(context=context)  # type: ignore[union-attr]

    async def on_exit(self, context: dict) -> None:
        """Called when a state is exited

        :param context: A dictionary that contains the current context of the system
        :type context: dict
        """
        self.logger.info("Exiting %s state in %s parent", self.name, self.parent)
        await self._process_callables(self.exit, context)
        if self.state:
            await self.state.on_exit(context=context)  # call the sub-state's on_exit to exit any sub-states
            self.state = None  # reset the stored state upon exiting

    async def _process_callables(self, callables: List[Callable], context: dict) -> None:
        """Process the given callables with the given context

        :param context: A dictionary that contains the current context of the system
        :type context: dict
        :param callables: A dictionary that contains the current context of the system
        :type callables: List[Callable]
        """
        for func in callables:
            if asyncio.iscoroutinefunction(func):
                await func(context)
            else:
                func(context)

    async def update_state(self, target: str, context: dict) -> Optional["State"]:
        """Update the current state to the target state

        :raises: UnknownTarget - If the target state can not be found
        """
        target_state, remainder = parse_target(target=target)

        state = self.states.get(target_state)  # type: ignore[union-attr]
        if state is None:  # noqa: SIM102
            # if there is a sub-state then pass this onto the next state
            if self.state:
                return await self.state.update_state(target=target, context=context)
        else:
            if self.state:  # exiting state
                await self.state.on_exit(context=context)
            self.state = state
            await self.state.on_entry(context)
            if remainder and remainder != target_state:
                await self.state.update_state(target=remainder, context=context)
            return state

        return None

    async def get_transition(self, context: dict) -> Optional[Transition]:
        """Check the conditions for each transition of the given state

        :param context: A dictionary that contains the current context of the system
        :type context: dict

        :returns: The next transition to take, if a condition is met
        :rtype: Optional[Transition]
        """

        if self.state:  # noqa: SIM102
            # Go depth first to the last state
            if new_transition := await self.state.get_transition(context=context):
                if new_transition.target is not None:
                    await self.on_exit(context=context)
                    await self.update_state(target=new_transition.target, context=context)

        for transition in self.transitions:
            if asyncio.iscoroutinefunction(transition.cond):
                condition = await transition.cond(context, None)
            else:
                condition = transition.cond(context, None)

            if condition:
                return transition

        return None
