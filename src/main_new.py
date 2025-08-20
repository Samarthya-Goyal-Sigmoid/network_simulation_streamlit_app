#!/usr/bin/env python3
"""
Main execution file for the Insight Agent system.
Modified from original main.py in LIft-Agent subfolder.
Uses single insight agent with multiple tools.
"""

import os
import pandas as pd
from langchain.schema import HumanMessage
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from utils import Agent, get_prompt_file, execute_analysis, get_graph
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import TypedDict, Annotated
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str
    chat_history: list  # Add memory field


class InsightAgentLift:
    def __init__(self, df_expenses, df_budget):
        """Initialize Insight Agent-Lift system with preloaded DataFrames."""
        self.df_expenses = df_expenses
        self.df_budget = df_budget

        file_path = os.getcwd()

        # Initialize LLM once
        self.llm = ChatOpenAI(
            model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0
        )

        # Load prompts for each dataset
        prompt_file_path_expenses = os.path.join(
            file_path, get_prompt_file("Expenses.csv")
        )
        with open(prompt_file_path_expenses, "r") as file:
            self.data_description_expenses = file.read().strip()

        prompt_file_path_budget = os.path.join(file_path, get_prompt_file("Budget.csv"))
        with open(prompt_file_path_budget, "r") as file:
            self.data_description_budget = file.read().strip()

        # Common agent prompt
        prompt_file_path_agent = os.path.join(
            file_path, "prompts/Insight_Agent_Prompt.txt"
        )
        with open(prompt_file_path_agent, "r") as file:
            prompt = file.read().strip()

        # Setup helper functions
        helper_functions = {"execute_analysis": execute_analysis}

        # Initialize single insight agent (for tool usage)
        self.insight_agent = Agent(
            llm=self.llm,
            prompt=prompt,
            tools=[],
            data_description=self.data_description_expenses
            + "\n\n"
            + self.data_description_budget,
            dataset=pd.concat(
                [self.df_expenses, self.df_budget], ignore_index=True
            ),  # Combined for reference
            helper_functions=helper_functions,
        )

        # Initialize memory (outside of functions)
        self.supervisor_memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # Create the workflow graph with the single insight agent
        self.graph = get_graph(
            self.df_expenses,
            self.df_budget,
            self.data_description_expenses,
            self.data_description_budget,
            prompt,
            self.supervisor_memory,  # Pass the memory instance
        )

        print("�� Insight Agent-Lift System initialized!")
        print(
            f"�� Available datasets: Expenses ({self.df_expenses.shape}), Budget ({self.df_budget.shape})"
        )

    def run_question(self, question):
        """Run a single question through the workflow."""
        print(f"\n🔍 Processing: {question}")
        print("⏳ Please wait...")

        state = {"messages": [HumanMessage(content=question)], "next": "supervisor"}

        counter = 0
        while state["next"] != "FINISH" and counter < 5:
            current_state = self.graph.nodes[state["next"]].invoke(state)
            state["messages"] = add_messages(
                state["messages"], current_state["messages"]
            )
            state["next"] = current_state["next"]
            counter += 1

        print(f"\n✅ Workflow completed in {counter} steps")

        # Display final answer after workflow finishes
        self.display_final_answer(state)

    def display_final_answer(self, state):
        """Display the final answer from the agent after workflow completion."""
        print("\n" + "=" * 60)
        print("🎯 FINAL ANSWER")
        print("=" * 60)

        # Find the last agent message (excluding supervisor messages)
        agent_messages = []
        for message in state["messages"]:
            if (
                hasattr(message, "name")
                and message.name
                and "supervisor" not in message.name.lower()
            ):
                agent_messages.append(message)

        if agent_messages:
            # Extract and display only the key parts
            final_agent_message = agent_messages[-1]
            print(f"🤖 Agent: {final_agent_message.name}")
            print("-" * 40)

            content = final_agent_message.content

            # Extract approach (if present)
            if "Analysis:" in content:
                approach_start = content.find("Analysis:")
                approach_end = content.find("Solution we got from this approach is:")
                if approach_end != -1:
                    approach = content[approach_start:approach_end].strip()
                    print("🔍 Approach:")
                    print(approach)
                    print()

            # Extract solution (if present)
            if "Solution we got from this approach is:" in content:
                solution_start = content.find("Solution we got from this approach is:")
                solution = content[solution_start:].strip()
                print("💡 Solution:")
                print(solution)
            else:
                # If no structured format, just show the content
                print("💡 Response:")
                print(content)

            print("-" * 40)
        else:
            # If no agent messages, show supervisor's final response
            supervisor_messages = [
                msg
                for msg in state["messages"]
                if hasattr(msg, "name")
                and msg.name
                and "supervisor" in msg.name.lower()
            ]
            if supervisor_messages:
                final_supervisor_message = supervisor_messages[-1]
                print(f"👑 Supervisor Response:")
                print("-" * 40)
                print(final_supervisor_message.content)
                print("-" * 40)
            else:
                print("❌ No final answer found in the workflow.")

        print("=" * 60)


if __name__ == "__main__":
    file_path = os.getcwd()

    # Load data (MODIFIED for new structure)
    df_expenses = pd.read_csv(os.path.join(file_path, "data/Expenses.csv"))
    df_budget = pd.read_csv(os.path.join(file_path, "data/Budget.csv"))
    # Handle budget data type conversion if needed
    if "2023 - Budget" in df_budget.columns:
        df_budget["2023 - Budget"] = (
            df_budget["2023 - Budget"].str.replace(",", "", regex=False).astype(int)
        )
    if "2024 - Budget" in df_budget.columns:
        df_budget["2024 - Budget"] = (
            df_budget["2024 - Budget"].str.replace(",", "", regex=False).astype(int)
        )

    # Create Insight Agent-Lift instance once
    insight_agent_lift = InsightAgentLift(df_expenses, df_budget)

    # Interactive loop
    print("�� Insight Agent-Lift System is ready!")
    print("🤖 Single Insight Agent with multiple tools!")
    print("🔧 Available tools: analyze_expense_data, analyze_budget_data")
    print("Type 'quit' to exit")
    print("-" * 50)

    while True:
        question = input("\n❓ Your question: ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break
        if question:
            insight_agent_lift.run_question(question)
