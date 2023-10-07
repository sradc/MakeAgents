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
"""Bonus content, i.e. not essential, not prioritised for development, but nice to have.
"""
import io


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
    gvz_graph = dot.pipe(format="png")
    image = Image.open(io.BytesIO(gvz_graph), mode="r", formats=["png"]).convert("RGB")
    return image
