import os
import pandas as pd
from langchain.schema import HumanMessage
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from utilities import Agent, get_prompt_file, execute_analysis, get_graph
import yaml
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import TypedDict, Annotated
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


class InsightAgentLift:
    def __init__(
        self,
        df_expenses,
        df_budget,
        file_path,
        model_name="gpt-4o-mini",
    ):
        """Initialize Agent-Lift system with preloaded DataFrames."""
        self.df_expenses = df_expenses
        self.df_budget = df_budget

        # Initialize LLM once
        try:
            self.llm = ChatOpenAI(
                model=model_name, api_key=os.getenv("OPENAI_API_KEY"), temperature=0
            )
        except Exception as e:
            print(e)
            return

        # Load prompts for each dataset
        prompt_file_path_cy = f"{file_path}/prompts/Prompt_Expense.txt"
        with open(prompt_file_path_cy, "r") as file:
            self.data_description_expenses = file.read().strip()

        prompt_file_path_budget = f"{file_path}/prompts/Prompt_Budget.txt"
        with open(prompt_file_path_budget, "r") as file:
            self.data_description_budget = file.read().strip()

        # Common agent prompt
        prompt_file_path_agent = f"{file_path}/prompts/Insight_Agent_Prompt.txt"
        with open(prompt_file_path_agent, "r") as file:
            prompt = file.read().strip()

        # Setup helper functions
        helper_functions = {"execute_analysis": execute_analysis}

        # Initialize agents
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

        # Create the workflow graph with the initialized agents
        self.graph = get_graph(
            self.df_expenses,
            self.df_budget,
            self.data_description_expenses,
            self.data_description_budget,
            prompt,
            self.supervisor_memory,  # Pass the memory instance
        )

        # print("🚀 Agent-Lift System initialized!")

    def run_question(self, question):
        """Run a single question through the workflow."""
        print(f"\n🔍 Processing: {question}")
        print("⏳ Please wait...")

        state = {"messages": [HumanMessage(content=question)], "next": "supervisor"}

        counter = 0
        while state["next"] != "FINISH" and counter < 10:
            current_state = self.graph.nodes[state["next"]].invoke(state)
            state["messages"] = add_messages(
                state["messages"], current_state["messages"]
            )
            state["next"] = current_state["next"]
            current_state["messages"][0].pretty_print()
            counter += 1

        print(f"\n✅ Workflow completed in {counter} steps")

        # Display final answer after workflow finishes
        status, response = self.display_final_answer(state)

    def display_final_answer(self, state):
        """Display the final answer from the agent after workflow completion."""
        print("\n" + "=" * 60)
        print("FINAL ANSWER")
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
            print(f" Agent: {final_agent_message.name}")
            content = final_agent_message.content

            # Extract solution (if present)
            if "Solution we got from this approach is:" in content:
                solution_start = content.find("Solution we got from this approach is:")
                solution = content[solution_start:].strip()
                print("💡 Solution:")
                print(solution)
                return "success", solution

            else:
                # If no structured format, just show the content
                print("💡 Response:")
                print(content)
                return "warning", content
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
                print(f"Supervisor Response:")
                print(final_supervisor_message.content)
                return "success", final_supervisor_message.content
            else:
                print("❌ No final answer found in the workflow.")
                return "danger", "❌ No final answer found in the workflow."
