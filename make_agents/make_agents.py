# Copyright 2023 Sidney Radcliffe

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import inspect
import json
from copy import deepcopy
from enum import Enum
from typing import Iterator, Optional, Union

from pydantic import BaseModel, Field

from make_agents.gpt import get_completion_func

default_completion = get_completion_func()

default_system_prompt = """You are a helpful assistant. You will be given tasks, via function calls. You will be given the ability to run different functions at different times. Please use them to complete the most recent task you have been given."""


def action(func: callable) -> callable:
    """A decorator to create *action functions* — functions to be used by the agent.
    An action function must have *at most* one parameter, which must be annotated with a Pydantic model.

    Note that the following should be considered part of the "prompt" for the agent:

    - The name of the function

    - The Pydantic model, if the function has a parameter

    - The function's docstring (don't annotate the parameter in the docstring, use the Pydantic model for this)

    Parameters
    ----------
    func : callable
        The function to be decorated.

    Returns
    -------
    callable
        The same function, with metadata attached.

    Raises
    ------
    ValueError
        If the function has more than one parameter, or if the parameter is not annotated with a Pydantic model.
    """
    parameters = inspect.signature(func).parameters
    if len(parameters) == 0:
        func.description_for_llm = {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": None,
        }
    elif len(parameters) == 1:
        func.description_for_llm = {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": get_pydantic_model_from_action_func(func).model_json_schema(),
        }
    else:
        raise ValueError(f"Function {func.__name__} must have at most one parameter.")
    return func


def get_pydantic_model_from_action_func(func: callable) -> BaseModel:
    (arg,) = inspect.signature(func).parameters.values()
    try:
        arg.annotation.model_json_schema
    except AttributeError:
        raise ValueError(
            f"The parameter of {func.__name__} must be annotated with a pydantic model."
        )
    return arg.annotation


def select_next_action_factory(options: list[callable]) -> callable:
    names = [description(x)["name"] for x in options]
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate function names: {names}")

    class SelectNextFuncArg(BaseModel):
        thought_process: str = Field(
            ...,
            description="Describe your thought process for selecting the next function in a few words.",
        )
        next_function: Enum(
            "function_names",
            {description(x)["name"]: description(x)["name"] for x in options},
        ) = Field(..., description="Name of the function to call next")

    def select_next_func(arg: SelectNextFuncArg):
        return arg.next_function.value

    select_next_func.__doc__ = (
        "Given the following functions, choose the one that will most help you achieve"
        " your goal: " + ", ".join([json.dumps(description(x)) for x in options])
    )
    return action(select_next_func)


def description(action_func: callable) -> dict:
    try:
        return action_func.description_for_llm
    except AttributeError:
        raise ValueError(
            f"Missing metadata. Has function {action_func.__name__} been decorated with"
            f" `{action.__name__}`?"
        )


def get_func_input_from_llm(messages: list[dict], func: callable, completion: callable):
    response = completion(
        messages=messages,
        functions=[description(func)],
        function_call={
            "name": description(func)["name"]
        },  # force the function to be called
    )
    # Validate the arg
    pydantic_model = get_pydantic_model_from_action_func(func)
    func_arg = pydantic_model(
        **json.loads(response.choices[0].message.function_call.arguments)
    )
    # If the above didn't raise an error, we can assume the arg is valid
    func_arg_message = json.loads(
        json.dumps(response.choices[0].message)
    )  # make a clean dict
    return func_arg_message, func_arg


def run_func_for_llm(func: callable, arg: Optional[BaseModel]):
    func_result = func(arg) if arg else func()
    func_result_message = {
        "role": "function",
        "name": func.description_for_llm["name"],
        "content": json.dumps(func_result),
    }
    return func_result_message, func_result


class Start:
    """Used to mark the start of the action graph."""


class End:
    """Can be used to end the action graph."""

    description_for_llm = {
        "name": "End",
        "description": "End your assistance with immediate effect.",
        "parameters": None,
    }


def identity(x):
    return x


def run_agent(
    action_graph: Union[dict, callable],
    messages_init: Optional[list[dict]] = None,
    completion: Optional[callable] = default_completion,
    pre_llm_callback: Optional[callable] = identity,
) -> Iterator[list[dict[str, str]]]:
    """Run an agent. This is a generator that yields the list of messages after each step.
    Be mindful that the yielded messages are mutable, allowing them to be modified in place,
    (make copies if you want to avoid this).

    Parameters
    ----------
    action_graph : Union[dict[callable, list[callable]], callable]
        The graph of actions that the agent can take. Can either be a dictionary
        or a callable. Use a callable to create a dynamic action graph. (See examples in the README)
    messages_init : Optional[list[dict]], optional
        Optionally initialise the list of messages, e.g. to specify a custom system prompt.
        If not provided, the default system prompt will be used.
    completion : Optional[callable], optional
        The function that will be used to get completions from the LLM.
    pre_llm_callback : Optional[callable], optional
        This function is called before any LLM calls.
        It will be passed the list of messages, and can modify it in place.
        Can be used for, e.g. reducing the list of messages to only the most recent ones,
        or reducing the list by summarising, etc.

    Yields
    ------
    Iterator[list[dict[str, str]]]
        At each step, the list of messages is yielded,
        i.e. the same list that was yielded in the previous step, with one more message appended.
    """
    if isinstance(action_graph, dict):
        action_graph = dict_to_action_graph_func(action_graph)
    messages = (
        deepcopy(messages_init)
        if messages_init
        else [{"role": "system", "content": default_system_prompt}]
    )
    current_action = Start
    current_action_result = None
    while True:
        next_action_options = action_graph(
            current_action=current_action, current_action_result=current_action_result
        )
        if not next_action_options:
            break
        # DECIDE NEXT ACTION
        if len(next_action_options) == 1:
            current_action = next_action_options[0]
        else:
            pre_llm_callback(messages)
            select_next_action: callable = select_next_action_factory(next_action_options)
            func_arg_message, func_arg = get_func_input_from_llm(
                messages, select_next_action, completion
            )
            messages.append(func_arg_message)
            yield deepcopy(messages)
            pre_llm_callback(messages)
            func_result_message, func_result = run_func_for_llm(
                select_next_action, func_arg
            )
            messages.append(func_result_message)
            yield deepcopy(messages)
            current_action = next(
                x for x in next_action_options if description(x)["name"] == func_result
            )
        if current_action == End:
            break
        # RUN THE ACTION
        if description(current_action)["parameters"]:
            pre_llm_callback(messages)
            func_arg_message, func_arg = get_func_input_from_llm(
                messages, current_action, completion
            )
        else:
            func_arg_message = {
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": description(current_action)["name"],
                    "arguments": "null",
                },
            }
            func_arg = None
        messages.append(func_arg_message)
        yield deepcopy(messages)
        pre_llm_callback(messages)
        func_result_message, func_result = run_func_for_llm(current_action, func_arg)
        messages.append(func_result_message)
        yield deepcopy(messages)
        current_action_result = func_result


def dict_to_action_graph_func(action_graph: dict) -> callable:
    def action_graph_func(
        current_action: callable, current_action_result: Union[dict, None]
    ):
        return action_graph.get(current_action, None)

    return action_graph_func
