import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


def get_completion(model: str = "gpt-3.5-turbo", **kwargs) -> callable:
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
