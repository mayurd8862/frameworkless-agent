import json
from typing import Any, Callable, Dict, Optional

import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()

# ============================================================
# AGENT STATE
# ============================================================

class AgentState:

    def __init__(self, user_query: str):

        self.user_query = user_query
        self.decision: str = ""
        self.tool_required: bool = False
        self.tool_name: Optional[str] = None
        self.tool_params: Dict[str, Any] = {}
        self.missing_params: list[str] = []
        self.tool_result: Optional[Any] = None
        self.final_ans: Optional[str] = None
        # Gemini conversation history
        self.messages: list[types.Content] = []


# ============================================================
# VALIDATE LLM STATE
# ============================================================

def validate_llm_state(
    result: Dict[str, Any]
) -> None:

    required_keys = {
        "decision",
        "tool_required",
        "tool_name",
        "tool_params",
        "final_ans"
    }

    missing_keys = (
        required_keys - result.keys()
    )

    if missing_keys:
        raise ValueError(
            f"Missing keys from LLM response: {missing_keys}"
        )

    if not isinstance(
        result["tool_required"],
        bool
    ):
        raise ValueError(
            "tool_required must be a boolean."
        )

    if not isinstance(
        result["tool_params"],
        dict
    ):
        raise ValueError(
            "tool_params must be a dictionary."
        )

    if result["tool_required"]:

        if not result["tool_name"]:
            raise ValueError(
                "tool_name is required when tool_required is true."
            )

        if result["final_ans"] is not None:
            raise ValueError(
                "final_ans must be null when a tool is required."
            )

    else:

        if result["tool_name"] is not None:
            raise ValueError(
                "tool_name must be null when no tool is required."
            )


# ============================================================
# PRINT STATE
# ============================================================

def print_state(state: AgentState):

    print("\n========== AGENT STATE ==========")

    print(
        json.dumps(
            {
                "decision": state.decision,
                "tool_required": state.tool_required,
                "tool_name": state.tool_name,
                "tool_params": state.tool_params,
                "missing_params": state.missing_params,
                "tool_result": state.tool_result,
                "final_ans": state.final_ans
            },
            indent=2,
            default=str
        )
    )

    print("=================================\n")
