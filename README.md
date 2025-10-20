# KOLI

An open-source AI Digital Human framework that enables developers to create lifelike, real-time virtual agents powered by multimodal AI. This project supports customized voice, facial expressions, and gestures tailored to user profiles—offering personalized and engaging human-AI interaction.

## ✨ Key Features

🎤 Voice Personalization:
Dynamically change the AI’s voice based on user preferences or personas. Choose from a wide range of voice tones and styles.

😃 Facial Expression Control:
Reflect emotions through expressive facial animations, synchronized with speech and conversation context.

🕺 Motion & Gesture Adaptation:
AI avatars can move and gesture naturally, adapting to dialogue and personality traits.

🧩 User Profile Driven:
Set different behaviors, emotions, and appearances by defining user personas (e.g., energetic assistant, calm guide, playful companion).

🔧 Easy Integration:
Designed with modular architecture and API-first principles to integrate with LLMs, speech-to-text, and text-to-speech engines.

## 📦 Use Cases

Virtual influencers & streamers

AI customer service agents

Interactive museum or exhibition guides

Digital companions for learning or mental wellness

## 📸 Demo

[![Watch the video](https://web3ai.s3.ap-southeast-2.amazonaws.com/20251020222650_5_4.png)](https://deepweb3.s3.ap-southeast-2.amazonaws.com/5b9ec5ae407468574c9eef109f7b540c.mp4)


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

Run backend server:

```shell
uv run backend/app.py
```

## 🤝 Contributions Welcome!

We’re building a creative, open digital human ecosystem. Feel free to open issues, request features, or contribute your own avatars and voice models.