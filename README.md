# agentServer

## 🚀 Quickstart

Clone the repository and activate a virtual environment:

```shell
git clone https://github.com/calixeth/agentServer
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Install dependencies:

```shell
uv pip install -r pyproject.toml
```

Set up your .env file to customize the environment variables (for model api key...):

```shell
cp .env.example .env
```

Run server

```shell
uv run backend/app.py
```

