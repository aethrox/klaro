<div align="center">
  <img src="assets/logo_transparent.png" alt="Klaro Logo" width="150"/>
  <h1>Klaro</h1>
  <strong>From Code to Clarity. Instantly.</strong>
</div>
<br />
<p align="center">
  <a href="#"><img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/aethrox/klaro/main.yml?style=for-the-badge"></a>
  <a href="#"><img alt="License" src="https://img.shields.io/github/license/aethrox/klaro?style=for-the-badge&color=blue"></a>
  <a href="#"><img alt="Python Version" src="https://img.shields.io/badge/python-3.9+-blue?style=for-the-badge&logo=python"></a>
</p>

## Overview

`Klaro` is an AI agent that autonomously reads your entire codebase, understands its logic, and generates clear, professional, and up-to-date technical documentation (such as README files, API references, and developer guides) with minimal human intervention.

### 💡 The Problem

Writing and maintaining documentation is a time-consuming, tedious, and often neglected task. This leads to technical debt, slow adaptation processes, and inefficiency.

### 🚀 The Solution

Writing and maintaining documentation is a time-consuming, tedious, and often neglected task. This leads to technical debt, slow adaptation processes, and inefficiency.

## ✨ Features (Planned)

* **Autonomous Code Analysis:** Reads the entire file tree, identifies key logic, and understands the relationships between components.
* **Multi-Format Output:** Generates professional Markdown (`README.md`), API references, and more.
* **AI-Powered Understanding:** Utilizes the most advanced LLMs (GPT-4o mini, Claude 3.5 Sonnet, etc.) via LangChain and LangGraph for deep understanding of the code.
* **Smart Model Steering:** Uses inexpensive models for simple tasks (file listing) and powerful models for complex analysis (code summarization) to optimize costs.
* **Style Guide Integration (RAG):** (Step 3) Learns from your existing documents to match the tone and style of your project.

## 🛠 Technology Stack

* **Core:** Python 3.9+
* **AI Framework:** LangChain & LangGraph
* **Models:** GPT-4o mini, Claude 3.5 Sonnet, Claude 3 Haiku (With Agentic Router)
* **Code Analysis:** `ast` (Abstract Syntax Tree), `GitPython`
* **Observability:** LangSmith

## 🚧 Status: Under Active Development

This project is currently in active development. You can refer to the project planning documents for the full roadmap.
*(I will upload a copy of these documents here later.)*

* `klaro_project_plan.md`
* `klaro_tech_docs_guide.md`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
