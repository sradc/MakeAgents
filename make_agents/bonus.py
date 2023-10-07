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
