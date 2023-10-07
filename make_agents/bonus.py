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


def display_message_dict_jupyter(message: dict):
    import pandas as pd
    from IPython.display import HTML, display

    # Create style without index and with left-aligned text
    style = """
    <style>
        .dataframe thead { display: none; }
        .dataframe tbody tr th:only-of-type { display: none; }
        .dataframe tbody td { text-align: left; }
    </style>
    """
    message = dict(sorted(message.items()))
    df = pd.DataFrame(list(message.items()), columns=["Key", "Value"])
    # Show DataFrame
    display(HTML(df.to_html(index=False)))
    display(HTML(style))
