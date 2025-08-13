import os
import pandas as pd
from langchain.schema import HumanMessage
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from utilities import Agent, get_prompt_file, execute_analysis, get_graph
import yaml


class AgentLift:
    def __init__(
        self,
        df_HY,
        df_CY,
        df_Budget,
        file_path,
        model_name="gpt-4o-mini",
    ):
        """Initialize Agent-Lift system with preloaded DataFrames."""
        self.df_HY = df_HY
        self.df_CY = df_CY
        self.df_Budget = df_Budget

        # Initialize LLM once
        try:
            self.llm = ChatOpenAI(
                model=model_name, api_key=os.getenv("OPENAI_API_KEY"), temperature=0
            )
        except Exception as e:
            print(e)
            return

        # Load prompts for each dataset
        prompt_file_path_hy = f"{file_path}/prompts/Prompt_HY.txt"
        with open(prompt_file_path_hy, "r") as file:
            self.data_description_HY = file.read().strip()

        prompt_file_path_cy = f"{file_path}/prompts/Prompt_CY.txt"
        with open(prompt_file_path_cy, "r") as file:
            self.data_description_CY = file.read().strip()

        prompt_file_path_budget = f"{file_path}/prompts/Prompt_Budget.txt"
        with open(prompt_file_path_budget, "r") as file:
            self.data_description_Budget = file.read().strip()

        # Common agent prompt
        prompt_file_path_agent = f"{file_path}/prompts/Agent_Prompt.txt"
        with open(prompt_file_path_agent, "r") as file:
            prompt = file.read().strip()

        # Setup helper functions
        helper_functions = {"execute_analysis": execute_analysis}

        # Initialize agents
        self.HYExpenseAgent = Agent(
            llm=self.llm,
            prompt=prompt,
            tools=[],
            data_description=self.data_description_HY,
            dataset=self.df_HY,
            helper_functions=helper_functions,
        )
        self.CYExpenseAgent = Agent(
            llm=self.llm,
            prompt=prompt,
            tools=[],
            data_description=self.data_description_CY,
            dataset=self.df_CY,
            helper_functions=helper_functions,
        )
        self.BudgetAgent = Agent(
            llm=self.llm,
            prompt=prompt,
            tools=[],
            data_description=self.data_description_Budget,
            dataset=self.df_Budget,
            helper_functions=helper_functions,
        )

        # Create the workflow graph with the initialized agents
        self.graph = get_graph(
            self.HYExpenseAgent, self.CYExpenseAgent, self.BudgetAgent
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

        print("=" * 60)
