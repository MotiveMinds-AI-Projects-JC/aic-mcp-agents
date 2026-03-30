# 🤖 SAP MCP Server — Pegged Requirements & GL Prediction Agent

> An AI-powered MCP (Model Context Protocol) server that connects **SAP S/4HANA** data with a **Large Language Model (GPT-4o)** to answer supply chain queries and predict General Ledger accounts — all through natural language.

---

## 📖 Table of Contents

- [What Does This Project Do?](#-what-does-this-project-do)
- [Who Is This For?](#-who-is-this-for)
- [Key Concepts Explained Simply](#-key-concepts-explained-simply)
- [Architecture Overview](#-architecture-overview)
- [File-by-File Breakdown](#-file-by-file-breakdown)
- [Data Flow Walkthrough](#-data-flow-walkthrough)
- [The Three Exposed Tools](#-the-three-exposed-tools)
- [Setup & Configuration](#-setup--configuration)
- [Environment Variables](#-environment-variables)
- [How to Run](#-how-to-run)
- [Example Queries](#-example-queries)
- [Deployment: Local vs Cloud Foundry](#-deployment-local-vs-cloud-foundry)

---

## 🧐 What Does This Project Do?

This project is a **smart server** that sits between an AI assistant (like SAP Joule) and your SAP system. It does three main things:

1. **Answers supply chain questions** — Given a Planned Order number or a Purchase Requisition number, it automatically fetches related supply/demand data from SAP and returns it in a neat table.
2. **Answers company policy questions** — Using a RAG (AI-powered knowledge base) system, it finds relevant answers from internal documents.
3. **Predicts GL (General Ledger) accounts** — Given financial document details, it uses a machine learning model to suggest which GL account to post to.

Think of it as a **smart middleman** — it takes a plain English question, figures out which SAP API to call, calls it, and gives back a clean, formatted answer.

---

## 👥 Who Is This For?

- **SAP Consultants** building AI-assisted workflows
- **Developers** integrating LLMs with enterprise ERP systems
- **Business Analysts** who want to understand how AI connects to SAP data
- **Beginners** curious about how real-world AI agents work in production

No prior Python experience is required to *understand* this README. Basic familiarity helps to *run* it.

---

## 🧱 Key Concepts Explained Simply

Before diving in, here's a quick glossary of terms you'll encounter:

| Term | Plain English Explanation |
|------|--------------------------|
| **MCP Server** | A standard way for AI assistants to call external tools/functions. Think of it as a plugin system for AI. |
| **LLM (Large Language Model)** | The AI brain (GPT-4o here) that understands your question and decides which tool to use. |
| **Agent** | An AI that can use tools autonomously — it reads your question, picks the right tool, calls it, and formats the answer. |
| **SAP S/4HANA** | SAP's enterprise ERP system that holds your company's supply chain, finance, and operational data. |
| **Pegged Requirements** | In supply chain, this means: "which demand (sales order, production order) is linked to which supply (planned order, purchase req)?" |
| **Planned Order (PO)** | A system-generated proposal in SAP to produce or procure a material. |
| **Purchase Requisition (PR)** | A request to purchase something — before it becomes a real purchase order. |
| **MRP (Material Requirements Planning)** | SAP's engine that calculates what needs to be produced/purchased and when. |
| **RAG (Retrieval-Augmented Generation)** | An AI technique where the model first *retrieves* relevant documents, then *generates* an answer based on them. |
| **GL (General Ledger)** | The master record of all financial transactions in a company. |
| **DAR (Data Attribute Recommendation)** | SAP's ML service for making predictions on structured data (used here for GL prediction). |
| **Gen AI Hub** | SAP's platform for accessing LLMs like GPT-4o in a managed, enterprise-safe way. |
| **Cloud Foundry** | A cloud platform (used by SAP BTP) to deploy and run applications. |
| **Environment Variables** | Secret config values (like passwords and URLs) stored outside the code for security. |

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Assistant                              │
│                    (e.g. SAP Joule / Claude)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │  Sends natural language query
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server  (main.py)                        │
│                                                                  │
│   Exposes 3 tools over HTTP:                                     │
│   ┌──────────────────┐ ┌───────────────────┐ ┌───────────────┐  │
│   │  echo()          │ │get_company_       │ │get_gl_        │  │
│   │  (Agent Tool)    │ │policies()         │ │prediction()   │  │
│   └────────┬─────────┘ └────────┬──────────┘ └──────┬────────┘  │
└────────────┼────────────────────┼───────────────────┼───────────┘
             │                    │                   │
             ▼                    ▼                   ▼
┌────────────────────┐  ┌─────────────────┐  ┌────────────────────┐
│   Agent (agent.py) │  │  RAG API        │  │  SAP DAR           │
│                    │  │  (resource.py)  │  │  ML Service        │
│  GPT-4o (via       │  │                 │  │  (tools.py)        │
│  Gen AI Hub)       │  │  External       │  │                    │
│        +           │  │  HTTP endpoint  │  │  Predicts GL       │
│  3 MRP Tools       │  │                 │  │  account           │
└────────┬───────────┘  └─────────────────┘  └────────────────────┘
         │
         │  Calls the right tool based on input type
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SAP S/4HANA APIs  (tools.py)                │
│                                                                  │
│  ┌────────────────────────┐   ┌──────────────────────────────┐  │
│  │ Planned Order API      │   │ Purchase Requisition API     │  │
│  │ /api_plannedorder/...  │   │ /api_purchaserequisition_2/  │  │
│  └────────────┬───────────┘   └─────────────┬────────────────┘  │
│               │                             │                    │
│               └──────────────┬──────────────┘                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │  Pegged Requirements API      │                  │
│              │  /zmm_sb_joule_pegged/...     │                  │
│              └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### In simple terms:
1. An AI assistant sends a question to this server
2. The server routes it to the right "tool" (function)
3. The tool calls SAP APIs to fetch real data
4. The AI formats the data into a clean Markdown table
5. The answer goes back to the user

---

## 📁 File-by-File Breakdown

```
project/
│
├── main.py        ← Entry point: starts the server, registers tools
├── agent.py       ← AI brain: GPT-4o + tool selection logic
├── tools.py       ← SAP API callers + GL prediction
├── resource.py    ← RAG system connector
├── config.py      ← Configuration & secrets loader
├── env.example    ← Template showing what secrets are needed
└── README.md      ← This file
```

---

### `main.py` — The Server Entry Point

**What it does:** Starts an HTTP server and registers three callable "tools" that AI assistants can invoke.

Think of this as the **front door** of the application. When an AI assistant wants to do something, it knocks on this door and asks for one of three services.

```
main.py registers:
├── echo()               → Routes to the AI Agent (for MRP/pegged requirements)
├── get_company_policies() → Routes to the RAG system (for policy questions)
└── get_gl_prediction()  → Routes to the DAR ML model (for GL account prediction)
```

The server runs on port `8000` by default (configurable via the `PORT` environment variable) and listens on all network interfaces (`0.0.0.0`).

---

### `agent.py` — The AI Brain

**What it does:** Creates an AI agent powered by GPT-4o that reads a user query, decides which SAP tool to call, and returns a formatted Markdown table.

This is the most "intelligent" part of the system. Here's what happens step by step:

```
User query arrives
       │
       ▼
GPT-4o reads the query + system prompt
       │
       ├── Is it a Planned Order number?     → calls get_mrp_plannedorder()
       ├── Is it a Purchase Req number?      → calls get_mrp_purchaserequisition()
       └── Is it Material + Area + Plant?    → calls get_pegged_requirements_for_mrp2()
       │
       ▼
Tool returns raw SAP data (a list of records)
       │
       ▼
GPT-4o formats it into a Markdown table
       │
       ▼
Table is returned as a string
```

The **system prompt** (`agent_instruction`) is a set of instructions written in plain English that tells GPT-4o exactly how to behave — which tool to pick, how to format output, and what rules to follow.

---

### `tools.py` — SAP API Callers

**What it does:** Contains all the functions that actually talk to SAP S/4HANA via HTTP REST APIs. Also contains the GL prediction function.

There are **5 functions** here:

| Function | Purpose |
|----------|---------|
| `get_mrp_plannedorder(planned_order)` | Given a Planned Order ID, fetches the material/plant/area, then gets pegged requirements |
| `get_mrp_purchaserequisition(purchase_req)` | Same as above but for Purchase Requisitions |
| `get_pegged_requirements_for_mrp2(Material, Plant, Area, PR)` | Core function — fetches actual pegged requirement records from SAP |
| `get_pegged_requirements_for_mrp(Material, Plant, Area)` | Same but without passing a PO/PR (uses a dummy placeholder) |
| `predict_gl(...)` | Sends financial fields to SAP DAR ML service for GL account prediction |

**How SAP API calls work here:**
```python
# 1. Build URL
URL = BASE_URL + "api_plannedorder/.../400000285"

# 2. Send HTTP GET with username + password
response = requests.get(url=URL, auth=(USER, PASSWORD))

# 3. Decode the response bytes to text
data_str = response.content.decode("utf-8")

# 4. Parse JSON text into a Python dictionary
data = json.loads(data_str)

# 5. Extract what you need
material = data.get("Material")
```

---

### `resource.py` — RAG System Connector

**What it does:** Sends a question to an external RAG (AI knowledge base) API and returns the answer.

RAG works like this:
```
User question
     │
     ▼
RAG API searches internal documents
     │
     ▼
Finds the most relevant document chunks
     │
     ▼
LLM generates an answer based on those chunks
     │
     ▼
Answer returned to user
```

The function simply sends an HTTP GET request with the query as a URL parameter (`?message=your_question`) and returns the `response` field from the JSON reply.

---

### `config.py` — Configuration Loader

**What it does:** Loads all secrets and configuration values in a safe, structured way — from a `.env` file locally, or from Cloud Foundry service bindings in production.

This is a security best practice: **never hardcode passwords in your code**. Instead, read them from the environment at runtime.

```
Is the app running in Cloud Foundry?
        │
        ├── YES → Read from CF service bindings (VCAP_SERVICES)
        │         └── Extract AI Core credentials automatically
        │
        └── NO  → Read from local .env file
                  └── You fill this in yourself for development
```

The `Settings` class uses **Pydantic** (a Python library) to define exactly what variables are expected and what type they should be. This catches typos and missing values early.

---

### `env.example` — Secrets Template

**What it does:** Shows you exactly which secrets you need to provide, without revealing any real values.

```env
DAR_DEPLOYMENT_URL = ""    ← URL of your deployed DAR ML model
DAR_BASE_URL = ""          ← Base URL of SAP DAR service
DAR_CLIENT_ID = ""         ← OAuth client ID for DAR
DAR_CLIENT_SECRET = ""     ← OAuth client secret for DAR
DAR_AUTH_URL = ""          ← Auth URL for DAR

RAG_ENDPOINT = ""          ← URL of your RAG API

BASE_URL = ""              ← Your SAP S/4HANA base URL
USER = ""                  ← SAP username
PASSWORD = ""              ← SAP password
```

Copy this file to `.env` and fill in your actual values.

---

## 🔄 Data Flow Walkthrough

### Scenario 1: User asks about a Planned Order

```
User: "Give me pegged requirements for Planned Order 400000285"

1. MCP Server (main.py) receives query → calls echo()
2. echo() passes query to agent() in agent.py
3. GPT-4o reads the query, sees a Planned Order number
4. GPT-4o calls get_mrp_plannedorder("400000285")
5. tools.py hits SAP API:
   GET /api_plannedorder/.../400000285
   → Returns: Material="MAT001", Plant="1810", MRPArea="1810"
6. tools.py calls get_pegged_requirements_for_mrp2("MAT001","1810","1810","400000285")
7. SAP returns a list of pegged requirement records
8. GPT-4o formats the records into a Markdown table:

   | Material | PR_PlannedOrder | Assembly | AssemblyPR_PlannedOrder |
   |----------|-----------------|----------|--------------------------|
   | MAT001   | 400000285       | ASSY001  | 500000123               |

9. Table is returned to the AI assistant
```

### Scenario 2: User asks a policy question

```
User: "What is the policy for vendor payment terms?"

1. MCP Server receives query → calls get_company_policies()
2. resource.py sends GET request to RAG_ENDPOINT?message=...
3. RAG system searches internal policy documents
4. Returns AI-generated answer based on found documents
5. Answer is returned to user
```

### Scenario 3: GL Account Prediction

```
User (or system): Provides financial document fields

1. MCP Server receives fields → calls get_gl_prediction()
2. tools.py creates an inference request with all fields
3. SAP DAR ML model processes the fields
4. Returns top 3 GL account predictions with confidence scores
5. Results returned to caller
```

---

## 🛠 The Three Exposed Tools

These are the three functions an AI assistant can call via MCP:

### 1. `echo(query: str) → str`
- **Purpose:** Handle MRP / supply chain queries
- **Input:** A natural language question containing a PO number, PR number, or Material+Area+Plant
- **Output:** Markdown table of pegged requirements
- **Internally uses:** `agent.py` → GPT-4o → SAP APIs

### 2. `get_company_policies(query: str) → str`
- **Purpose:** Answer questions about internal company policies
- **Input:** A natural language question
- **Output:** AI-generated answer from the RAG knowledge base
- **Internally uses:** `resource.py` → External RAG API

### 3. `get_gl_prediction(Company_Code, Document_Number, Fiscal_Year, LineItem, AccountType, Amount, Vendor, DocumentType, PostingDate, TaxCode)`
- **Purpose:** Predict the correct General Ledger account for a financial document
- **Input:** 10 financial document fields (all strings)
- **Output:** Top 3 GL account predictions
- **Internally uses:** `tools.py` → SAP DAR ML Service

---

## ⚙️ Setup & Configuration

### Prerequisites

Make sure you have the following installed:

- Python 3.9 or higher
- `pip` (Python package manager)
- Access to an SAP S/4HANA system
- Access to SAP Gen AI Hub (for GPT-4o)
- Access to SAP DAR service (for GL prediction)
- A running RAG endpoint

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <your-repo-folder>

# 2. Create a virtual environment (keeps dependencies isolated)
python -m venv venv

# 3. Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastmcp` | Framework for building MCP-compatible tool servers |
| `requests` | Making HTTP API calls to SAP and RAG |
| `pydantic-settings` | Structured, validated configuration loading |
| `python-dotenv` | Reading `.env` files |
| `cfenv` | Reading Cloud Foundry environment bindings |
| `gen-ai-hub-sdk` | Connecting to SAP Gen AI Hub (GPT-4o) |
| `deepagents` | Creating LLM agents that can call tools |
| `sap-ai-core-sdk` | SAP DAR inference client |

---

## 🔐 Environment Variables

Copy `env.example` to a new file named `.env`:

```bash
cp env.example .env
```

Then fill in your actual values:

```env
# SAP DAR (Data Attribute Recommendation) — for GL prediction
DAR_DEPLOYMENT_URL = "https://your-dar-deployment-url"
DAR_BASE_URL = "https://your-dar-base-url"
DAR_CLIENT_ID = "your-client-id"
DAR_CLIENT_SECRET = "your-client-secret"
DAR_AUTH_URL = "https://your-auth-url"

# RAG System — for company policy queries
RAG_ENDPOINT = "https://your-rag-api-endpoint"

# SAP S/4HANA — for MRP/supply chain data
BASE_URL = "https://your-s4hana-url/"
USER = "your-sap-username"
PASSWORD = "your-sap-password"
```

> ⚠️ **Never commit your `.env` file to Git.** Add it to `.gitignore`.

---

## 🚀 How to Run

### Local Development

```bash
# Make sure your .env file is filled in
python main.py
```

The server will start at: `http://localhost:8000`

You can change the port by setting the `PORT` environment variable:
```bash
PORT=9000 python main.py
```

### Verify It's Running

The MCP server exposes an HTTP endpoint. You can check it's alive by visiting:
```
http://localhost:8000
```

---

## 💬 Example Queries

Here's how you'd query each tool once the server is connected to an AI assistant:

**Pegged requirements by Planned Order:**
> "Show me pegged requirements for planned order 400000285"

**Pegged requirements by Purchase Requisition:**
> "Get pegged requirements for purchase requisition 3000001516"

**Pegged requirements by Material details:**
> "Fetch pegged requirements for material KKR001 in plant 1810 and MRP area 1810"

**Company policy:**
> "What is our policy on three-way invoice matching?"

**GL prediction:**
> *(Sent programmatically with all 10 financial fields)*

---

## ☁️ Deployment: Local vs Cloud Foundry

The `config.py` file handles two environments automatically:

### Local Development
- Reads all config from your `.env` file
- `DEBUG=True` by default
- No extra setup needed beyond filling in `.env`

### Cloud Foundry (SAP BTP)
- Detects `VCAP_SERVICES` environment variable automatically
- Reads AI Core credentials from the bound service
- Reads all other config from CF environment variables
- `DEBUG=False` automatically in production

To deploy on Cloud Foundry:
```bash
cf push
```

Make sure your `manifest.yml` includes the environment variables and the AI Core service binding.

---

## 🔍 How the AI Decides Which Tool to Call

This is the magic of the **agent**. The system prompt (`agent_instruction` in `agent.py`) gives GPT-4o a set of clear rules:

```
IF input looks like a Planned Order number  → use get_mrp_plannedorder
IF input looks like a Purchase Req number   → use get_mrp_purchaserequisition  
IF input has Material + Area + Plant        → use get_pegged_requirements_for_mrp
```

GPT-4o reads your query, applies these rules, calls the right function, receives the raw data, and then converts it into the required table format — all automatically.

