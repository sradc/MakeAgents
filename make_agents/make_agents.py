import inspect


def llm_func(func):
    # Keep the logic simple, by restricting the `func` to have exactly 1 parameter,
    # that must be annotated with a pydantic model.
    parameters = inspect.signature(func).parameters
    if len(parameters) != 1:
        raise ValueError(f"Function {func.__name__} must have exactly 1 parameter.")
    (arg,) = inspect.signature(func).parameters.values()
    if not getattr(arg.annotation, "model_json_schema", None):
        raise ValueError(
            f"The parameter of {func.__name__} must be annotated with a pydantic model."
        )
    # Simply attach metadata to the function, so it can still be used as normal
    func.description_for_llm = {
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": arg.annotation.model_json_schema(),
    }
    return func
