"""Deep Agent setup using Azure OpenAI."""

import json
import os
import re

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from deepagents import create_deep_agent

from .parsers import extract_prompts
from .prompts import SYSTEM_PROMPT

load_dotenv()


def _build_model() -> AzureChatOpenAI:
    required = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_VERSION",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your Azure OpenAI credentials."
        )

    return AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        max_retries=6,
    )


def build_agent():
    model = _build_model()
    agent = create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


def evaluate_log(raw_text: str) -> dict:
    """Run the deep agent against the log content and return a parsed result dict."""
    prompts = extract_prompts(raw_text)
    prompt_block = "\n---\n".join(
        f"[Prompt {i+1}]\n{p}" for i, p in enumerate(prompts)
    )

    user_message = (
        f"Analyze the following {len(prompts)} user prompt(s) extracted from an AI coding assistant log.\n\n"
        f"{prompt_block}\n\n"
        "Return your evaluation as a JSON object following the schema in your instructions."
    )

    agent = build_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )

    last_message = result["messages"][-1].content

    # Extract JSON from the response (agent may wrap it in markdown fences)
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", last_message, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r"\{.*\}", last_message, re.DOTALL)
        json_str = json_match.group(0) if json_match else last_message

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Return a minimal structure if parsing fails
        return {
            "rating": None,
            "summary": last_message,
            "strengths": [],
            "weaknesses": [],
            "improvement_tips": [],
            "industry_benchmark": "",
        }
