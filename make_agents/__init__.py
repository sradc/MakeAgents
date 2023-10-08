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
from importlib_metadata import version

__version__ = version(__package__)

# Expose the objects that are part of the API
import make_agents.bonus as bonus  # noqa: F401
import make_agents.gpt as gpt  # noqa: F401
from make_agents.make_agents import (  # noqa: F401
    ActionGraphDict,
    Start,
    action,
    run_agent,
)
