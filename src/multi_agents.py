# Import Libraries
import warnings

warnings.filterwarnings("ignore")
import functools
import traceback
import os
import pandas as pd
import json
from typing import TypedDict, Annotated
from typing import Dict, Any
import re
import copy

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# LangChain imports
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
)
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.output_parsers.structured import StructuredOutputParser, ResponseSchema
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import Tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.callbacks.base import BaseCallbackHandler

# Import Support Files
from supervisor import supervisor_prompt, supervisor_function_def
from helpers import execute_analysis
from insight_prompt import (
    insight_agent_prompt,
    insight_agent_expense_tool_prompt,
    insight_agent_budget_tool_prompt,
)


def extract_answer_content(text: str) -> str:
    """
    Extract content inside <answer>...</answer> tags.
    If no such tags exist, return the original text.
    """
    match = re.search(r"<answer>(.*?)</answer>", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


# ------------------------------
# Custom Callback for Step Tracing
# ------------------------------
class StepRecorder(BaseCallbackHandler):
    def __init__(self):
        self.steps = []

    def on_agent_action(self, action, **kwargs):
        self.steps.append(
            {
                "thought": action.log,
                "tool": action.tool,
                "tool_input": action.tool_input,
            }
        )

    def on_tool_end(self, output, **kwargs):
        if self.steps:
            self.steps[-1]["observation"] = output

    def on_agent_finish(self, finish, **kwargs):
        self.steps.append({"final_answer": finish.log})


class MultiAgentSystem:

    def __init__(
        self,
        model_name,
        api_key,
        expense_dataset,
        budget_dataset,
        plot_path,
    ):
        # Initialise model
        self.llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=0)
        # Datasets
        self.expense_dataset = expense_dataset
        self.budget_dataset = budget_dataset
        self.insight_agent_prompt = insight_agent_prompt.format(
            expense_df=expense_dataset.head().to_string(),
            budget_df=budget_dataset.head().to_string(),
        )
        self.insight_agent_expense_tool_prompt = (
            insight_agent_expense_tool_prompt.format(
                expense_df=expense_dataset.head().to_string()
            )
        )
        self.insight_agent_budget_tool_prompt = insight_agent_budget_tool_prompt.format(
            budget_df=budget_dataset.head().to_string()
        )
        # Execute analysis
        self.execute_analysis = execute_analysis
        # Plot path
        # Create folder if not available
        os.makedirs(plot_path, exist_ok=True)
        self.plot_path = plot_path
        # Initialise supervisor memory
        self.supervisor_memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        # Supervisor chain
        self.supervisor_chain = (
            supervisor_prompt
            | self.llm.bind_functions(
                functions=[supervisor_function_def], function_call="route"
            )
            | JsonOutputFunctionsParser()
        )
        # Initialise graph
        self.graph = self.get_workflow_graph()

    # Tools
    def expense_data_tool(self, query: str) -> Dict[str, Any]:
        # Prompt template
        prompt_temp = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.insight_agent_expense_tool_prompt,
                ),  # This contains the data description and the question
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        # Invoke LLM
        result = self.llm.invoke(
            prompt_temp.invoke({"messages": [HumanMessage(content=query)]})
        )
        # Response
        response = self.execute_analysis.invoke(
            {
                "df": self.expense_dataset,
                "response_text": result.content,
                "PLOT_DIR": self.plot_path,
            }
        )
        # Keys present in response (All these extracted from the llm response)
        # approach
        # answer
        # figure
        # code
        # chart_code
        return response

    def budget_data_tool(self, query: str) -> Dict[str, Any]:
        # Prompt template
        prompt_temp = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.insight_agent_budget_tool_prompt,
                ),  # This contains the data description and the question
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        # Invoke LLM
        result = self.llm.invoke(
            prompt_temp.invoke({"messages": [HumanMessage(content=query)]})
        )
        # Response
        response = self.execute_analysis.invoke(
            {
                "df": self.budget_dataset,
                "response_text": result.content,
                "PLOT_DIR": self.plot_path,
            }
        )
        # Keys present in response (All these extracted from the llm response)
        # approach
        # answer
        # figure
        # code
        # chart_code
        return response

    # Agent
    def supervisor_agent(self, query):

        # Invoke chain with enhanced context
        result = self.supervisor_chain.invoke(
            {
                "question": query,  # Human question
                "chat_history": [],  # Chat history placeholder
            }
        )

        if result["next"] == "SELF_RESPONSE":
            # Response provided by supervisor
            if "direct_response" in result:
                # Get the direct response, if not available get the thought process
                return_response = ""
                if result.get("direct_response"):
                    if result.get("direct_response") != "":
                        return_response = result["direct_response"]
                    else:
                        # Check for thought process
                        if result.get("thought_process"):
                            if result.get("thought_process") != "":
                                return_response = result["thought_process"]
                elif result.get("thought_process"):
                    if result.get("thought_process") != "":
                        return_response = result["thought_process"]

                # Direct response
                return {
                    "result": result,
                    "messages": [AIMessage(content=return_response, name="supervisor")],
                    "next": "FINISH",
                }
            else:
                # No direct response even if supervisor is tasked with answering the question
                return {
                    "result": result,
                    "messages": [
                        AIMessage(
                            content=result.get(
                                "thought_process",
                                "I do not understand your question. Please provide a different question.",
                            ),
                            name="supervisor",
                        )
                    ],
                    "next": "FINISH",
                }
        else:
            routing_message = result.get("thought_process", "N/A")
            return {
                "result": result,
                "messages": [AIMessage(content=routing_message, name="supervisor")],
                "next": result["next"],
            }

    # Agent
    def insight_agent(self):
        # Tools for this insight agent
        expense_tool = Tool.from_function(
            func=self.expense_data_tool,
            name="analyze_expense_data",
            description="Analyze expense data (both historical and current year) based on the question.",
        )
        budget_tool = Tool.from_function(
            func=self.budget_data_tool,
            name="analyze_budget_data",
            description="Analyze budget data based on the question.",
        )
        # Tools
        tools = [expense_tool, budget_tool]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.insight_agent_prompt),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Function to create the workflow graph
    def get_workflow_graph(
        self,
    ):

        # Supervisor Agent Node
        def supervisor_step(state: Dict[str, Any]):
            if "question" in state:
                result = self.supervisor_agent(state["question"])
            elif "output" in state:
                output_from_agent = extract_answer_content(state["output"])
                result = self.supervisor_agent(
                    f"Final answer by '{state['agent']}' agent: {output_from_agent}"
                )
            else:
                print(f"Invalid output received from agent {state['agent']}")
                result = copy.deepcopy(state)
            return result

        # Insight Agent Node
        def insight_step(state: Dict[str, Any]):
            question = None
            # Enriched question
            if state.get("enriched_question"):
                question = state["enriched_question"]
            else:
                if state.get("result"):
                    if state["result"].get("enriched_question"):
                        question = state["result"]["enriched_question"]
            # If question is not available
            if question is not None:
                agent = self.insight_agent()
                # Attach custom step recorder
                recorder = StepRecorder()
                result = agent.invoke(
                    {"input": f"{question}"},
                    config={"callbacks": [recorder]},
                )
                result["recorder_steps"] = recorder.steps
                result["agent"] = "Insight Agent"
                return result
            else:
                print("Insight Agent did not receive the enriched question")
                result["final_answer"] = (
                    "I did not receive the question from the Supervisor. I'm unable to provide the answer"
                )
                result["agent"] = "Insight Agent"
                return result

        # Build the workflow graph
        workflow = StateGraph(Dict[str, Any])
        workflow.add_node("Insight Agent", insight_step)
        workflow.add_node("supervisor", supervisor_step)

        # Workers always return to supervisor
        workflow.add_edge("Insight Agent", "supervisor")

        # Supervisor decides the next step
        # Add conditional edges
        conditional_map = {"Insight Agent": "Insight Agent", "FINISH": END}
        workflow.add_conditional_edges(
            "supervisor", lambda x: x["next"], conditional_map
        )
        workflow.set_entry_point("supervisor")

        # Use the passed memory instance
        return workflow.compile()
