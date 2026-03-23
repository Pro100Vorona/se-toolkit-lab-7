"""LLM client for tool calling.

Sends user messages + tool definitions to the LLM, executes tool calls,
feeds results back, and returns the final answer.
"""

import json
import httpx
from typing import Any


class LLMClient:
    """Client for LLM tool calling.
    
    Uses OpenAI-compatible API format for tool definitions and calls.
    """
    
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def chat_with_tools(
        self,
        user_message: str,
        tools: list[dict[str, Any]],
        system_prompt: str,
        execute_tool: callable,
    ) -> str:
        """Chat with the LLM, executing tool calls and returning the final answer.
        
        Args:
            user_message: The user's input message
            tools: List of tool definitions (OpenAI format)
            system_prompt: System prompt for the LLM
            execute_tool: Async function that takes (tool_name, args) and returns result
        
        Returns:
            The final answer from the LLM
        """
        client = await self._get_client()
        
        # Build conversation messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call the LLM
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                },
            )
            
            if response.status_code != 200:
                return f"LLM error: HTTP {response.status_code} {response.text}"
            
            data = response.json()
            choice = data["choices"][0]
            assistant_message = choice["message"]
            
            # Add assistant message to conversation
            messages.append(assistant_message)
            
            # Check if there are tool calls
            tool_calls = assistant_message.get("tool_calls", [])
            
            if not tool_calls:
                # No tool calls - LLM is done, return the answer
                return assistant_message.get("content", "No response")
            
            # Execute each tool call
            for tool_call in tool_calls:
                function = tool_call["function"]
                tool_name = function["name"]
                tool_args = json.loads(function["arguments"])
                
                print(f"[tool] LLM called: {tool_name}({tool_args})", file=__import__("sys").stderr)
                
                # Execute the tool
                try:
                    result = await execute_tool(tool_name, tool_args)
                    print(f"[tool] Result: {str(result)[:100]}", file=__import__("sys").stderr)
                except Exception as e:
                    result = f"Error: {e}"
                    print(f"[tool] Error: {e}", file=__import__("sys").stderr)
                
                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })
            
            print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=__import__("sys").stderr)
        
        return "Reached maximum iterations. Please try again."
