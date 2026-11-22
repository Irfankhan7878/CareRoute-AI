# CareRoute AI: Hospital Patient Intake & Department Routing Assistant

An autonomous multi-agent healthcare coordination system built with **Microsoft Semantic Kernel (v1.47.0)**, **ChromaDB RAG**, **FastAPI**, and **React + Tailwind CSS**.

> **MANDATORY NOTICE**: CareRoute AI is an administrative intake and department routing assistant, **NOT a medical diagnosis system**. It never diagnoses conditions, prescribes pharmaceuticals, or guarantees clinical outcomes. Every response explicitly advises consulting a qualified healthcare professional.

---

## 1. Project Objective

Automates hospital patient intake: collecting described symptoms, screening for emergency red flags, recalling returning patient history, routing concerns across 11 hospital departments, retrieving grounded clinical intake policies, and offering demonstration appointment reservations.

## 2. Multi-Agent Roster & Native Python Tools

Six specialized agents operate within Microsoft Semantic Kernel using real Python tools decorated with `@kernel_function`:

1. **Intake Agent** (`backend/agents/intake_agent.py`)
   - `validate_patient_input()`: Validates name, age (0–120), and symptom presence.
   - `create_patient_record()`: Generates unique session/patient IDs and commits to SQLite.
2. **Records Memory Agent** (`backend/agents/records_memory_agent.py` - Team of 3 Feature)
   - `search_patient_history()`: Queries historical intake sessions by patient ID/name.
   - `recall_previous_routing()`: Recalls previous department and date as a reference without biasing new clinical evaluation.
3. **Safety Gate Agent** (`backend/agents/safety_gate_agent.py` - Non-Bypassable Gatekeeper)
   - `detect_urgent_warning_signs()`: Evaluates red flags across cardiovascular, respiratory, stroke, trauma, and allergy rules.
   - `generate_urgent_care_advisory()`: Issues emergency care advisory, halts routine routing, and suppresses standard appointment booking.
4. **Triage Router Agent** (`backend/agents/triage_router_agent.py`)
   - `classify_patient_concern()`: Matches symptoms to 11 hospital departments with confidence scoring (0.0–1.0).
   - `get_department_information()`: Verifies department operating status in the catalogue.
5. **Information Agent** (`backend/agents/information_agent.py`)
   - `retrieve_department_information()`: Semantic retrieval across ChromaDB vector store.
   - `format_grounded_instructions()`: Formats documents to bring, prep instructions, and source citations (`[source: file.txt]`).
6. **Appointment Agent** (`backend/agents/appointment_agent.py`)
   - `get_available_appointment_slots()`: Queries database for available department slots.
   - `reserve_appointment_slot()`: Atomically locks a slot and generates reference ID (`BK-XXXXXX`), preventing double-bookings.

---

## 3. Architecture: Routing with RAG

* **Why it fits**: Healthcare administrative intake demands absolute determinism. Combining rule-grounded triage routing with vector retrieval eliminates LLM hallucinations, grounds instructions in authentic hospital policy documents (`documents/hospital_info/`), and provides transparent source attribution.
* **Records Memory**: Identifies returning patients (e.g. `P-1001` Eleanor Vance), displaying prior consultation details for continuity while independently assessing current complaints.
* **Safety Gate Priority**: Sits between intake validation and department routing. Urgent signs (e.g. severe chest pain or breathing difficulty) immediately halt normal outpatient routing.

## 4. One Honest Failure Handled

* **Ambiguous or Non-Specific Patient Concerns**: When a patient enters vague symptoms (e.g., *"I feel strange and a bit unwell overall without specific pain"*), confidence is inherently low (< 0.65). Instead of inventing false certainty, the Triage Router Agent falls back to **General Medicine** with an explicit notice recommending a comprehensive primary physician evaluation.

---

## 5. Technology Stack

* **Backend**: Python 3.11+, FastAPI, Pydantic V2, Uvicorn, SQLAlchemy, SQLite
* **Multi-Agent Core**: Microsoft Semantic Kernel 1.47.0
* **Vector Store & Embeddings**: ChromaDB with local ONNX MiniLM embeddings (No paid API keys required)
* **Frontend**: React 19, Vite, Tailwind CSS v4, Axios, Lucide React
* **Testing & Audit**: Pytest, FastAPI TestClient, Append-only JSONL log (`logs/agent_runs.jsonl`)

---

## 6. Installation & Execution Guide

### Prerequisites
* Python 3.11+ and Node.js 18+ (tested on Windows)

### Step 1: Clone Repository & Setup Virtual Environment
```powershell
git clone <your-repo-url>
cd agenticCA2

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Seed Database & Index Hospital Documents
```powershell
python scripts/seed_db.py
```

### Step 3: Run Backend Server
```powershell
uvicorn backend.main:app --port 8000 --reload
# Backend active at: http://localhost:8000 (API Docs: http://localhost:8000/docs)
```

### Step 4: Run Frontend Dashboard
```powershell
cd frontend
npm install
npm run dev
# Frontend active at: http://localhost:3000
```

### Step 5: Run Automated Tests
```powershell
pytest -v tests/
```

### Step 6: Run Demonstration Notebook
```powershell
jupyter notebook notebooks/hospital_intake_demo.ipynb
```

---

