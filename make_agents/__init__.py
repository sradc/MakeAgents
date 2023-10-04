from importlib_metadata import version

__version__ = version(__package__)

# Expose the main api:
from make_agents.make_agents import Start, draw_graph, llm_func, run_agent  # noqa: F401
