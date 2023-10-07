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
from typing import Iterator, Optional

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


def get_pydantic_model_from_action_func(action_func) -> BaseModel:
    (arg,) = inspect.signature(action_func).parameters.values()
    try:
        arg.annotation.model_json_schema
    except AttributeError:
        raise ValueError(
            f"The parameter of {action_func.__name__} must be annotated with a pydantic"
            " model."
        )
    return arg.annotation


def select_next_action_factory(functions: list[callable]):
    class SelectNextFuncArg(BaseModel):
        next_function: Enum(
            "function_names",
            {description(x)["name"]: description(x)["name"] for x in functions},
        ) = Field(..., description="Name of the function to call next")

    def select_next_func(arg: SelectNextFuncArg) -> str:
        return {"next_function": arg.next_function.value}

    select_next_func.__doc__ = (
        "Given the following functions, choose the one that will most help you achieve"
        " your goal: "
        + ", ".join([json.dumps(description(x)) for x in functions])
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


def get_func_input_from_llm(
    messages: list[dict], llm_func: callable, completion: callable
):
    response = completion(
        messages=messages,
        functions=[description(llm_func)],
        function_call={
            "name": description(llm_func)["name"]
        },  # force the function to be called
    )
    # Validate the arg
    pydantic_model = get_pydantic_model_from_action_func(llm_func)
    func_arg = pydantic_model(
        **json.loads(response.choices[0].message.function_call.arguments)
    )
    # If the above didn't raise an error, we can assume the arg is valid
    func_arg_message = json.loads(
        json.dumps(response.choices[0].message)
    )  # make a clean dict
    return func_arg_message, func_arg


def run_func_for_llm(llm_func: callable, arg):
    func_result = llm_func(arg) if arg else llm_func()
    func_result_message = {
        "role": "function",
        "name": llm_func.description_for_llm["name"],
        "content": json.dumps(func_result),
    }
    return func_result_message, func_result


class Start:
    """Used to mark the start of the action graph."""


def run_agent(
    action_graph: dict[callable, list[callable]],
    messages_init: Optional[list[dict]] = None,
    completion: Optional[callable] = default_completion,
) -> Iterator[list[dict[str, str]]]:
    """Run an agent. This is a generator that yields the list of messages after each step.
    Be mindful that the yielded messages are mutable, allowing them to be modified in place,
    (make copies if you want to avoid this).

    Parameters
    ----------
    action_graph : dict[callable, list[callable]]
        The graph of actions that the agent can take.
    messages_init : Optional[list[dict]], optional
        Optionally initialise the list of messages, e.g. to specify a custom system prompt.
        If not provided, the default system prompt will be used.
    completion : Optional[callable], optional
        The function that will be used to get completions from the LLM.

    Yields
    ------
    Iterator[list[dict[str, str]]]
        At each step, the list of messages is yielded,
        i.e. the same list that was yielded in the previous step, with one more message appended.
    """
    messages = (
        deepcopy(messages_init)
        if messages_init
        else [{"role": "system", "content": default_system_prompt}]
    )
    options = action_graph[Start]
    while True:
        # Decide which function to run next
        if len(options) == 1:
            current_node = options[0]
        else:
            # llm decides the next function
            select_next_func = select_next_action_factory(options)
            func_arg_message, func_arg = get_func_input_from_llm(
                messages, select_next_func, completion
            )
            messages.append(func_arg_message)
            yield messages
            func_result_message, func_result = run_func_for_llm(
                select_next_func, func_arg
            )
            messages.append(func_result_message)
            yield messages
            next_function = func_result["next_function"]
            current_node = next(
                x for x in options if description(x)["name"] == next_function
            )
        if description(current_node)["parameters"]:
            # llm decides the arg
            func_arg_message, func_arg = get_func_input_from_llm(
                messages, current_node, completion
            )
            messages.append(func_arg_message)
            yield messages
            func_result_message, func_result = run_func_for_llm(current_node, func_arg)
            messages.append(func_result_message)
            yield messages
        else:
            # no arg, just run the function directly
            func_result_message, func_result = run_func_for_llm(current_node, None)
            messages.append(func_result_message)
            yield messages
        options = action_graph.get(current_node, None)
        if not options:
            break
