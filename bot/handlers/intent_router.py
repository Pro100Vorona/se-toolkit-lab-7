"""Intent router - uses LLM to decide which tools to call.

This module defines all backend endpoints as LLM tools and routes
user messages to the appropriate tool calls.
"""

import json
from services.lms_client import LMSClient
from services.llm_client import LLMClient
from config import load_config


# System prompt for the LLM
SYSTEM_PROMPT = """You are a helpful assistant for a Learning Management System (LMS).
You have access to tools that fetch data about labs, students, scores, and analytics.

When a user asks a question:
1. Think about what data they need
2. Call the appropriate tool(s) to get that data
3. Use the tool results to answer their question

If the user's message is unclear or gibberish, politely explain what you can help with.
If the user greets you, respond warmly and mention you can help with lab data.

Always be specific and include numbers from the data when available."""


# Tool definitions for all 9 backend endpoints
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks. Use this to see what labs are available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get list of enrolled students and their groups.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets) for a specific lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average pass rates and attempt counts for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submission timeline (submissions per day) for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group performance and student counts for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                    "limit": {"type": "integer", "description": "Number of top learners to return, e.g. 5"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL pipeline sync to refresh data from autochecker.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


async def execute_tool(tool_name: str, args: dict, lms_client: LMSClient) -> dict:
    """Execute a tool call and return the result.
    
    Args:
        tool_name: Name of the tool to call
        args: Arguments for the tool
        lms_client: The LMS client to use
    
    Returns:
        The tool result as a dict
    """
    if tool_name == "get_items":
        return await lms_client.get_labs_raw()
    elif tool_name == "get_learners":
        return await lms_client.get_learners()
    elif tool_name == "get_scores":
        return await lms_client.get_scores_analytics(args.get("lab", ""))
    elif tool_name == "get_pass_rates":
        return await lms_client.get_pass_rates(args.get("lab", ""))
    elif tool_name == "get_timeline":
        return await lms_client.get_timeline(args.get("lab", ""))
    elif tool_name == "get_groups":
        return await lms_client.get_groups(args.get("lab", ""))
    elif tool_name == "get_top_learners":
        return await lms_client.get_top_learners(args.get("lab", ""), args.get("limit", 5))
    elif tool_name == "get_completion_rate":
        return await lms_client.get_completion_rate(args.get("lab", ""))
    elif tool_name == "trigger_sync":
        return await lms_client.trigger_sync()
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def route_intent(user_message: str) -> str:
    """Route a user message to the appropriate tool(s) and return the answer.
    
    Args:
        user_message: The user's input message
    
    Returns:
        The final answer from the LLM
    """
    config = load_config()
    
    lms_client = LMSClient(config["LMS_API_URL"], config["LMS_API_KEY"])
    llm_client = LLMClient(
        config.get("LLM_API_BASE_URL", "http://localhost:42005/v1"),
        config.get("LLM_API_KEY", ""),
        config.get("LLM_API_MODEL", "coder-model"),
    )
    
    try:
        # Define the tool executor
        async def execute_tool_wrapper(tool_name: str, args: dict):
            return await execute_tool(tool_name, args, lms_client)
        
        # Call the LLM with tools
        response = await llm_client.chat_with_tools(
            user_message=user_message,
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            execute_tool=execute_tool_wrapper,
        )
        
        return response
    finally:
        await lms_client.close()
        await llm_client.close()

# Task 3: Intent Routing with LLM tool calling
