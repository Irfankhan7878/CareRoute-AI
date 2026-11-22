# System Architecture: Hospital Patient Intake & Department Routing Assistant

## 1. Executive Summary & Objective

The **Hospital Patient Intake and Department Routing Assistant** is an autonomous multi-agent healthcare coordination platform built on **Microsoft Semantic Kernel (v1.47.0)**, **ChromaDB Vector Retrieval (RAG)**, **FastAPI**, and **React + Tailwind CSS**. 

The system automates the administrative intake workflow: collecting patient complaints, screening for life-threatening emergency signs, recalling previous visit history for returning patients, routing concerns across 11 hospital departments, retrieving grounded clinical intake guidelines, and coordinating conflict-free demonstration appointment bookings.

> [!IMPORTANT]
> **Administrative Scope & Non-Diagnostic Guarantee**: CareRoute AI is strictly an administrative triage and hospital navigation system. It **never diagnoses diseases, prescribes pharmaceuticals, or replaces licensed medical evaluation**. Every patient response explicitly reinforces consultation with a qualified medical professional.

---

## 2. Why Routing with RAG Architecture Fits This Domain

1. **Deterministic Clinical Gating vs. Free-Form Hallucination**:
   Healthcare intake requires strict, deterministic boundaries. Combining rule-grounded triage routing with semantic vector retrieval prevents language models from fabricating hospital policies, misdirecting emergency patients, or hallucinating diagnoses.
2. **Dynamic Knowledge Separation**:
   Hospital operational policies (prep instructions, fasting requirements, required imaging) evolve frequently. Housing policy documents in a modular ChromaDB vector database allows hospital administrators to update clinical intake guidelines without fine-tuning models or rewriting core logic.
3. **Auditability & Traceability**:
   Every instruction returned to the patient cites its specific source document (e.g. `[source: orthopaedics.txt#Section 3]`). This enables rigorous healthcare auditing, compliance tracking, and administrative accountability.

---

## 3. High-Level System Architecture

```mermaid
graph TD
    Client([React 19 Frontend Dashboard]) <-->|REST API / JSON| API[FastAPI Gateway]
    
    subgraph MultiAgentSystem [Microsoft Semantic Kernel Orchestration Core]
        API --> Orch[Central Orchestrator]
        
        Orch --> Ag1[1. Intake Agent]
        Ag1 -->|Validated Record| Ag6[6. Records Memory Agent]
        Ag6 -->|Patient History Context| Ag5[5. Safety Gate]
        
        Ag5 -->|CRITICAL RED FLAG DETECTED| UrgentStop[Halt Pipeline & Issue Emergency Advisory]
        Ag5 -->|SAFETY CLEARANCE| Ag2[2. Triage Router Agent]
        
        Ag2 -->|Target Department| Ag3[3. Information Agent]
        Ag3 <-->|Semantic Search & Citations| VectorDB[(ChromaDB Hospital Index)]
        
        Ag3 -->|Grounded Instructions| Ag4[4. Appointment Agent]
        Ag4 <-->|Query Slots & Atomic Booking| RelDB[(SQLite Database)]
    end
    
    UrgentStop --> Output[Aggregated Intake Response]
    Ag4 --> Output
    Output --> API
    
    Orch -.->|Thread-Safe JSONL Stream| AuditLog[(logs/agent_runs.jsonl)]
```

---

## 4. Multi-Agent Roster & Tool Registry

Every agent is encapsulated as an independent Python module with real tool functions decorated with Semantic Kernel's `@kernel_function`:

| Agent Name | Primary Responsibility | Native Python Tools | Framework Integration |
| :--- | :--- | :--- | :--- |
| **1. Intake Agent** | Input validation, sanitization, and structured DB session persistence | `validate_patient_input()`<br>`create_patient_record()` | `IntakePlugin`<br>Semantic Kernel |
| **6. Records Memory Agent** | Returning patient identification, history recall, and reference generation | `search_patient_history()`<br>`recall_previous_routing()` | `RecordsMemoryPlugin`<br>Semantic Kernel |
| **5. Safety Gate** | Mandatory red-flag clinical symptom screening and emergency routing halt | `detect_urgent_warning_signs()`<br>`generate_urgent_care_advisory()` | `SafetyGatePlugin`<br>Semantic Kernel |
| **2. Triage Router Agent** | Symptom classification across 11 hospital departments with confidence scoring | `classify_patient_concern()`<br>`get_department_information()` | `TriageRouterPlugin`<br>Semantic Kernel |
| **3. Information Agent** | Semantic RAG retrieval over hospital policies and grounded instruction formatting | `retrieve_department_information()`<br>`format_grounded_instructions()` | `InformationPlugin`<br>Semantic Kernel |
| **4. Appointment Agent** | Demonstration slot availability query and atomic conflict-free reservation | `get_available_appointment_slots()`<br>`reserve_appointment_slot()` | `AppointmentPlugin`<br>Semantic Kernel |

---

