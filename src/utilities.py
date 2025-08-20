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
from langchain.memory import ConversationBufferMemory

# Load environment variables
from dotenv import load_dotenv
import yaml

load_dotenv()

# Setup directories
PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)


llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

# Initialize memory (outside of functions)
supervisor_memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True
)


def get_prompt_file(data_source):
    """Return the appropriate prompt file based on the data source."""
    prompt_mapping = {
        "Expenses.csv": "prompts/Expense.txt",
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
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        result = self.llm.invoke(
            prompt_temp.invoke(
                {
                    "data_description": self.data_description,
                    "question": question,
                    "messages": [HumanMessage(content=question)],
                    "chat_history": supervisor_memory.chat_memory.messages,
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


# NEW: Tool-based functions for the insight agent
# FIXED: Tool-based functions for the insight agent - Remove @tool decorator
@tool
def analyze_expense_data(
    question: str, dataset: pd.DataFrame, data_description: str, prompt: str
) -> dict:
    """Analyze expense data (both historical and current year) based on the question."""
    # Create temporary agent for expense analysis
    temp_agent = Agent(
        llm=llm,
        prompt=prompt,  # Will be replaced with actual prompt
        tools=[],
        data_description=data_description,
        dataset=dataset,
        helper_functions={"execute_analysis": execute_analysis},
    )

    response = temp_agent.generate_response(question)
    return response


@tool
def analyze_budget_data(
    question: str, dataset: pd.DataFrame, data_description: str, prompt: str
) -> dict:
    """Analyze budget data based on the question."""

    # Create temporary agent for budget analysis
    temp_agent = Agent(
        llm=llm,
        prompt=prompt,  # Will be replaced with actual prompt
        tools=[],
        data_description=data_description,
        dataset=dataset,
        helper_functions={"execute_analysis": execute_analysis},
    )

    response = temp_agent.generate_response(question)
    return response


# Define the supervisor role and members (MODIFIED for single insight agent)
role = """
You are a Multi-Agent Supervisor responsible for managing the conversation flow.
Your role is to analyze user queries and orchestrate responses efficiently.

The Supervisor analyzes the conversation history, decides which agent should act next, and routes the conversation accordingly.
The Supervisor ensures smooth coordination and task completion.

You also have the capability to answer simple questions directly without routing to specialized agents.
This improves efficiency and user experience for straightforward queries.

Use step-by-step reasoning (Chain-of-Thought) before deciding which agent should act next or if you should answer directly.
Upon receiving responses, reflect and dynamically adjust the approach using ReAct to ensure an optimal solution.

Please try to follow the below mentioned instructions:
1. Analyze the user's query and determine the best course of action.
2. For simple questions about the system, general information, or clarifications that don't require specialized data analysis, ANSWER DIRECTLY using the "SELF_RESPONSE" option.
3. For questions requiring data analysis, visualization, or specialized domain knowledge, route to "Insight Agent".
4. If no further action is required, route the process to "FINISH".
5. Ensure smooth coordination and track conversation progress.
6. If you are not sure about the question or next step, you can ask the user for clarification.
7. Based on conversation history, you can answer directly or rephrase recent user questions and pass to the agent.
"""

# Define the members (MODIFIED for single insight agent)
members = [
    {
        "agent_name": "Insight Agent",
        "description": """Insight Agent is responsible for analyzing expense and budget data to generate insights. 
         It handles tasks such as performing exploratory data analysis (EDA), calculating summary statistics, 
         identifying trends, comparing metrics across different dimensions (e.g., year, regions, Brand, Tier), 
         generating visualizations, and providing comprehensive analysis using multiple tools at its disposal.
         The agent can analyze expense data (both historical and current year) and budget data, combining insights
         from multiple sources when needed for comprehensive analysis.""",
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
        6. Questions you can answer based on conversation history
        7. Rephrasing or clarifying recent user questions
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
- "Can you explain what the Insight Agent does?"
- "What kind of data does this system analyze?"
- "I'm not sure how to phrase my question about expenses"
- "What's the difference between expenses and budget?"
- "Can you rephrase my last question?"
- "Based on our conversation, what should I ask next?"

Examples of when to route to Insight Agent:
- "Give me summary view of the Tier 1 expenses for Brazil for the past 2 years"
- "What is the pull to push ratio for current year expenses for brand Pepsi?"
- "What is the pull to push ratio for 2024 budget?"
- "Compare current year expenses vs budget for Brand X"
- "Show me year-over-year expense trends"
- "Analyze budget allocation across different tiers"

If needed, reflect on responses and adjust your approach and finally provide response.
"""

# Define the prompt with placeholders for variables
Supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", final_prompt.strip()),
        MessagesPlaceholder(variable_name="chat_history"),
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
    chat_history: list  # Add memory field


# Define the supervisor node function
def supervisor_node(state: AgentState, chain=supervisor_chain):

    # Get conversation history from memory
    chat_history = supervisor_memory.chat_memory.messages

    # Invoke chain with enhanced context
    result = chain.invoke({"messages": state["messages"], "chat_history": chat_history})

    if result["next"] == "SELF_RESPONSE":
        if "direct_response" in result:
            return_response = result.get("direct_response", "thought_process")
            return_response = (
                return_response
                if return_response != ""
                else result.get("thought_process", "")
            )

            # Add response to memory
            supervisor_memory.chat_memory.add_ai_message(return_response)

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

    # Check if this is a response from the insight agent
    if any(msg.name == "Insight Agent" for msg in state["messages"]):
        # Insight agent has completed its work, end the workflow
        completion_message = "Analysis completed successfully."

        # Add completion to memory
        supervisor_memory.chat_memory.add_ai_message(completion_message)

        return {
            "messages": [AIMessage(content=completion_message, name="supervisor")],
            "next": "FINISH",
        }

    # Route to insight agent for the first time
    routing_message = f"Routing to Insight Agent for data analysis."

    # Add routing decision to memory
    supervisor_memory.chat_memory.add_ai_message(routing_message)

    return {
        "messages": [AIMessage(content=routing_message, name="supervisor")],
        "next": "Insight Agent",
    }


# MODIFIED: Single insight agent with two-task LLM approach
def insight_agent_workflow(
    state: AgentState,
    expense_dataset,
    budget_dataset,
    expense_description,
    budget_description,
    agent_prompt,
):
    """Single insight agent that uses one LLM for two tasks: tool selection and final response generation."""
    question = state["messages"][len(state["messages"]) - 2].content

    print(f"🔍 Insight Agent analyzing: {question}")

    # Add question to memory
    supervisor_memory.chat_memory.add_user_message(question)

    # TASK 1: LLM decides which tools to call based on user query
    tool_selection_prompt = f"""
    You are an intelligent tool selector. Analyze the user question and determine which tools are needed.
    
    User Question: {question}
    
    Available Tools:
    1. analyze_expense_data - For expense analysis, analyzing both historical and current year expense data. 
         Handles EDA, summary statistics, identifying trends, comparing metrics across different dimensions 
         (e.g., year, regions, Brand, Tier), and generating visualizations for expense patterns.
    2. analyze_budget_data - For budget data analysis, allocation, planning, budget vs actual comparisons. 
       Suitable for queries about budget allocations, year-on-year budget comparisons, or proportional spending splits.
    
    Return a JSON response with:
    {{
        "tools_needed": ["expense", "budget", "both"],
        "reasoning": "Explain why these specific tools are needed for this question",
        "execution_order": ["tool1", "tool2"] // The order in which tools should be executed
    }}
    
    Consider the full context and intent of the question. Be specific about which tools are needed.
    """

    print("🤖 LLM Task 1: Selecting tools...")
    tool_selection_response = llm.invoke(tool_selection_prompt)

    # Parse tool selection (simple parsing for demonstration)
    try:
        import json

        content = tool_selection_response.content
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end != 0:
            json_str = content[json_start:json_end]
            tool_decision = json.loads(json_str)
        else:
            # Fallback parsing
            tool_decision = {
                "tools_needed": ["expense"],
                "reasoning": "Default fallback",
                "execution_order": ["expense"],
            }
    except:
        # Fallback if JSON parsing fails
        tool_decision = {
            "tools_needed": ["expense"],
            "reasoning": "Default fallback",
            "execution_order": ["expense"],
        }

    print(f"🔧 Tool Selection: {tool_decision}")

    # Execute tools sequentially based on LLM decision
    tool_results = []

    for tool_name in tool_decision.get(
        "execution_order", tool_decision.get("tools_needed", ["expense"])
    ):
        print(f"⚙️ Executing {tool_name} tool...")

        if tool_name == "analyze_expense_data":
            # Call the tool using the invoke method
            result = analyze_expense_data.invoke(
                {
                    "question": question,
                    "dataset": expense_dataset,
                    "data_description": expense_description,
                    "prompt": agent_prompt,
                }
            )

        elif tool_name == "analyze_budget_data":
            result = analyze_budget_data.invoke(
                {
                    "question": question,
                    "dataset": budget_dataset,
                    "data_description": budget_description,
                    "prompt": agent_prompt,
                }
            )
        else:
            continue

        tool_results.append({"tool": tool_name, "result": result})

        # Display any generated plots
        additional_kwargs = {}
        if result.get("figure"):
            display_saved_plot(result["figure"])
            # Additional keyword arguments
            additional_kwargs["figure_path"] = result["figure"]

    print(
        f"📊 Tool execution completed. Generated results from {len(tool_results)} tools."
    )

    # TASK 2: LLM generates final response based on tool execution results
    final_response_prompt = f"""
    You are an intelligent response generator. Based on the user's question and the results from tool execution, generate a comprehensive final answer.
    
    User Question: {question}
    
    Tool Execution Results:
    {chr(10).join([f"Tool: {tr['tool']}\nApproach: {tr['result'].get('approach', 'N/A')}\nAnswer: {tr['result'].get('answer', 'N/A')}\n" for tr in tool_results])}
    
    Your task is to:
    1. Synthesize the information from all tool results
    2. Provide a clear, comprehensive answer to the user's question
    3. if image from any tool is generated, show it to the user with a short description of the image.
    4. Highlight key insights and findings
    5. Present the information in a structured, easy-to-understand format
    6. Do not include any external information or additional supporting text. Use only the tool’s response to generate the final answer.

    Generate a final response that directly answers the user's question using the tool results.
    """

    print("🤖 LLM Task 2: Generating final response...")
    final_response = llm.invoke(final_response_prompt)

    # Create the final message
    message = f"{final_response.content}"
    # Add response to memory
    supervisor_memory.chat_memory.add_ai_message(f"[Insight Agent] {message}")
    # Return with FINISH to end the workflow
    return {
        "messages": [
            HumanMessage(
                content=message,
                name="Insight Agent",
                additional_kwargs=additional_kwargs,
            )
        ],
        "next": "FINISH",  # Changed from "supervisor" to "FINISH"
    }


# Function to create the workflow graph (FIXED)
def get_graph(
    expense_dataset,
    budget_dataset,
    expense_description,
    budget_description,
    agent_prompt,
    memory_instance,
):
    """Create and return the workflow graph with a single insight agent."""

    # Create the insight agent node
    insight_agent_node = functools.partial(
        insight_agent_workflow,
        expense_dataset=expense_dataset,
        budget_dataset=budget_dataset,
        expense_description=expense_description,
        budget_description=budget_description,
        agent_prompt=agent_prompt,
    )
    supervisor_node_partial = functools.partial(supervisor_node, chain=supervisor_chain)

    # Build the workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("Insight Agent", insight_agent_node)
    workflow.add_node("supervisor", supervisor_node_partial)

    # Add edges
    workflow.add_edge("Insight Agent", "supervisor")

    # Add conditional edges
    conditional_map = {"Insight Agent": "Insight Agent", "FINISH": END}
    workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
    workflow.set_entry_point("supervisor")

    # Use the passed memory instance
    return workflow.compile(checkpointer=supervisor_memory)
