# Import Libraries
import warnings

warnings.filterwarnings("ignore")
import re
import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import traceback

# Langchain Imports
from langchain_core.tools import tool


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
def execute_analysis(df, response_text, PLOT_DIR):
    """Execute the extracted code segments on the provided dataframe and store formatted answer."""
    results = {
        "approach": None,
        "answer": None,
        "figure": None,
        "code": None,
        "chart_code": None,
    }

    try:
        print("Response Text:")
        print(response_text)
        print(110 * "-")
        # Extract code segments
        segments = extract_code_segments(response_text)
        print("Segments:")
        print(segments)
        print(110 * "-")
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
        print(f"Error during execution: {str(e)} \n{traceback.format_exc()}")
        return results
