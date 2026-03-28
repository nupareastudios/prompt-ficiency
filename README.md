# Prompt-ficiency (Code-Assist Usage Evaluator)

Prompt-ficiency evaluates how effectively users are leveraging AI coding tools (such as GitHub Copilot, Claude Code, Cursor, etc.). It analyzes user prompt logs using a LangChain Deep Agent backed by Azure OpenAI and provides insightful feedback.

## Features

- **Rating**: Provides a rating out of 10 indicating usage proficiency.
- **Summary**: Summarizes the overall AI interactions.
- **Strengths & Weaknesses**: Identifies areas where the user did well and areas needing improvement.
- **Improvement Tips**: Generates actionable tips with "Before & After" examples showing how prompts could be better.
- **Industry Benchmarking**: Contextualizes user behavior with industry benchmarking.
- **Supports Multiple Formats**: Can process `.log`, `.txt`, `.doc`, `.docx`, and `.pdf` files.
- **JSON or Pretty Output**: Options to view formatted rich console output or raw JSON data.

## Setup

Create a virtual environment and activate it:
```bash
python -m venv venv
venv\Scripts\activate
pip install uv
uv pip install -r requirements.txt
```

## Configuration
This tool runs securely with Azure OpenAI. Create a `.env` file in the project's root directory (you can copy from `.env.example`) and fill in your Azure OpenAI credentials.

```env
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
AZURE_OPENAI_API_VERSION=""
```

You can verify your configuration at any time by running:
```bash
python main.py config
```

## Usage

You can use the CLI to evaluate log files.

```bash
# General evaluation of a raw text/log configuration
python main.py evaluate path/to/your/log_file.txt

# Detailed evaluation with before/after prompt improvement examples
python main.py evaluate path/to/log_file.txt --verbose

# Get raw JSON output
python main.py evaluate path/to/log_file.pdf --output json
```

### Analyzing Sample Logs

Sample files are available in the `sample_logs` directory to test the tool's effectiveness:
- `sample_logs/sample_claude_code.log`
- `sample_logs/sample_claude_code_session.log`
- `sample_logs/sample_copilot_session.txt`

Example:
```bash
python main.py evaluate sample_logs/sample_copilot_session.txt --verbose
```
