# NFRGENAI Assistant

A prototype tool application that combines the **NFR (Non-Functional Requirements) Framework metamodel** with **Large Language Model** capabilities to help requirements engineers systematically elicit, classify, and explore non-functional requirements.

DOI: 10.5281/zenodo.18797266
---

## Overview

This prototype tool was developed for the paper: Eliciting Nonfunctional Requirements: an Ontology-driven Generative AI Approach.
Below is the tutorial on how to run the tool. 

## Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Runtime |
| **Ollama** | Latest | Local LLM inference server |

### Required Ollama Models

The application uses the following Ollama model. You must pull it before running the tool:

```bash
ollama pull llama3.1:8b
```

> **Note:** Ollama must be installed and its server must be running before you launch the application.
> Download Ollama from [https://ollama.com](https://ollama.com). After installation, the Ollama server typically starts automatically. You can verify by running `ollama list` in a terminal.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/nfr-elicitation-assistant.git
cd nfr-elicitation-assistant
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install PySide6 ollama
```

The full list of required packages:

| Package | Purpose |
|---|---|
| `PySide6` | GUI framework (Qt for Python) |
| `ollama` | Python client for the Ollama LLM server |

Standard library modules used (no install needed): `json`, `re`, `sys`, `os`, `inspect`, `threading`, `typing`, `dataclasses`, `enum`.

### 4. Verify Ollama Is Running

```bash
ollama list
```

You should see `llama3:8b` and `llama3.1:8b` in the output. If not, pull them as described above.

---

## Running the Application

From the project root directory:

```bash
python homescreen.py
```

The application will:

1. Open a PySide6 GUI window (the Home Screen)
2. Begin loading the metamodel, classifier, and LLM in the background
3. Display a status indicator once all components are ready

---

## Project Structure

```
.
├── homescreen.py            # Main entry point — launches the GUI
├── metamodel.py             # 3-level NFR Framework metamodel (47+ types)
├── nfr_queries.py           # Query API for the metamodel
├── classifier_v6.py         # Requirement classifier (FR/NFR + subtype)
├── menu_windows.py          # GUI windows for each menu action
├── menuLLM.py               # Lightweight LLM wrapper for menu responses
├── workflow.py              # Intent classification and query routing
├── prompt_templates.py      # Structured prompts for LLM actions
├── system_prompt.py         # System instructions for the MenuLLM
├── chat_interface.py        # chatbot-focused version
└── utils.py                 # Shared utilities (fuzzy matching, formatting)
```
## Experiment Data

Experiment 1: Prompt responses from LLM and tool in various tasks

Experiment 2: NFR specification documents from using tool + LLM and LLM alone, as well as student teams' SIGs

---

