import pytest
from pydantic import BaseModel, Field

from make_agents.make_agents import llm_func


def test_llm_func():
    class ExampleFuncArg(BaseModel):
        example_field: str = Field(description="This is an example field.")

    @llm_func
    def example_func(arg: ExampleFuncArg):
        """This is an example docstring"""
        return arg.example_field

    assert example_func.description_for_llm == {
        "name": "example_func",
        "description": "This is an example docstring",
        "parameters": {
            "properties": {
                "example_field": {
                    "description": "This is an example field.",
                    "title": "Example Field",
                    "type": "string",
                }
            },
            "required": ["example_field"],
            "title": "ExampleFuncArg",
            "type": "object",
        },
    }, "Did not get expected metadata."

    assert (
        example_func(ExampleFuncArg(example_field="example")) == "example"
    ), "Expected to be able to use function as normal."

    # Check that the function raises an error if there are multiple parameters
    with pytest.raises(ValueError):

        @llm_func
        def example_func(arg: ExampleFuncArg, arg2: ExampleFuncArg):
            pass

    # Check that the function raises an error if there are no parameters
    with pytest.raises(ValueError):

        @llm_func
        def example_func():
            pass

    # Check that the function raises an error if type hint not pydantic
    with pytest.raises(ValueError):

        @llm_func
        def example_func(arg: str):
            pass

    # Check that the function raises an error if no type hint
    with pytest.raises(ValueError):

        @llm_func
        def example_func(arg):
            pass
