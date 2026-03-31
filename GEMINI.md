# Migration Master Directive: Monolith to Headless

## 1. Core Mission
Migrate the legacy Django monolithic application to a decoupled architecture:
* **Backend:** Django with Django-Ninja (REST API).
* **Frontend:** React/Node.js with Vite, Tailwind CSS, and Shadcn UI.
* **Primary Goal:** 1:1 functional parity with the original app before any new features are added.

## 2. Source of Truth Protocol
The "requirements documents" are the legacy files located in the backend:
* **UI/Logic:** `backend/templates/` folders.
* **Interaction:** Associated `static/js/` files.
* **Data:** The back end has been seeded with a clean pull from the original monolith.

## 3. Implementation Order (Piecewise)
1. **Account Module:** `backend/templates/account/`.
2. **Photo Documents:** `backend/photos/templates/photos/photodocument/`.
3. **Email Manager:** `backend/email_manager/templates/email_manager/`.

## 4. Technical Constraints
* **Authentication:** Use `NinjaJWTDefaultController` for JWT-based auth.
* **API Pattern:** Versioned routers (e.g., `/api/v2/photos`).
* **Frontend State:** Use React Router for navigation and Axios for API consumption.
* **No Guessing:** Do not create new UI patterns. If a feature existed in the template (like the TinyMCE editor in `detail.html`), it must exist in the React frontend.

## 5. Success & Reporting Criteria
* Every task must include unit tests for Ninja endpoints and functional validation for React components.
* Output a **Full Accomplishment Report** after every prompt including modified files, API schemas, and a parity checklist.