from pydantic import BaseModel, Field

import make_agents as ma


@ma.action
def get_task_instructions():
    return "Get the users email address, and validate it."


class MessageUserArg(BaseModel):
    message: str = Field(description="Message to send user")


@ma.action
def message_user(arg: MessageUserArg):
    """Send the user a message, and get their response."""
    response = ""
    while response == "":
        response = input(arg.message + "\n").strip()
    return response


class SendValidationEmailArg(BaseModel):
    users_email_address: str = Field(description="The users email address")


@ma.action
def send_validation_email(arg: SendValidationEmailArg):
    """Send the user a validation email."""
    if not arg.users_email_address.endswith(".com"):
        return {"status": "error", "description": "Email address must end with `.com`"}
    else:
        return {"status": "success", "description": "Validation code sent"}


class CheckValidationCodeArg(BaseModel):
    validation_code: str = Field(description="The validation code (6 digits)")


@ma.action
def check_validation_code(arg: CheckValidationCodeArg):
    """Send the user a validation email."""
    if len(arg.validation_code) != 6:
        return {"status": "error", "description": "Validation code must be 6 digits"}
    elif arg.validation_code == "123456":
        return {"status": "success", "description": "Validation code correct"}
    else:
        return {"status": "error", "description": "Validation code incorrect"}


def action_graph(current_action: callable, current_action_result: dict) -> list[callable]:
    """Return the next action(s) to run, given the current action and its result."""
    if current_action == ma.Start:
        return [get_task_instructions]
    elif current_action == get_task_instructions:
        return [message_user]
    elif current_action == message_user:
        return [message_user, send_validation_email, check_validation_code]
    elif current_action == send_validation_email:
        if current_action_result["status"] == "success":
            return [message_user]
        else:
            return [message_user, send_validation_email]
    elif current_action == check_validation_code:
        if current_action_result["status"] == "success":
            return [ma.End]
        else:
            return [message_user, check_validation_code]
    else:
        raise ValueError(f"Unknown action: {current_action}")


# Run the agent
print("Starting agent...\n\n")
for messages in ma.run_agent(action_graph):
    ma.bonus.pretty_print(messages[-1])
