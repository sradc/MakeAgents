from importlib_metadata import version

__version__ = version(__package__)

# Expose the main api:
import make_agents.bonus as bonus  # noqa: F401
from make_agents.gpt import gpt  # noqa: F401
from make_agents.make_agents import Start, action, run_agent  # noqa: F401
