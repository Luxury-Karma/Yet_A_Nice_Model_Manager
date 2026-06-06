# 3D File Classifier & Indexer

A self-contained, lightweight local web application designed to automatically scan, index, organize, and search 3D printing files (STL, 3MF, OBJ) across your local storage. 

This project bridges the gap between a powerful database-driven web application and a frictionless, zero-setup desktop utility. It can be run either as a single, zero-dependency executable (`.exe`) or deployed as a headless, network-accessible community hub via Docker.

---

## 🛠️ Project Architecture

The application utilizes a **Hybrid Desktop-Web Architecture** with modular authentication boundaries to support both single-user workstation isolation and secure multi-user network sharing:

```
 [ Remote Friend's Browser ]         [ Your Local Browser ]
             │                             │
             ▼ ( Authenticated Request )   ▼
┌────────────────────────────────────────────────────────┐
│               PYTHON BACKEND EXECUTABLE                │
│                                                        │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │   Auth Middleware     │──>│  FastAPI Web Server  │  │
│  │  • JWT Token Validator│   │  • REST API / Stream │  │
│  │  • RBAC Permissions   │   │  • Web Asset Router  │  │
│  └───────────────────────┘   └───────────┬──────────┘  │
│  ┌───────────────────────┐               │             │
│  │   Background Worker   │<──────────────┘             │
│  │  • Metadata Parser    │                             │
│  └───────────┬───────────┘                             │
└──────────────┼─────────────────────────────────────────┘
               ▼
┌──────────────────────────┐   ┌─────────────────────────┐
│     SQL DATABASE         │   │  LOCAL STORAGE VAULT    │
│  • SQLite (Local .exe)   │   │  • STL, 3MF, OBJ Files  │
│  • PostgreSQL (Docker)   │   │  • Streamed in Chunks   │
└──────────────────────────┘   └─────────────────────────┘
```

* **Backend:** Python 3.11+ powered by **FastAPI** (ASGI web server). FastAPI manages request/response pipelines, streams large static binaries efficiently, and handles async middleware validation layers.
* **Database Layer:** Dual-mode relational engine using **SQLAlchemy ORM**:
    * *Desktop Mode:* **SQLite** embedded directly within the process. Zero configuration; database tables are initialized automatically inside a local `library.db` file upon launch. Defaults to a single auto-authenticated administrative profile.
    * *Server Mode:* **PostgreSQL** support via environment configuration for multi-user, multi-owner network sharing and NAS scale.
* **Authentication Layer:** Secure password hashing via `passlib[bcrypt]` and stateless authorization tokens via **OAuth2 with JWT (JSON Web Tokens)** to govern cross-network asset security.
* **Frontend UI:** Vanilla JavaScript/HTML5 or a lightweight frontend framework served directly by the Python backend. Features a secure login portal, asset management dashboards, tag management filters, and an interactive WebGL 3D model viewport.

---

## 🚀 Target Deployment & Workflow Modes

### Mode A: The "Single-Click" Executable (Workstation Mode)
Designed for individual creators who want an immediate asset manager on their local machine without setting up runtimes or databases.
1. The user launches `3d-file-indexer.exe`.
2. The application provisions a local SQLite file, skips explicit credential checks by defaulting to a localized root admin environment, and hosts the server at `http://127.0.0.1:8000`.
3. A browser instance hooks directly into the running instance for single-session tracking.

### Mode B: The Network Hub Stack (Docker / Multi-User Sharing Mode)
Designed for power users running unRAID, TrueNAS, or cloud-accessible home servers who want to share access to their model libraries with friends.
* Deployed headlessly via `docker-compose`.
* Connects to a persistent volume containing 3D printing directories.
* Routes incoming external connections through authentication middleware to protect non-public models.
* Uses streaming responses to allow authenticated friends to safely download raw files directly from your host infrastructure without exhausting server RAM.

---

## 📂 Core Feature Roadmap

### 1. Automated Metadata Extraction & Parsing
* **STL Files:** Parses binary/ASCII headers to extract raw triangle and facet counts, calculating structural bounding boxes to derive physical model dimensions (X, Y, Z in mm).
* **3MF & OBJ Files:** Extracts native embedded file metadata, internal manifest XML data, slicing profiles, and standalone object components.
* **Automatic Thumbnail Generation:** Generates lightweight static preview snapshots or renders fallback vector icons using an embedded headless standard canvas worker.

### 2. Intelligent Search & Indexing Engine
* **Instant Querying:** Indexed paths are searched via optimized SQL indexing, yielding sub-millisecond response times across thousands of items.
* **Tagging System:** Allows logical categorization (e.g., `Miniature`, `Functional`, `Warhammer`, `Terrain`) mapping a clean many-to-many relationship structure in the database.
* **Duplicate Detection:** Computes partial hashes or file-size matches to flag duplicate models across multiple hard drives.

### 3. Multi-User Access Control & Remote Streaming (Networking Update)
* **Role-Based Access Control (RBAC):** Restricts asset modifications to the specified content owner or instance system administrators.
* **Granular Asset Sharing:** Models can be toggled to `is_public` (accessible to anyone with account access) or shared explicitly with specified friend accounts via user mapping tables.
* **Memory-Efficient File Streaming:** Leverages chunked binary streaming to transfer massive CAD and mesh geometries (up to hundreds of megabytes) across the WAN without encountering server out-of-memory (OOM) crashes.

---

## 📊 Database Schema Design

The relational structure is expanded to handle secure user profiles, relational data ownership flags, and peer-to-peer security constraints:

```sql
-- Track user accounts and hashed credentials
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Core model metadata table linked explicitly to an owner
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    file_extension TEXT NOT NULL,
    hash_signature TEXT,
    dim_x REAL,
    dim_y REAL,
    dim_z REAL,
    triangle_count INTEGER,
    is_public BOOLEAN DEFAULT FALSE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Many-to-Many categorization tagging table
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE model_tags (
    model_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (model_id, tag_id),
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Granular peer-to-peer model sharing permission rules
CREATE TABLE model_shares (
    model_id INTEGER,
    shared_with_user_id INTEGER,
    PRIMARY KEY (model_id, shared_with_user_id),
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🛠️ Step-by-Step Implementation Strategy

### Phase 1: Core CLI & Parsing Engine (The Foundation)
* Build the core Python file walker utilities and binary parsers for extracting geometry limits out of `.stl` and `.3mf` headers.
* Establish the base SQLAlchemy database engines and test initial structural migrations.

### Phase 2: Web API, Auth Engine & Frontend Scaffold
* Build FastAPI endpoint routes for metadata fetching and dashboard management.
* Implement JWT Token authentication handlers, user registration logic, and password salting/hashing routines.
* Create a simple web view featuring file cards, access toggle controls, and basic tag filter lookups.

### Phase 3: Networking, Chunked Streaming & Sharing Pipelines
* Write the access verification security dependencies to validate token scopes before reading raw disk arrays.
* Introduce streaming mechanisms via chunked file transfers to allow low-overhead model downloads.
* Expand the UI to enable sharing specific models or collections with targeted user accounts.

### Phase 4: Bundling & Containerization
* Configure PyInstaller configurations to compress the core application environment down into a single portable application executable.
* Build multi-stage Docker architectures optimizing final container dimensions for lean network hosting.
