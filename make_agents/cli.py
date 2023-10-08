import click

from make_agents.agents import bash_assistant


@click.group()
def cli():
    pass


@click.group()
def run():
    """This is a group for running different agents"""


@run.command(name="bash_assistant")
@click.option("--verbose", "-v", is_flag=True, help="Will print all messages.")
def _bash_assistant(verbose):
    """This is a bash agent that will try to assist you with your system..."""
    bash_assistant.run(verbose=verbose)


cli.add_command(run)

if __name__ == "__main__":
    cli()
