from importlib_metadata import version

__version__ = version(__package__)

# Expose the objects that are part of the API
import make_agents.bonus as bonus  # noqa: F401
import make_agents.gpt as gpt  # noqa: F401
from make_agents.make_agents import Start, action, run_agent  # noqa: F401
