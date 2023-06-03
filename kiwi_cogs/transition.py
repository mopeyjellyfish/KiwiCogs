from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, validator

from .exceptions import UnknownAction, UnknownGuard


def ALWAYS(*_: Any) -> bool:
    return True


def load_actions(values: List[Union[str, Callable]], funcs: Dict[str, Callable]) -> List[Callable]:
    """Load all of the actions in the passed values

    :param values: values to load
    :type values: List[Union[str, Callable]]
    :param funcs: functions to load from
    :type funcs: Dict[str, Callable]
    :raises UnknownAction: when an action can be looked up in the passed in actions
    :return: list of loaded callable actions
    :rtype: List[Callable]
    """
    loaded_actions = []
    for value in values:
        if isinstance(value, str):
            action = funcs.get(value)
            if action is not None:
                loaded_actions.append(action)
            else:
                raise UnknownAction(f"Unknown action '{value} - expected one of: {', '.join(funcs.keys())}'")
        else:
            loaded_actions.append(value)

    return loaded_actions


class Transition(BaseModel):
    """Represents a state transition in a state machine

    :param target: The target state to transition to.
    :type target: str
    :param cond: A function or string that represents the condition that must be met before the transition can occur.
                 If it is a string, it is assumed to be the name of a function that must be available in the current context.
    :type cond: Callable or str
    :param actions: A list of functions or strings that represent the actions to be executed during the transition.
                   If an item is a string, it is assumed to be the name of a function
                   that must be available in the current context.
    :type actions: List[Union[Callable, str]]
    """

    target: Optional[str] = None
    """The target state for this transition if the condition is met"""
    guards: Optional[Dict[str, Callable]]
    """Possible guards, which are callables"""
    actions_map: Optional[Dict[str, Callable]] = None
    """Action map"""
    actions: List[Callable] = []
    """Action side effects for the machine"""
    cond: Callable = ALWAYS
    """The condition for the transition"""

    @validator("actions", pre=True)
    def build_actions(cls: "Transition", value: Union[Callable, List], values: Dict[str, Any]) -> List[Callable]:  # type: ignore[return]
        """Builds the list of actions to be executed during the transition.

        :param value: A function or a list of functions that represent the actions to be executed during the transition.
        :type value: Union[Callable, List]
        :return: A list of functions that represent the actions to be executed during the transition.
        :rtype: List[Callable]
        """
        actions = values.get("actions_map")

        if callable(value):  # a single action value return as a list
            return [value]
        elif isinstance(value, str):  # string callable look it up!
            return load_actions([value], actions)
        elif actions:
            return load_actions(value, actions)  # load the list of actions

    @validator("cond", pre=True)
    def build_cond(cls: "Transition", value: Union[Callable, str], values: Dict[str, Any]) -> Optional[Callable]:  # type: ignore[return]
        """Builds the cond value for a transition

        :param value: the condition callable / str
        :type value: Union[Callable, str]
        :param values: values
        :type values: Dict[str, Any]
        :return: Callable
        :rtype: Callable
        """
        guards = values.get("guards")
        if callable(value):
            return value
        elif isinstance(value, str) and guards is not None:
            guard = guards.get(value)
            if guard is None:
                raise UnknownGuard(f"Unknown action '{value} - expected one of: {', '.join(guards.keys())}'")
            elif callable(guard):
                return guard  # type: ignore[no-any-return]
