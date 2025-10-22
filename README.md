<div align="center">
  <img src="assets/logo_transparent.png" alt="Klaro Logo" width="150"/>
  <h1>Klaro</h1>
  <strong>From Code to Clarity. Instantly.</strong>
</div>
<br />
<p align="center">
  <a href="https://github.com/aethrox/klaro/actions/workflows/main.yml"><img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/aethrox/klaro/main.yml?style=for-the-badge"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/github/license/aethrox/klaro?style=for-the-badge&color=blue"></a>
  <a href="#"><img alt="Python Version" src="https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python"></a>
</p>

## Overview
`Klaro` is an **autonomous AI agent** designed to solve the problem of neglected technical documentation. It works by autonomously navigating your codebase, performing deep logic analysis, and generating clear, professional, and up-to-date documentation (such as README files and API references) with minimal human intervention.

### 💡 The Problem
Writing and maintaining documentation is a time-consuming, tedious, and often neglected task. This common issue leads to accumulated technical debt, slow project onboarding for new team members, and overall project inefficiency.

### 🚀 The Solution
Klaro automates the entire documentation process. It employs an advanced **Pure Python ReAct loop** coupled with custom analysis tools and a **Retrieval-Augmented Generation (RAG) system** to ensure the generated documentation is not only accurate but also adheres to specified project style guides.

## ✨ Core Features (Completed & Planned)
* **Autonomous Code Analysis:** Implemented using **Python's AST (Abstract Syntax Tree)** to read the entire file tree, identify key logic (classes, functions), and extract structured data for analysis.
* **Style Guide Integration (RAG):** **(Completed in Stage 3)** Learns from your existing project style guides or reference documents, retrieving relevant context from a vector database to match the tone, structure, and style of the final documentation.
* **Multi-Tool Orchestration:** Uses a **Pure Python ReAct** (Reasoning and Acting) loop to dynamically plan steps, execute custom tools (`list_files`, `analyze_code`, `web_search`), and self-correct errors during the documentation process.
* **Multi-Format Output (Planned):** Generates professional Markdown (`README.md`), API references, and more.
* **Smart Model Steering (Planned):** Will utilize LangGraph for dynamic model routing (e.g., using GPT-4o mini for file listing and GPT-4o for complex analysis) to optimize API costs.

## 🛠 Technology Stack
* **Core:** Python 3.11+ (Current stable version)
* **AI Framework:** LangChain (Tools & Prompts) & **LangGraph (Agent Orchestration)**
* **Agent Core:** LangGraph State Machine (Stage 4 Completed)
* **Vector DB/RAG:** ChromaDB, OpenAI Embeddings
* **Code Analysis:** `ast` (Abstract Syntax Tree)

## 🚧 Status: Under Active Development
This project is currently in active development, having completed **Stages 2 (Agent Core)**, **3 (RAG/Quality)**, and **4 (LangGraph Integration)** of the roadmap.

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.