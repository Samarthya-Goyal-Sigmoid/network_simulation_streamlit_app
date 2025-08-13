#!/usr/bin/env python3
"""
Main execution file for the Agent-Lift system.
Uses workflow graph approach like in agent-lift-system.
"""

import os
import re
import openai
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
import functools

# LangChain imports
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
)
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Load environment variables
from dotenv import load_dotenv
import yaml

load_dotenv()

# Setup directories
PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)


llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
# Initialize memory
memory = MemorySaver()


def get_prompt_file(data_source):
    """Return the appropriate prompt file based on the data source."""
    prompt_mapping = {
        "Historical_Expenses.csv": "prompts/prompt_HY.txt",
        "CY_Expense.csv": "prompts/prompt_CY.txt",
        "Budget.csv": "prompts/prompt_Budget.txt",
    }
    return prompt_mapping.get(data_source)


def extract_code_segments(response_text):
    """Extract code segments from the API response using regex."""
    segments = {}

    # Extract approach section
    approach_match = re.search(r"<approach>(.*?)</approach>", response_text, re.DOTALL)
    if approach_match:
        segments["approach"] = approach_match.group(1).strip()

    # Extract content between <code> tags
    code_match = re.search(r"<code>(.*?)</code>", response_text, re.DOTALL)
    if code_match:
        segments["code"] = code_match.group(1).strip()

    # Extract content between <chart> tags
    chart_match = re.search(r"<chart>(.*?)</chart>", response_text, re.DOTALL)
    if chart_match:
        segments["chart"] = chart_match.group(1).strip()

    # Extract content between <answer> tags
    answer_match = re.search(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
    if answer_match:
        segments["answer"] = answer_match.group(1).strip()

    return segments


def display_saved_plot(plot_path: str) -> None:
    """Loads and displays a saved plot from the given path."""
    if os.path.exists(plot_path):
        print(f"Plot saved at: {plot_path}")
    else:
        print(f"Plot not found at {plot_path}")


@tool
def execute_analysis(df, response_text):
    """Execute the extracted code segments on the provided dataframe and store formatted answer."""
    results = {
        "approach": None,
        "answer": None,
        "figure": None,
        "code": None,
        "chart_code": None,
    }

    try:
        # Extract code segments
        segments = extract_code_segments(response_text)
        print("Segments are:", segments)
        if not segments:
            print("No code segments found in the response")
            return results

        # Store the approach and raw code
        if "approach" in segments:
            results["approach"] = segments["approach"]
        if "code" in segments:
            results["code"] = segments["code"]
        if "chart" in segments:
            results["chart_code"] = segments["chart"]

        # Create a single namespace for all executions
        namespace = {"df": df, "pd": pd, "plt": plt, "sns": sns}

        # Execute analysis code and answer template
        if "code" in segments and "answer" in segments:
            # Properly dedent the code before execution
            code_lines = segments["code"].strip().split("\n")
            min_indent = float("inf")
            for line in code_lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)

            dedented_code = "\n".join(
                line[min_indent:] if line.strip() else "" for line in code_lines
            )

            # Combine code with answer template
            combined_code = f"""
{dedented_code}

# Format the answer template
answer_text = f'''{segments['answer']}'''
"""
            print("Combined Code:\n", combined_code)
            exec(combined_code, namespace)
            results["answer"] = namespace.get("answer_text")

        # Execute chart code if present
        if "chart" in segments and "No" not in segments["chart"]:
            chart_lines = segments["chart"].strip().split("\n")
            chart_lines = [x for x in chart_lines if "plt.show" not in x]

            min_indent = float("inf")
            for line in chart_lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)

            dedented_chart = "\n".join(
                line[min_indent:] if line.strip() else "" for line in chart_lines
            )

            plot_path = os.path.join(PLOT_DIR, f"plot_{uuid.uuid4().hex}.png")
            dedented_chart += f"\nplt.savefig('{plot_path}', bbox_inches='tight')"

            exec(dedented_chart, namespace)
            results["figure"] = plot_path

        return results

    except Exception as e:
        print(f"Error during execution: {str(e)}")
        return results


