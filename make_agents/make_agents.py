import inspect
import io
import json
from copy import deepcopy
from enum import Enum

from pydantic import BaseModel, Field

from make_agents.gpt import get_completion

default_completion = get_completion()


def llm_func(func):
    # Restrict `func` to have exactly 1 parameter, that must be annotated with a pydantic model,
    # to keep the logic simple.
    # We'll just attach metadata to the function, so it can still be used as normal.
    parameters = inspect.signature(func).parameters
    if len(parameters) == 0:
        # A func with no parameters will be called without asking the LLM for args,
        # but we still want the name and description to be available, and we will attach the response.
        func.description_for_llm = {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": None,
        }
    elif len(parameters) == 1:
        pydantic_model = get_llm_func_pydantic_model(func)
        func.description_for_llm = {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": pydantic_model.model_json_schema(),
        }
    else:
        raise ValueError(f"Function {func.__name__} must have exactly 1 parameter.")
    return func


def get_llm_func_pydantic_model(func) -> BaseModel:
    (arg,) = inspect.signature(func).parameters.values()
    if not getattr(arg.annotation, "model_json_schema", None):
        raise ValueError(
            f"The parameter of {func.__name__} must be annotated with a pydantic model."
        )
    return arg.annotation


def select_next_func_factory(functions: list[callable]):
    class SelectNextFuncArg(BaseModel):
        next_function: Enum(
            "function_names",
            {description(x)["name"]: description(x)["name"] for x in functions},
        ) = Field(..., description="Name of the function to call next")

    def select_next_func(arg: SelectNextFuncArg) -> str:
        return {"next_function": arg.next_function.value}

    select_next_func.__doc__ = (
        "Given the following functions, choose the one that will most help you achieve your goal: "
        + ", ".join([json.dumps(description(x)) for x in functions])
    )
    return llm_func(select_next_func)


def description(llm_func: callable) -> dict:
    try:
        return llm_func.description_for_llm
    except AttributeError:
        raise ValueError(
            f"Missing metadata. Has function {llm_func.__name__} been decorated with `llm_func`?"
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
    pydantic_model = get_llm_func_pydantic_model(llm_func)
    func_arg = pydantic_model(
        **json.loads(response.choices[0].message.function_call.arguments)
    )
    # If the above didn't raise an error, we can assume the arg is valid
    func_arg_message = json.loads(
        json.dumps(response.choices[0].message)
    )  # make a clean dict
    return func_arg_message, func_arg


def run_func_for_llm(llm_func: callable, arg):
    func_result = llm_func(arg)
    func_result_message = {
        "role": "function",
        "name": llm_func.description_for_llm["name"],
        "content": json.dumps(func_result),
    }
    return func_result_message, func_result


class Start:
    pass


def run_agent(
    agent_graph: dict[callable, list[callable]],
    messages_init: list[dict],
    completion: callable = default_completion,
):
    messages = deepcopy(messages_init)
    options = agent_graph[Start]
    while True:
        # Decide which function to run next
        if len(options) == 1:
            current_node = options[0]
            arguments = json.dumps({"next_function": description(current_node)["name"]})
            # Pretend that we asked the LLM to select the next function (so it's in the history)
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": "select_next_func",
                        "arguments": arguments,
                    },
                },
            )
            yield messages
            messages.append(
                {
                    "role": "function",
                    "name": "select_next_func",
                    "content": arguments,
                },
            )
            yield messages
        else:
            # llm decides the next function
            select_next_func = select_next_func_factory(options)
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
        # Run the function that was selected
        func_arg_message, func_arg = get_func_input_from_llm(
            messages, current_node, completion
        )
        messages.append(func_arg_message)
        yield messages
        func_result_message, func_result = run_func_for_llm(current_node, func_arg)
        messages.append(func_result_message)
        yield messages
        options = agent_graph.get(current_node, None)
        if not options:
            break


def draw_graph(agent_graph: dict[callable, list[callable]]):
    try:
        import graphviz
        from PIL import Image
    except ImportError:
        raise ImportError("You need to install graphviz and PIL to use this function.")
    dot = graphviz.Digraph(comment="graph", format="png", graph_attr={"dpi": "120"})
    for node in agent_graph:
        dot.node(node.__name__, node.__name__)
    for node, children in agent_graph.items():
        if isinstance(children, list):
            for child in children:
                dot.edge(node.__name__, child.__name__)
        else:
            dot.edge(node.__name__, children.__name__)
    gvz_graph = dot.pipe(format="png", engine="neato", renderer="cairo")
    image = Image.open(io.BytesIO(gvz_graph), mode="r", formats=["png"]).convert("RGB")
    return image
