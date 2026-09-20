from deepagents import create_deep_agent

from models import model

agent = create_deep_agent(model=model)

result = agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]})

print(result["messages"][-1].text)

"""
An **LLM** is a **Large Language Model**—an AI system trained on vast amounts of text to understand and generate human-like language.

LLMs can:

- Answer questions
- Summarize and translate text
- Write or edit content
- Generate and explain code
- Hold conversations

They work by predicting what text is likely to come next based on patterns learned during training. They don’t “think” or understand exactly like humans, and they can sometimes produce incorrect information.
"""