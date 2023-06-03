from asyncio import iscoroutinefunction
from typing import Callable, Dict, List, Optional, Union

from pydantic import BaseModel, validator

from .transition import Transition


class Event(BaseModel):
    name: Optional[str] = None
    """Name of the event"""
    guards: Optional[Dict[str, Callable]] = None
    """Possible guards, which are callables"""
    actions: Optional[Dict[str, Callable]] = None
    """Action side effects for the machine"""
    transitions: List[Transition]

    @validator("transitions", pre=True)
    def build_transitions(cls, value: Union[Dict, List], values: Dict) -> List[Transition]:
        """Build a list of transitions from the given transition data

        :param transition_data: The transition data, either a single transition dict or a list of transition dicts
        :type transition_data: Union[Dict, List]

        :returns: The list of transitions
        :rtype: List[Transition]"""
        guards = values.get("guards")
        actions = values.get("actions")
        if isinstance(value, dict):
            return [Transition(guards=guards, actions_map=actions, **value)]
        else:
            return [Transition(guards=guards, actions_map=actions, **transition) for transition in value]

    async def execute_actions(self, context: dict, event: str, transition: Transition) -> None:
        """Execute all of the actions in a transition

        :param context: The context of the system
        :type context: dict

        :param event: The event that triggered the transition
        :type event: str

        :param transition: The transition that will be executed
        :type transition: Transition"""
        for action in transition.actions:
            if iscoroutinefunction(action):
                await action(context, event)
            else:
                action(context, event)

    async def get_transition(self, context: dict, event: str) -> Optional[Transition]:  # type: ignore[return]
        """Return the next transition to take, if a condition is met

        :param context: The context of the system
        :type context: dict

        :param event: The event that triggered the transition
        :type event: str

        :returns: The next transition to take, if a condition is met
        :rtype: Optional[Transition]
        """
        for transition in self.transitions:
            if transition.cond(context, event):
                await self.execute_actions(context=context, event=event, transition=transition)
                return transition
