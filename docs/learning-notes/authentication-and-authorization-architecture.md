# Authentication and Authorization Architecture

## Overview

CareerLens is a modular monolith combining a **Next.js / Vite React frontend** with a **FastAPI Python backend**. To ensure multi-user isolation, user data privacy (resumes, interview answers, scorecards, learning roadmaps), and security compliance, authentication and authorization are implemented at both the API boundary and the frontend state layer.

---

## 1. Backend Security Layer

### Password Hashing
- **Algorithm:** Argon2id (via `pwdlib.PasswordHash.recommended()`).
- **Enforcement:** Minimum password length of 12 characters is strictly validated at both the Pydantic schema level (`RegisterRequest`) and the cryptographic utility level (`hash_password`).
- **Security Benefits:** Argon2 is memory-hard and computationally resistant to GPU/ASIC brute-force attacks, providing significantly higher security than legacy MD5/SHA algorithms.

### Token Architecture
- **Standard:** JSON Web Tokens (JWT) signed using HMAC SHA-256 (`HS256`).
- **Claims:**
  - `sub`: User ID (persisted integer converted to string).
  - `exp`: Short-lived expiration (default: 30 minutes, configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Secret Management:** Read from `JWT_SECRET` environment variable with fallback only allowed when `CAREERLENS_ENV=development`.

### Route & Resource Authorization
1. **Global Route Guard:** All application routes except `/health` and `/auth/*` require `Depends(get_current_user)`.
2. **Resource Ownership Helpers:**
   - `require_current_user_id`: Verifies requested user ID matches token identity.
   - `require_owned_resume`: Verifies that a target resume belongs to `current_user.id` before analysis, matching, or roadmap generation.
   - `require_owned_blueprint` & `require_owned_execution_session`: Verifies the interview execution session belongs to the candidate.
   - `require_owned_roadmap_item`: Prevents candidates from reading or modifying another user's learning roadmap progress.

---

## 2. Frontend Security & Animated UX

### State & Context Architecture
- **`AuthContext` (`frontend/src/context/AuthContext.jsx`):**
  - Manages `user`, `token`, `isAuthenticated`, `isLoading`, and modal triggers.
  - Hydrates session on startup from `localStorage` by verifying the bearer token against `/auth/me`.
  - Automatically clears stale tokens if the backend returns HTTP 401.
- **Client Header Helper (`frontend/src/services/api/auth.js`):**
  - Exports `getAuthHeaders()`, injecting `Authorization: Bearer <token>` into all outbound requests.

### Animated Interface (`frontend/src/components/auth/AuthPage.jsx`)
- **Libraries Used:**
  - `motion/react`: Spring-based layout animations for mode tabs (`layoutId="auth-tab-pill"`), exit/entry animations for alerts and input fields (`AnimatePresence`).
  - `lucide-react`: Crisp icons for security shields, user identity, lock security, and visibility toggling.
- **Live Password Strength Meter:**
  - Dynamic score calculating length (>= 12), mixed case, and numbers/symbols.
  - Real-time checklist providing immediate visual confirmation of the backend's 12-character requirement.
- **Demo Quick-Fill Lenses:**
  - One-click switches for **Student Lens** (`student@careerlens.dev`) and **Professional Lens** (`professional@careerlens.dev`), enabling frictionless presentation and testing.
