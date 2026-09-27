import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from state import AgentState, validate_llm_state, print_state
from tools import TOOLS, get_missing_parameters, execute_tool
from call_llm import call_llm

load_dotenv()


def run_agent_turn(state: AgentState) -> str:
    """
    Executes one agent turn using state.messages history.

    Gemini can be called multiple times internally:
    1. Decide whether a tool is required.
    2. If parameters are missing, generate a clarification question.
    3. After tool execution, generate the final answer.
    """

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        print(f"\n========== ITERATION {iteration} ==========")

        # ============================================================
        # STEP 1: CALL GEMINI
        # ============================================================

        result = call_llm(state.messages)

        # ============================================================
        # STEP 2: VALIDATE GEMINI OUTPUT
        # ============================================================

        validate_llm_state(result)

        # ============================================================
        # STEP 3: SYNCHRONIZE LLM STATE
        # ============================================================

        state.decision = result.get("decision")
        state.tool_required = result.get("tool_required", False)
        state.tool_name = result.get("tool_name")
        state.tool_params = result.get("tool_params", {})
        state.final_ans = result.get("final_ans")

        # ============================================================
        # STEP 4: COMPUTE MISSING PARAMETERS
        # Python is responsible for this.
        # ============================================================

        if state.tool_required and state.tool_name in TOOLS:

            state.missing_params = get_missing_parameters(
                state.tool_name,
                state.tool_params
            )

        else:
            state.missing_params = []

        # ============================================================
        # STEP 5: PRINT CURRENT STATE
        # ============================================================

        print_state(state)

        # ============================================================
        # STEP 6: NO TOOL REQUIRED
        # ============================================================

        if not state.tool_required:

            if not state.final_ans:
                raise ValueError(
                    "Gemini returned no final answer."
                )

            # Save Gemini response to conversation history
            state.messages.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(result)
                        )
                    ]
                )
            )

            print("\nFINAL ANSWER:")
            print(state.final_ans)

            return state.final_ans

        # ============================================================
        # STEP 7: VALIDATE TOOL
        # ============================================================

        if state.tool_name not in TOOLS:

            raise ValueError(
                f"Gemini selected an invalid tool: {state.tool_name}"
            )

        # ============================================================
        # STEP 8: MISSING PARAMETERS
        # ============================================================

        if state.missing_params:

            print(
                f"\nMissing parameters detected by runtime: "
                f"{state.missing_params}"
            )

            # Save the original tool decision
            state.messages.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(result)
                        )
                    ]
                )
            )

            # Ask Gemini to generate clarification question
            state.messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=(
                                f"The tool '{state.tool_name}' requires "
                                f"parameter(s) {state.missing_params} "
                                "which are currently missing.\n"
                                "Set tool_required to false and ask the user "
                                "to provide these values in final_ans."
                            )
                        )
                    ]
                )
            )

            # ------------------------------------------------------------
            # CALL GEMINI ONLY FOR CLARIFICATION
            # ------------------------------------------------------------

            clarification_result = call_llm(state.messages)

            validate_llm_state(clarification_result)

            clarification_question = clarification_result.get("final_ans")

            # Save Gemini clarification response to history
            state.messages.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(clarification_result)
                        )
                    ]
                )
            )

            print("\nCLARIFICATION:")
            print(clarification_question)

            return clarification_question

        # ============================================================
        # STEP 9: EXECUTE TOOL
        # ============================================================

        state.tool_result = execute_tool(
            state.tool_name,
            state.tool_params
        )

        print("\n[TOOL CALL]")
        print(f"Name: {state.tool_name}")
        print(
            f"Parameters: "
            f"{json.dumps(state.tool_params)}"
        )

        print("\n[TOOL RESULT]")
        print(
            json.dumps(
                state.tool_result,
                indent=2,
                ensure_ascii=False
            )
        )

        # ============================================================
        # STEP 10: SAVE TOOL CALL TO HISTORY
        # ============================================================

        state.messages.append(
            types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=json.dumps(result)
                    )
                ]
            )
        )

        # ============================================================
        # STEP 11: SEND TOOL RESULT BACK TO GEMINI
        # ============================================================

        tool_result_message = (
            f"Tool executed successfully.\n\n"
            f"Tool name: {state.tool_name}\n"
            f"Tool parameters: "
            f"{json.dumps(state.tool_params)}\n"
            f"Tool result: "
            f"{json.dumps(state.tool_result)}\n\n"
            "Generate the final natural-language answer using "
            "the tool result."
        )

        state.messages.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=tool_result_message
                    )
                ]
            )
        )

        # Continue loop.
        # Gemini will generate final answer.
        continue

    raise RuntimeError(
        f"Agent exceeded maximum iterations ({max_iterations})."
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print("Gemini Tool-Calling Agent")
    print("Type 'exit' to quit.\n")

    # Persistent state for the entire conversation
    session_state = AgentState(
        user_query=""
    )

    while True:

        user_query = input("\nUser: ").strip()

        if user_query.lower() == "exit":
            print("Agent stopped.")
            break

        if not user_query:
            continue

        try:

            # ========================================================
            # IMPORTANT:
            # DO NOT RESET tool_name/tool_params here.
            #
            # They may contain a pending tool call waiting for
            # missing parameters.
            # ========================================================

            session_state.user_query = user_query

            # --------------------------------------------------------
            # Add actual user message to conversation
            # --------------------------------------------------------

            session_state.messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=user_query
                        )
                    ]
                )
            )

            # --------------------------------------------------------
            # Execute agent turn
            # --------------------------------------------------------

            run_agent_turn(session_state)

        except Exception as error:

            print(
                f"\nAgent error: {error}\n"
            )