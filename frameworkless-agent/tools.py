import json
from typing import Any, Callable, Dict, Optional

import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()

# ============================================================
# TOOLS
# ============================================================

def get_weather(city: str, days: int):
    """
    Example tool.
    Replace this with your actual Python function/API.
    """

    return {
        "city": city,
        "days": days,
        "temperature": "28°C",
        "condition": "Partly cloudy",
        "forecast": f"Weather forecast for {days} days in {city}"
    }


def calculate_sum(a: float, b: float):
    """
    Another example tool.
    """

    return {
        "a": a,
        "b": b,
        "result": a + b
    }




# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = {
    "get_weather": {
        "function": get_weather,
        "description": "Get weather information for a city.",
        "parameters": {
            "city": {
                "type": "string",
                "description": "Name of the city"
            },
            "days": {
                "type": "integer",
                "description": "Number of forecast days"
            }
        },
        "required": ["city", "days"]
    },

    "calculate_sum": {
        "function": calculate_sum,
        "description": "Calculate the sum of two numbers.",
        "parameters": {
            "a": {
                "type": "number",
                "description": "First number"
            },
            "b": {
                "type": "number",
                "description": "Second number"
            }
        },
        "required": ["a", "b"]
    }
}


# ============================================================
# DYNAMIC TOOL DESCRIPTION
# ============================================================

def build_tool_description(
    tools: Dict[str, Dict[str, Any]]
) -> str:

    descriptions = []

    for name, tool in tools.items():

        parameter_lines = []

        for param_name, param_info in tool["parameters"].items():

            required = (
                param_name in tool["required"]
            )

            required_text = (
                "required"
                if required
                else "optional"
            )

            parameter_lines.append(
                f"- {param_name}: "
                f"{param_info['type']}, "
                f"{required_text}. "
                f"{param_info['description']}"
            )

        descriptions.append(
            f"""
Tool name: {name}

Description:
{tool['description']}

Parameters:
{chr(10).join(parameter_lines)}
"""
        )

    return "\n".join(descriptions)


# ============================================================
# MISSING PARAMETER DETECTION
# ============================================================

def get_missing_parameters(
    tool_name: str,
    collected_params: Dict[str, Any]
) -> list[str]:

    tool = TOOLS[tool_name]

    missing = []

    for param in tool["required"]:

        if (
            param not in collected_params
            or collected_params[param] is None
        ):
            missing.append(param)

    return missing


# ============================================================
# MISSING PARAMETER DETECTION
# ============================================================

def get_missing_parameters(
    tool_name: str,
    collected_params: Dict[str, Any]
) -> list[str]:

    tool = TOOLS[tool_name]

    missing = []

    for param in tool["required"]:

        if (
            param not in collected_params
            or collected_params[param] is None
        ):
            missing.append(param)

    return missing



# ============================================================
# ASK USER FOR MISSING PARAMETERS
# ============================================================

def ask_for_missing_parameters(
    tool_name: str,
    missing_params: list[str]
) -> Dict[str, Any]:

    tool = TOOLS[tool_name]

    collected_values = {}

    for param_name in missing_params:

        param_info = tool["parameters"][param_name]

        while True:

            user_input = input(
                f"Please provide '{param_name}' "
                f"({param_info['description']}): "
            )

            try:

                converted_value = convert_parameter(
                    user_input,
                    param_info["type"]
                )

                collected_values[param_name] = (
                    converted_value
                )

                break

            except ValueError:

                print(
                    f"Invalid value. "
                    f"Expected type: {param_info['type']}."
                )

    return collected_values


# ============================================================
# PARAMETER TYPE CONVERSION
# ============================================================

def convert_parameter(
    value: str,
    param_type: str
) -> Any:

    value = value.strip()

    if param_type == "integer":
        return int(value)

    if param_type == "number":
        return float(value)

    if param_type == "boolean":
        value_lower = value.lower()

        if value_lower in ["true", "yes", "y"]:
            return True

        if value_lower in ["false", "no", "n"]:
            return False

        raise ValueError(
            "Please enter true/false."
        )

    return value


# ============================================================
# EXECUTE PYTHON TOOL
# ============================================================

def execute_tool(
    tool_name: str,
    tool_params: Dict[str, Any]
) -> Any:

    if tool_name not in TOOLS:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    tool = TOOLS[tool_name]

    function: Callable = tool["function"]

    print("\n[TOOL CALL]")
    print(f"Name: {tool_name}")
    print(
        f"Parameters: "
        f"{json.dumps(tool_params)}"
    )

    result = function(**tool_params)

    print("\n[TOOL RESULT]")
    print(json.dumps(result, indent=2))

    return result


TOOL_DESCRIPTION = build_tool_description(TOOLS)