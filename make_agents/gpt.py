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
import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


def get_completion_func(model: str = "gpt-4", **kwargs) -> callable:
    """Returns a function for getting completions from OpenAI.
    Can specify more parameters, e.g. temperature, etc. via kwargs, see:
    https://platform.openai.com/docs/api-reference/introduction?lang=python

    Parameters
    ----------
    model : str, optional
        The chat model to use, by default "gpt-4".

    Returns
    -------
    callable
        A function that is used to get completions from OpenAI, to drive agents.
    """

    @retry(
        retry=retry_if_exception_type(
            (openai.error.Timeout, openai.error.RateLimitError)
        ),
        wait=wait_random_exponential(min=0, max=60),
        stop=stop_after_attempt(6),
    )
    def completion(**kwargs2):
        return openai.ChatCompletion.create(model=model, **kwargs, **kwargs2)

    return completion
