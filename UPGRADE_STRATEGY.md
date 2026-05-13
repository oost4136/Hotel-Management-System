# Hotel Management System (PMS): Multi-Platform Upgrade Strategy

**Author:** Senior Developer (Gemini CLI)  
**Date:** May 11, 2026  
**Status:** Architectural Proposal

## 1. Executive Summary
To support **Desktop, Web, and Mobile** platforms simultaneously, the current "Monolithic Desktop" architecture must evolve into a **Service-Oriented Architecture (SOA)**. The desktop app will no longer talk to the database directly; instead, all platforms will communicate with a centralized **Cloud Backend (API)**.

## 2. Core Architecture: The "Source of Truth"
The central component will be a RESTful API. Given the current project is in Python, **FastAPI** is the recommended choice due to its high performance, automatic documentation (OpenAPI), and native support for asynchronous operations.

### Key Components:
*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL (Replacing SQLite for concurrency and scaling)
*   **Storage:** AWS S3 or Cloudinary (For room/inventory images)
*   **Real-time:** WebSockets (For instant sync across devices, e.g., Room Status updates)

## 3. Security Strategy: JWT with Refresh Tokens
Since we are moving to a remote API, **JSON Web Tokens (JWT)** are now the **Best Practice**.

### The Flow:
1.  **Authentication:** User logs in with credentials.
2.  **Tokens Issued:**
    *   **Access Token:** Short-lived (e.g., 15 mins). Used for every API request.
    *   **Refresh Token:** Long-lived (e.g., 7 days). Used only to get a new Access Token.
3.  **Storage (Critical):**
    *   **Web:** Store Refresh Token in an `HttpOnly`, `Secure` Cookie (prevents XSS).
    *   **Mobile/Desktop:** Store tokens in the system's secure keychain (e.g., Android Keystore, iOS Keychain, Windows Credential Manager).

### Why this is best:
*   **Statelessness:** The server doesn't need to remember every session, allowing it to scale.
*   **Security:** If an Access Token is stolen, it expires quickly. The Refresh Token can be revoked from the database to "kill" a session remotely.

## 4. Platform Implementation Details

### Desktop App (Refactoring)
*   Replace `database.py` with an `api_client.py`.
*   The UI remains `customtkinter`, but data is fetched via `requests` or `httpx`.
*   Maintain an "Offline Mode" cache if necessary, though primary operations move to the API.

### Web Application
*   **Frontend:** React or Next.js.
*   Focus on administrative dashboards and remote reporting for owners.

### Mobile Application
*   **Framework:** Flutter or React Native (Cross-platform).
*   Focus on "On-the-go" tasks: Housekeeping status updates, Guest check-ins via tablet, and Inventory scanning.

## 5. Security Best Practices to Adopt
1.  **HTTPS Everywhere:** All communication between apps and the backend must be encrypted via TLS.
2.  **Role-Based Access Control (RBAC):** Define clear permissions on the backend (e.g., `staff` cannot see `revenue_reports`).
3.  **Rate Limiting:** Prevent brute-force attacks on the login endpoint.
4.  **Input Validation:** The backend must never trust data from the clients (even the desktop app).

## 6. Migration Roadmap (Phased)
1.  **Phase 1:** Build the FastAPI Backend and migrate SQLite schema to PostgreSQL.
2.  **Phase 2:** Refactor Desktop App to use the API (keeping current UI).
3.  **Phase 3:** Develop the Web Dashboard.
4.  **Phase 4:** Develop the Mobile App.