## 5. Sequence & Orchestration Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Patient / Staff
    participant API as FastAPI Gateway
    participant Orch as Central Orchestrator
    participant Intake as 1. Intake Agent
    participant Memory as 6. Records Memory Agent
    participant Safety as 5. Safety Gate
    participant Triage as 2. Triage Router Agent
    participant Info as 3. Information Agent
    participant Appt as 4. Appointment Agent
    participant DB as SQLite / ChromaDB

    Patient->>API: POST /api/process (Concern, Demographics)
    API->>Orch: process_intake(payload)
    
    Note over Orch,Intake: Step 1: Validate Demographics
    Orch->>Intake: run(raw_input)
    Intake->>DB: validate_patient_input() & create_patient_record()
    Intake-->>Orch: Validated Session (INTK-XXXX)

    Note over Orch,Memory: Step 2: Check Records Memory
    Orch->>Memory: run(patient_id, name)
    Memory->>DB: search_patient_history() & recall_previous_routing()
    Memory-->>Orch: Returning Patient Context (Previous Visits)

    Note over Orch,Safety: Step 3: Mandatory Safety Gate
    Orch->>Safety: run(concern, age)
    Safety->>Safety: detect_urgent_warning_signs()
    
    alt Urgent Red Flags Detected
        Safety->>Safety: generate_urgent_care_advisory()
        Safety-->>Orch: URGENT_STOP (Halt Normal Pipeline)
        Orch->>DB: Record Emergency Stop Status
        Orch-->>API: Emergency Advisory + Local Hotlines (Zero Routine Slots)
        API-->>Patient: Display Urgent-Care Screen
    else No Urgent Red Flags (Normal)
        Safety-->>Orch: Normal Clearance
        
        Note over Orch,Triage: Step 4: Department Classification
        Orch->>Triage: run(concern, age)
        Triage->>DB: classify_patient_concern() & get_department_information()
        Triage-->>Orch: Selected Department + Confidence Score

        Note over Orch,Info: Step 5: ChromaDB RAG Retrieval
        Orch->>Info: run(department, concern)
        Info->>DB: ChromaDB Semantic Search & Document Attributions
        Info-->>Orch: Grounded Instructions & Source Citations

        Note over Orch,Appt: Step 6: Available Slots Query
        Orch->>Appt: run(department_code)
        Appt->>DB: get_available_appointment_slots()
        Appt-->>Orch: Available Slot Options

        Orch->>DB: Commit RoutingRecord
        Orch-->>API: Full Structured Routing Result
        API-->>Patient: Render Routing Results & Appointment Selector
    end
```

---

## 6. Safety Gate Decision Logic

The Safety Gate is an uncompromising barrier placed before normal outpatient routing. It screens symptoms across six high-risk clinical categories:

```mermaid
flowchart TD
    Start([Incoming Patient Concern]) --> Scan[SafetyGatePlugin: detect_urgent_warning_signs]
    
    Scan --> Check1{Cardiovascular?<br>Crushing chest pain, left arm radiation}
    Scan --> Check2{Respiratory?<br>Severe shortness of breath, gasping, cyanosis}
    Scan --> Check3{Neurological?<br>Slurred speech, facial droop, thunderclap headache}
    Scan --> Check4{Trauma / Hemorrhage?<br>Uncontrolled bleeding, high-velocity injury}
    Scan --> Check5{Anaphylaxis?<br>Throat closure, swollen tongue/lips}

    Check1 -- Yes --> Halt[TRIGGER SAFETY STOP]
    Check2 -- Yes --> Halt
    Check3 -- Yes --> Halt
    Check4 -- Yes --> Halt
    Check5 -- Yes --> Halt

    Halt --> Advise[generate_urgent_care_advisory]
    Advise --> Supress[Suppress Routine Appointments]
    Supress --> ER[Display Emergency Red Wing Location & 112/911/108 Hotlines]

    Check1 -- No --> Pass[All Checks Passed]
    Check2 -- No --> Pass
    Check3 -- No --> Pass
    Check4 -- No --> Pass
    Check5 -- No --> Pass
    
    Pass --> Continue[Proceed to Triage Router Agent]
```

---

## 7. RAG Semantic Knowledge Pipeline

```mermaid
graph LR
    subgraph Offline Ingestion
        Docs[12 Hospital Policy Docs in documents/hospital_info/] --> Splitter[Section & Heading Parser]
        Splitter --> Embedder[all-MiniLM-L6-v2 ONNX Embeddings]
        Embedder --> Chroma[(ChromaDB Persistent Collection)]
    end

    subgraph Runtime Retrieval
        Query[Patient Symptom Query] --> Filter[Department Metadata Filter]
        Filter --> Chroma
        Chroma --> Ranked[Top-K Grounded Chunks]
        Ranked --> Formatter[format_grounded_instructions Tool]
        Formatter --> Attributions[Synthesized Instructions + Exact File Citations]
    end
```

---

## 8. Database Entity Relationship Diagram (SQLite)

```mermaid
erDiagram
    PATIENTS ||--o{ INTAKE_SESSIONS : submits
    PATIENTS ||--o{ ROUTING_RECORDS : receives
    PATIENTS ||--o{ APPOINTMENT_BOOKINGS : reserves

    INTAKE_SESSIONS ||--o| ROUTING_RECORDS : generates
    
    DEPARTMENTS ||--o{ APPOINTMENT_SLOTS : offers
    APPOINTMENT_SLOTS ||--o| APPOINTMENT_BOOKINGS : booked_as

    AGENT_EXECUTIONS ||--o{ AGENT_TOOL_LOGS : invokes

    PATIENTS {
        string patient_id PK
        string full_name
        int age
        datetime created_at
    }

    INTAKE_SESSIONS {
        string session_id PK
        string patient_id FK
        text described_concern
        string duration
        boolean is_returning_patient
        string status
        datetime created_at
    }

    DEPARTMENTS {
        int id PK
        string code UK
        string name
        text description
        string location
        string operating_hours
    }

    ROUTING_RECORDS {
        int id PK
        string session_id FK
        string patient_id FK
        string selected_department
        string department_code
        float confidence_score
        text reason
        string safety_status
        datetime created_at
    }

    APPOINTMENT_SLOTS {
        int id PK
        string department_code FK
        string date
        string time_slot
        string doctor_name
        boolean is_available
    }

    APPOINTMENT_BOOKINGS {
        int id PK
        string booking_reference UK
        int slot_id FK
        string patient_id FK
        string appointment_date
        string time_slot
        string status
    }
```
