 # Frameworkless Agent

 A small, framework-free agent architecture built with Python and the Google Gemini SDK. The project demonstrates the core mechanics of a tool-using agent without relying on LangChain, LangGraph, or another orchestration framework.

 The agent lets Gemini decide whether a request needs a registered Python tool. Python remains responsible for validation, required-parameter detection, tool execution, conversation state, and loop control.

 ## What It Does

 The agent supports two example tools:

 - `get_weather(city, days)` returns a sample weather forecast.
 - `calculate_sum(a, b)` returns the sum of two numbers.

 It can also answer requests that do not require a tool. When a tool needs information that the user did not provide, the agent asks a clarification question and keeps the pending conversation state for the next turn.

 ## Architecture

 ```text
 User input
	 |
	 v
 AgentState.messages  <------------------------------+
	 |                                                |
	 v                                                |
 call_llm()                                           |
 Gemini returns strict JSON                            |
	 |                                                |
	 v                                                |
 validate_llm_state()                                 |
	 |                                                |
	 v                                                |
 Python synchronizes AgentState                       |
	 |                                                |
	 +--> No tool required --------------------------> final answer
	 |
	 +--> Tool selected
			 |
			 v
	   get_missing_parameters()
			 |
	   +-----+-------------------+
	   |                         |
	   v                         v
 Missing values             All values present
	   |                         |
	   v                         v
 Ask Gemini for             execute_tool()
 clarification                  |
								 v
						 Tool result added to history
								 |
								 v
						 Gemini writes final answer
 ```

 ## Request Lifecycle

 1. The CLI appends the user's message to `AgentState.messages`.
 2. `call_llm()` sends the conversation and system prompt to Gemini.
 3. Gemini returns a JSON decision containing `decision`, `tool_required`, `tool_name`, `tool_params`, and `final_ans`.
 4. `validate_llm_state()` rejects malformed or contradictory responses.
 5. Python checks the selected tool's required parameters. The model does not decide whether parameters are missing.
 6. If values are missing, the runtime asks Gemini to produce a clarification question and returns it to the user.
 7. If all values are present, `execute_tool()` invokes the registered Python function.
 8. The tool result is appended to the conversation, and Gemini produces the final natural-language response.
 9. The loop allows up to 10 internal iterations per turn.

 ## Project Structure

 ```text
 frameworkless-agent/
 ├── main.py             # CLI, agent loop, state synchronization, orchestration
 ├── state.py            # AgentState and Gemini response validation
 ├── call_llm.py         # Gemini client, model configuration, JSON response parsing
 ├── prompt.py           # System prompt and agent behavior rules
 ├── tools.py            # Tool implementations, registry, parameter checks, execution
 ├── agent.ipynb         # Notebook experiments and exploratory examples
 ├── requirement.txt     # Python dependencies for this project
 ├── .env.example        # Environment variable template
 └── .env                # Local secrets; do not commit this file
 ```

 ## Requirements

 - Python 3.10 or newer
 - A Google Gemini API key
 - Internet access for Gemini API requests

 ## Setup

 From the `frameworkless-agent` directory:

 ```powershell
 python -m venv .venv
 .\.venv\Scripts\Activate.ps1
 pip install google-genai python-dotenv
 ```

 On macOS or Linux, activate the environment with:

 ```bash
 source .venv/bin/activate
 ```

 Create a `.env` file from the template and set your key:

 ```env
 GEMINI_API_KEY=your_gemini_api_key
 ```

 `python-dotenv` loads the value, and the Google GenAI client reads `GEMINI_API_KEY` from the environment. Keep `.env` private and use `.env.example` only as a template.

 ## Run

 ```powershell
 python main.py
 ```

 Enter requests at the `User:` prompt. Type `exit` to stop the application.

 Example interaction:

 ```text
 User: calculate the sum of 10 and 20
 ...
 FINAL ANSWER:
 The sum of 10 and 20 is 30.

 User: what is the weather in Pune?
 ...
 CLARIFICATION:
 How many forecast days would you like?

 User: 5 days
 ...
 FINAL ANSWER:
 The weather forecast for Pune is partly cloudy for 5 days.
 ```

 The weather implementation currently returns sample data. Replace it with a real weather API call before using it in production.

 ## Gemini Response Contract

 Every Gemini response must contain this JSON shape:

 ```json
 {
   "decision": "short explanation",
   "tool_required": true,
   "tool_name": "calculate_sum",
   "tool_params": {"a": 10, "b": 20},
   "final_ans": null
 }
 ```

 When no tool is needed, `tool_required` is `false`, `tool_name` is `null`, `tool_params` is `{}`, and `final_ans` contains the answer. When a tool is required, `final_ans` must be `null` until the tool result has been returned.

 ## Adding a Tool

 1. Implement a normal Python function in `tools.py`.
 2. Add it to the `TOOLS` registry with its description, parameter metadata, and required parameter names.
 3. Keep the parameter names in the registry aligned with the function signature.
 4. `TOOL_DESCRIPTION` is generated from the registry and automatically included in the system prompt.

 Example:

 ```python
 def multiply(a: float, b: float):
	 return {"a": a, "b": b, "result": a * b}
 ```

 Then register `multiply` using the same structure as `calculate_sum` in `tools.py`.

 ## Design Principles

 - **LLM decides, Python verifies:** Gemini selects a tool and extracts known values; Python validates the response and controls execution.
 - **No invented values:** The prompt instructs Gemini not to guess missing parameters.
 - **Explicit state:** `AgentState` makes decisions, parameters, results, and message history inspectable.
 - **Simple orchestration:** The complete agent loop is visible in `main.py` and can be extended without adopting a framework.
 - **Deterministic model configuration:** Gemini is called with temperature `0` and JSON response mode.

 ## Current Limitations

 - The example tools are synchronous and run in the same process as the CLI.
 - Tool outputs and agent state are printed directly to the console.
 - There is no persistence beyond the running process.
 - There is no authentication, authorization, timeout, retry policy, or sandbox for tools.
 - Tool parameter type conversion helpers exist in `tools.py`, but the current agent flow expects Gemini to return already structured JSON values.
 - The dependency file is currently empty; install `google-genai` and `python-dotenv` manually as shown above, or add pinned versions before deployment.

 ## Production Hardening

 Before deploying this architecture, add automated tests for response validation and tool execution, pin dependencies, validate tool arguments independently of the model, add API timeouts and retries, redact secrets from logs, and restrict which functions can be registered and executed.
