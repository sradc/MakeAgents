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
"""Bonus content.
Not properly documented or tested, and dependencies not captured in Poetry.
Use at your own risk.
"""


def draw_graph(agent_graph: dict[callable, list[callable]]):
    import io

    import graphviz
    from PIL import Image

    dot = graphviz.Digraph(comment="graph", format="png", graph_attr={"dpi": "80"})
    for node in agent_graph:
        dot.node(node.__name__, node.__name__)
    for node, children in agent_graph.items():
        if isinstance(children, list):
            for child in children:
                dot.edge(node.__name__, child.__name__)
        else:
            dot.edge(node.__name__, children.__name__)
    gvz_graph = dot.pipe(format="png")
    image = Image.open(io.BytesIO(gvz_graph), mode="r", formats=["png"]).convert("RGB")
    return image


def pretty_print(message: dict):
    # Originally based on: https://github.com/openai/openai-cookbook/blob/f52ffdaca42073066f8f43f7d65a59dcc01c9349/examples/How_to_call_functions_with_chat_models.ipynb
    if message["role"] == "system":
        print(f"system message: {message['content']}\n")
    elif message["role"] == "user":
        print(f"user message: {message['content']}\n")
    elif message["role"] == "assistant" and message.get("function_call"):
        arguments = message["function_call"]["arguments"]
        arguments = "<no arguments>" if arguments == "null" else arguments
        print(f"call `{message['function_call']['name']}`: {arguments}\n")
    elif message["role"] == "assistant" and not message.get("function_call"):
        print(f"assistant message: {message['content']}\n")
    elif message["role"] == "function":
        print(f"`{message['name']}` result: {message['content']}\n")
