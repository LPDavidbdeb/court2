# AI PROJECT CHARTER AND GUARDRAILS DOCUMENT
**Project:** Headless V2 Refactoring (Django API + React)
**Date:** March 2026

> **SYSTEM DIRECTIVE FOR THE AI AGENT:** > This document is your absolute source of truth for this project. Before executing any refactoring task, generating code, or modifying the architecture, you must verify that your actions are aligned with the rules, technical stack, and scope defined below.

---

## 1. PROJECT CHARTER (VISION AND OBJECTIVES)
* **Vision:** Transform the current monolithic Django application into a decoupled (Headless) architecture using the "Strangler Fig" pattern. The goal is to strictly separate the business logic (Backend) from the user interface (Frontend) to facilitate the future integration of real-time AI.
* **Main Objective:** Replace classic Django views with a fast RESTful API, consumed by a reactive frontend, with ZERO corruption to the existing database.
* **In-Scope:**
  * End-to-end API creation.
  * Implementation of new token-based authentication (JWT).
  * Translation of complex data (MPTT hierarchies, Tabula PDF parsing) into standardized JSON formats.
  * Creation of a new frontend.
* **Out-of-Scope (STRICT):**
  * **FORBIDDEN** to modify the fundamental structure of the PostgreSQL database or the ORM relationships in `models.py` without explicit authorization.
  * **FORBIDDEN** to modify the mathematical logic of the `pgvector` queries.

---

## 2. MANDATORY TECH STACK (STRICT)
The agent must exclusively use the following technologies. Any deviation will result in the code being rejected.

### Backend (Port: 8001)
* **Language & Framework:** Python 3.x, Django 5.x.
* **API:** Django Ninja (**STRICTLY FORBIDDEN to use Django REST Framework / DRF**). Validation via Pydantic schemas.
* **Authentication:** `ninja-jwt`.
* **Data & DB:** PostgreSQL, `django-mptt` (for the hierarchical tree).
* **Workers/Analysis:** Celery, `tabula-py`, `pandas`.

### Frontend (Port: 5173)
* **Framework:** React 18, Vite, TypeScript.
* **Styling:** Tailwind CSS, CSS Modules.
* **UI/Components:** Shadcn UI (using `lucide-react`, `clsx`, `tailwind-merge`).

---

## 3. WORK BREAKDOWN STRUCTURE (WBS)
Code execution must follow these phases sequentially. Do not skip steps.

### Phase 1: Framing and Isolation (Infrastructure)
* [ ] **1.1** Initialize the clean repository (Clean Pull).
* [ ] **1.2** Configure `docker-compose.yml` to expose the API on 8001 and Vite on 5173.
* [ ] **1.3** Ensure the project points to the isolated development database (`court_v2_db`), seeded with a recent dump.

### Phase 2: Backend Development (Django Ninja)
* [ ] **2.1** Initialize the main Django Ninja router (`api.py`).
* [ ] **2.2** Implement the authentication module (`/api/token/` and `/api/token/refresh/` endpoints via `ninja-jwt`).
* [ ] **2.3** Extract business logic from the old `views.py` into independent `services.py` files, decoupled from the UI.
* [ ] **2.4** Create Pydantic schemas (Inputs/Outputs) for each model, using the `ExhibitableMixin` as a common serialization baseline.
* [ ] **2.5** Create endpoints to expose the MPTT tree and the PDF parsing results (`tabula-py`).

### Phase 3: Frontend Development (React/Vite)
* [ ] **3.1** Initialize the Vite/React folder architecture (`components/`, `pages/`, `services/`, `utils/`).
* [ ] **3.2** Install and configure Tailwind CSS and Shadcn UI.
* [ ] **3.3** Generate fundamental UI components via Shadcn (Buttons, Forms, Data Tables, Modals).
* [ ] **3.4** Create the authentication context (`AuthContext`) to store and inject the JWT into API requests (Axios or fetch).
* [ ] **3.5** Develop the connected views linked to the endpoints to display case files, the accounting tree, and documents.

---

## 4. RULES OF CONDUCT FOR THE AGENT (PRE-SUBMISSION CHECKLIST)
Before proposing a code modification, the agent must mentally validate these points:
1. Did I use Django Ninja and Pydantic instead of DRF?
2. Did I preserve the integrity of `models.py`?
3. Is the frontend code strictly written in TypeScript with Tailwind/Shadcn?
4. Has the business logic been extracted from views into reusable services?