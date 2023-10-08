import pprint
import shlex
import subprocess

from pydantic import BaseModel, Field

import make_agents as ma


class MessageUserArg(BaseModel):
    message: str = Field(description="Message to send user")


@ma.action
def message_user(arg: MessageUserArg):
    """Send the user a message, and get their response."""
    response = ""
    while response == "":
        response = input(arg.message + "\n>  ").strip()
    return response


@ma.action
def get_task_instructions():
    return "Your task is help the user with their computer system, using Bash, until they ask to end the chat. Please give the user only the relevant information."


class RunBashCommandArg(BaseModel):
    plan: str = Field(description="Plan what to run")
    command: str = Field(description="Command to run")


@ma.action
def run_bash_command(arg: RunBashCommandArg):
    """Record the users first and last name."""
    command = arg.command.strip()
    answer = input(
        f"Please validate the following bash command:\n`{command}`\nDo you want the agent to run it? (y/n)\n>  "
    ).lower()
    while not answer:
        if answer not in ["y", "n"]:
            answer = input("Please enter either 'y' or 'n'.\n>  ").lower()
    if answer == "n":
        return {"status": "user cancelled command"}
    result = subprocess.run(shlex.split(arg.command), capture_output=True, text=True)
    return {"stout": result.stdout, "stderr": result.stderr, "status": "command ran"}


# Define action graph
action_graph = {
    ma.Start: [get_task_instructions],
    get_task_instructions: [message_user],
    message_user: [message_user, run_bash_command, ma.End],
    run_bash_command: [message_user, run_bash_command],
}


def run(verbose: bool = False):
    # Run the agent
    print(
        "Initializing Bash Assistant...\n[WARNING] Commands suggested can be executed upon your confirmation.\nProceed with caution.\n"
    )
    for messages in ma.run_agent(action_graph):
        if verbose:
            pprint.pprint(messages[-1])
            print()
