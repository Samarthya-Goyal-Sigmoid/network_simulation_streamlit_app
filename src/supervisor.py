# Import Libraries
import re

# LangChain imports
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


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
supervisor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", final_prompt.strip()),  # System message
        MessagesPlaceholder(variable_name="chat_history"),  # Chat history placeholder
        ("human", "{question}"),  # Human question placeholder
    ]
)

# Define the function for routing
supervisor_function_def = {
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
            "enriched_question": {
                "title": "Enriched Question",
                "type": "string",
                "description": "By considering all the previous messages or conversation and the next agent to be called, frame a single line question. Keep track of these parameters while summarising: Region, Country, Year, Month, Category, Brand, Data Type, Tier 1, Tier 2, Tier 3, Expense, Status, Pep (%), Budget",
            },
        },
    },
    "required": ["thought_process", "next", "enriched_question"],
}
