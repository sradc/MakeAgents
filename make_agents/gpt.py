from pathlib import Path

import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

# TODO: move to config
openai.api_key = Path("openai.key").read_text().strip()


@retry(
    retry=retry_if_exception_type((openai.error.Timeout, openai.error.RateLimitError)),
    wait=wait_random_exponential(min=0, max=60),
    stop=stop_after_attempt(6),
)
def completion(**kwargs):
    return openai.ChatCompletion.create(**kwargs)
