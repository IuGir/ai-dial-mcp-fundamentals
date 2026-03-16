import asyncio
import os

from agent.dial_client import DialClient
from agent.mcp_client import MCPClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT


# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts

async def main():
    mcp_server_url = "http://localhost:8005/mcp"

    async with MCPClient(mcp_server_url) as mcp_client:
        # Get available MCP resources and print them
        resources = await mcp_client.get_resources()
        print("Available MCP Resources:", [r.uri for r in resources] if resources else "none")

        # Get available MCP tools
        tools = await mcp_client.get_tools()
        print("Available MCP Tools:", [t["function"]["name"] for t in tools])

        # Create DialClient
        dial_client = DialClient(
            api_key=os.getenv("DIAL_API_KEY", ""),
            endpoint="https://ai-proxy.lab.epam.com",
            tools=tools,
            mcp_client=mcp_client,
        )

        # Build initial messages: system prompt + MCP prompts as user context
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ]
        prompts = await mcp_client.get_prompts()
        for prompt in prompts:
            content = await mcp_client.get_prompt(prompt.name)
            if content.strip():
                messages.append(Message(role=Role.USER, content=content))

        # Console chat loop
        print("\n--- User Management Agent ---")
        print("Type your message and press Enter. Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye.")
                break
            messages.append(Message(role=Role.USER, content=user_input))
            ai_message = await dial_client.get_completion(messages)
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
