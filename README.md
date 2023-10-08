<!-- Copyright 2023 Sidney Radcliffe

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

<!-- Warning, README.md is autogenerated from README.ipynb, do not edit it directly -->


`pip install make_agents`
 
<p align="center">
  <img src="https://raw.githubusercontent.com/sradc/MakeAgents/master/README_files/make_agents_logo.jpg" width=256>
</p>

# MakeAgents 

MakeAgents is a micro framework for creating LLM-driven agents. It currently supports OpenAI's GPT chat models.

The MakeAgents paradigm is to define an agent's behaviour and capabilities entirely through **action functions**, and an **action graph**. 

TODO: put this in a "concepts" tutorial, with examples for each:

- Action functions: capabilities of the agent, that also shape its behaviour, (can be considered as part of the prompt).
- Action graph: defines what actions the agent has access to at a given point in time. Can shape the behaviour, and e.g. make sure that certain actions have been carried out before other actions.
- Execution is carried out using a generator, which makes it easy to see and vet what the agent is doing / about to do.


## Quickstart examples

### Example 1: A conversational agent for getting the user's name


```python
# TODO: simpler example here, just one instruction action, and one action

from IPython.display import display, Markdown

import json

from pydantic import BaseModel, Field

import make_agents as ma
```


```python
# Define action functions


@ma.action
def get_task_instructions():
    return "Your task is to get both the user's first and last name."


class MessageUserArg(BaseModel):
    question: str = Field(description="Question to ask user")


@ma.action
def message_user(arg: MessageUserArg):
    """Send the user a message, and get their response."""
    response = ""
    while response == "":
        response = input(arg.question).strip()
    return response


class LogNameArg(BaseModel):
    first_name: str = Field(description="User's first name")
    last_name: str = Field(description="User's last name")


@ma.action
def record_first_and_last_name(arg: LogNameArg):
    """Record the users first and last name."""
    return {"first_name": arg.first_name, "last_name": arg.last_name}


# Define action graph
action_graph = {
    ma.Start: [get_task_instructions],
    get_task_instructions: [message_user],
    message_user: [message_user, record_first_and_last_name],
}
display(Markdown("### Action graph"))
display(ma.bonus.draw_graph(action_graph))

# Run the agent
display(Markdown("### Agent activity"))
for messages in ma.run_agent(action_graph):
    ma.bonus.pretty_print(messages[-1])  # print most recent message on stack
print(f"Retrieved user_name: {json.loads(messages[-1]['content'])}")
```


### Action graph



    
![png](https://raw.githubusercontent.com/sradc/MakeAgents/master/README_files/README_3_1.png)
    



### Agent activity


    call `get_task_instructions`: <no arguments>
    
    `get_task_instructions` result: "Your task is to get both the user's first and last name."
    
    call `message_user`: {
      "question": "Could you please tell me your first name?"
    }
    
    `message_user` result: "It's Bill"
    
    call `select_next_func`: {
      "thought_process": "Now that I have the user's first name, I'll ask for their last name.",
      "next_function": "message_user"
    }
    
    `select_next_func` result: "message_user"
    
    call `message_user`: {
      "question": "Could you please tell me your last name?"
    }
    
    `message_user` result: "Sure, it's BoBaggins"
    
    call `select_next_func`: {
      "thought_process": "Now that I have both first and last name of the user, I'll store them using record_first_and_last_name function.",
      "next_function": "record_first_and_last_name"
    }
    
    `select_next_func` result: "record_first_and_last_name"
    
    call `record_first_and_last_name`: {
      "first_name": "Bill",
      "last_name": "BoBaggins"
    }
    
    `record_first_and_last_name` result: {"first_name": "Bill", "last_name": "BoBaggins"}
    
    Retrieved user_name: {'first_name': 'Bill', 'last_name': 'BoBaggins'}


### Notes:

Prompting has a big impact on the performance of the agent. The `llm_func` function names, Pydantic models and docstrings can all be considered part of the prompt.

### Contributing

- Please consider contributing cool examples of agents to `community_examples`
- For any ideas/comments/suggestions, create a GitHub issue (or comment in a relevant issue).
- For the development of the framework itself, the aspiration is take an "example driven" development approach. 
    I.e. find compelling examples where a feature / change would be helpful before adding it.

### Dev setup

- Clone the repo and `cd` into it
- Run `poetry install`
- Run `poetry run pre-commit install`