class Agent:
    def __init__(
        self, llm, prompt, tools, data_description, dataset, helper_functions=None
    ):
        self.llm = llm
        self.prompt = prompt
        self.tools = tools
        self.data_description = data_description
        self.dataset = dataset
        self.helper_functions = helper_functions or {}

    def add_helper_function(self, name, func):
        self.helper_functions[name] = func

    def run(self, question):
        prompt_temp = ChatPromptTemplate.from_messages(
            [
                ("system", self.prompt.strip()),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        result = self.llm.invoke(
            prompt_temp.invoke(
                {
                    "data_description": self.data_description,
                    "question": question,
                    "messages": [HumanMessage(content=question)],
                }
            )
        )

        return result

    def generate_response(self, question):
        result = self.run(question)
        response = self.helper_functions["execute_analysis"].invoke(
            {"df": self.dataset, "response_text": result.content}
        )
        return response

    def __repr__(self):
        return f"Agent(prompt={self.prompt}, data_description={self.data_description}, dataset={self.dataset.head()})"


# Define the supervisor role and members
role = """
You are a Multi-Agent Supervisor responsible for managing the conversation flow between multiple agents.
Your role is to analyze user queries and orchestrate responses efficiently by assigning tasks to the appropriate agents.

The Supervisor analyzes the conversation history, decides which agent should act next, and routes the conversation accordingly.
The Supervisor ensures smooth coordination and task completion by assigning specific roles to agents.

You also have the capability to answer simple questions directly without routing to specialized agents.
This improves efficiency and user experience for straightforward queries.

Use step-by-step reasoning (Chain-of-Thought) before deciding which agent should act next or if you should answer directly.
Upon receiving responses, reflect and dynamically adjust the approach using ReAct to ensure an optimal solution.

Please try to follow the below mentioned instructions:
1. Analyze the user's query and determine the best course of action.
2. For simple questions about the system, general information, or clarifications that don't require specialized data analysis, ANSWER DIRECTLY using the "SELF_RESPONSE" option.
3. For questions requiring data analysis, visualization, or specialized domain knowledge, select an appropriate agent from "Historical Expense Agent", "CY Expense Agent", or "Budget Agent".
4. If no further action is required, route the process to "FINISH".
5. Ensure smooth coordination between agents and track conversation progress.
"""

# Define the members
members = [
    {
        "agent_name": "Historical Expense Agent",
        "description": """Historical Expense Agent is responsible for analyzing past year's expense data to generate insights. 
         It handles tasks such as performing exploratory data analysis (EDA), calculating summary statistics, 
         identifying trends, comparing metrics across different dimensions (e.g., year, regions,Brand,Tier), and generating 
         visualizations for historic period.Suitable when user queries involve multi-year or pre-current-year expense patterns, comparisons, or trends.""",
    },
    {
        "agent_name": "CY Expense Agent",
        "description": """CY(Current Year) Expense Agent is responsible for analyzing current year expense data to generate insights. It handles tasks such as performing exploratory data analysis (EDA), calculating summary statistics, 
         identifying trends, comparing metrics across different dimensions (e.g., year, regions,Brand,Tier), and generating 
         visualizations specific to current year expense data. Suitable for queries focusing on in-year performance, approval statuses, or category/tier breakdowns for the current year.""",
    },
    {
        "agent_name": "Budget Agent",
        "description": """Budget Agent is responsible for analyzing budget-related data to generate insights. It Handles EDA, summary statistics, comparisons across tiers, and visualizations for allocated budgets.
        Suitable for queries about budget allocations, year-on-year budget comparisons, or proportional spending splits.""",
    },
    {
        "agent_name": "SELF_RESPONSE",
        "description": """Use this option when you can directly answer the user's question without specialized data analysis.
        This is appropriate for:
        1. General questions about the system's capabilities
        2. Clarification questions
        3. Simple information requests that don't require data analysis
        4. Explanations of concepts or terms
        5. Help with formulating questions for specialized agents
        When selecting this option, you should provide a complete, helpful response to the user's query.""",
    },
]

# Define the options for workers
options = ["FINISH"] + [mem["agent_name"] for mem in members]

# Generate members information for the prompt
members_info = "\n".join(
    [
        f"{member['agent_name']}: {re.sub(r'\s+', ' ', member['description'].replace('\n',' ')).strip()}"
        for member in members
    ]
)

final_prompt = (
    role
    + "\nHere is the information about the different agents you've:\n"
    + members_info
)
final_prompt += """
Think step-by-step before choosing the next agent or deciding to answer directly. 

Examples of when to use SELF_RESPONSE:
- "Can you explain what the Budget Agent does?"
- "What kind of data does this system analyze?"
- "I'm not sure how to phrase my question about current year expense"
- "What's the difference between Current and Historic Expences ?"

Examples of when to route to specialized agents:
- "Give me summary view of the Tier 1 expenses for Brazil for the past 2 years" (Historical Expense Agent)
- "What is the pull to push ratio for Current Year given the expense logged until now for brand Pepsi?" (CY Expense Agent)
- "What is the pull to push ratio for 2024 budget?" (Budget Agent)
- "For the current year, which expenses split are higher than the budget planned for Brand X?" (Both Budget and CY Expense Agent)

If needed, reflect on responses and adjust your approach and finally provide response.
"""

# Define the prompt with placeholders for variables
Supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", final_prompt.strip()),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Define the function for routing
function_def = {
    "name": "route",
    "description": "Select the next role based on reasoning.",
    "parameters": {
        "title": "routeSchema",
        "type": "object",
        "properties": {
            "thought_process": {
                "title": "Thought Process and Response",
                "type": "string",
                "description": "Step-by-step reasoning behind the decision and reply to the question.",
            },
            "next": {
                "title": "Next",
                "anyOf": [{"enum": options}],
                "description": "The next agent to call or SELF_RESPONSE if answering directly.",
            },
            "direct_response": {
                "title": "Direct Response",
                "type": "string",
                "description": "The direct response to provide to the user when SELF_RESPONSE is selected.",
            },
        },
        "required": ["thought_process", "next"],
    },
}

# Create the supervisor chain
supervisor_chain = (
    Supervisor_prompt
    | llm.bind_functions(functions=[function_def], function_call="route")
    | JsonOutputFunctionsParser()
)


# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str


# Define the supervisor node function
def supervisor_node(state: AgentState, chain=supervisor_chain):
    result = chain.invoke(state["messages"])
    if result["next"] == "SELF_RESPONSE":
        if "direct_response" in result:
            return_response = result.get("direct_response", "thought_process")
            return_response = (
                return_response
                if return_response != ""
                else result.get("thought_process", "")
            )
            return {
                "messages": [AIMessage(content=return_response, name="supervisor")],
                "next": "FINISH",
            }
        return {
            "messages": [
                AIMessage(
                    content=result.get(
                        "thought_process",
                        "I understand your question. Let me answer directly.",
                    ),
                    name="supervisor",
                )
            ],
            "next": "FINISH",
        }
    final_msg = f"Calling {result['next']}."

    return {
        "messages": [
            AIMessage(
                content=result.get(
                    "direct_response", result.get("thought_process", final_msg)
                ),
                name="supervisor",
            )
        ],
        "next": result["next"],
    }


# Define agent node functions
def agent_node(state, agent, name):
    result = agent(state)  # This result will be the list of messages
    return {"messages": result, "next": "supervisor"}


# Define specific agent functions - NOW THEY TAKE AGENTS AS PARAMETERS
def HYExpense_agent(state: AgentState, hy_agent):
    """Historical Expense Agent is responsible for analyzing past year's expense data to generate insights."""
    question = state["messages"][len(state["messages"]) - 2].content
    response = hy_agent.generate_response(question)

    if response["figure"]:
        display_saved_plot(response["figure"])

    print("Response is:", response)

    message = (
        (response.get("approach") or "")
        + "\nSolution we got from this approach is:\n"
        + (response.get("answer") or "")
    )

    return [HumanMessage(content=message, name="HY_Expense_Agent")]


def CYExpense_agent(state: AgentState, cy_agent):
    """CY(Current Year) Expense Agent is responsible for analyzing current year expense data to generate insights."""
    question = state["messages"][len(state["messages"]) - 2].content
    response = cy_agent.generate_response(question)

    if response["figure"]:
        display_saved_plot(response["figure"])

    message = (
        response["approach"]
        + "\nSolution we got from this approach is:\n"
        + response["answer"]
    )

    return [HumanMessage(content=message, name="CY_Expense_Agent")]


def Budget_agent(state: AgentState, budget_agent):
    """Budget Agent is responsible for analyzing budget-related data to generate insights."""
    question = state["messages"][len(state["messages"]) - 2].content
    response = budget_agent.generate_response(question)

    if response["figure"]:
        display_saved_plot(response["figure"])

    message = (
        response["approach"]
        + "\nSolution we got from this approach is:\n"
        + response["answer"]
    )

    return [HumanMessage(content=message, name="Budget_Agent")]


# Function to create the workflow graph with agents as parameters
def get_graph(hy_agent, cy_agent, budget_agent):
    """Create and return the workflow graph with the provided agents."""

    # Create agent nodes with agents as parameters using functools.partial
    HYExpense_agent_node = functools.partial(
        agent_node,
        agent=lambda state: HYExpense_agent(state, hy_agent),
        name="Historical Expense Agent",
    )
    CYExpense_agent_node = functools.partial(
        agent_node,
        agent=lambda state: CYExpense_agent(state, cy_agent),
        name="CY Expense Agent",
    )
    Budget_agent_node = functools.partial(
        agent_node,
        agent=lambda state: Budget_agent(state, budget_agent),
        name="Budget Agent",
    )
    supervisor_node_partial = functools.partial(supervisor_node, chain=supervisor_chain)

    # Build the workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("Historical Expense Agent", HYExpense_agent_node)
    workflow.add_node("CY Expense Agent", CYExpense_agent_node)
    workflow.add_node("Budget Agent", Budget_agent_node)
    workflow.add_node("supervisor", supervisor_node_partial)

    # Add edges
    for member in members:
        if member["agent_name"] != "SELF_RESPONSE":
            workflow.add_edge(member["agent_name"], "supervisor")

    # Add conditional edges
    conditional_map = {
        k["agent_name"]: k["agent_name"]
        for k in members
        if k["agent_name"] != "SELF_RESPONSE"
    }
    conditional_map["FINISH"] = END
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    workflow.set_entry_point("supervisor")

    # Compile and return the graph
    return workflow.compile(checkpointer=memory)
