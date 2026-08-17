# Peblo TV Mini — Platform Engineering Take-Home

> **CMS upload → published catalogue → Netflix-style browse**  
> *Peblo · Full-Stack Platform Engineer (Python/FastAPI + React)*

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Quickstart Guide](#2-quickstart-guide)
   - [Option A: Local Development (Python + Vite)](#option-a-local-development-python--vite)
   - [Option B: Docker Compose (PostgreSQL + FastAPI + Nginx)](#option-b-docker-compose-postgresql--fastapi--nginx)
3. [Automated Test Suite](#3-automated-test-suite)
4. [Written Analysis & Architectural Questions](#4-written-analysis--architectural-questions)
   - [Q1: Atomic Publish Mechanics & Failure Modes](#q1-how-the-atomic-publish-works-end-to-end-and-what-could-go-wrong)
   - [Q2: Cloudflare R2 Migration Strategy](#q2-how-youd-migrate-the-storage-abstraction-to-cloudflare-r2-in-production)
   - [Q3: Scaling Search to 50,000+ Episodes](#q3-where-search-will-bottleneck-as-the-catalogue-grows-to-50k-episodes-and-what-youd-change)
   - [Q4: Trade-offs: Static Catalogue in Storage vs. Live DB Queries](#q4-the-trade-offs-of-the-static-catalogue-in-storage-pattern-vs-querying-a-database-directly)
   - [Q5: AI Usage Disclosure](#q5-ai-usage-disclosure)
5. [Key Design Decisions & Omissions](#5-key-design-decisions--omissions)
6. [Operability & Alerting Guide (`/health`)](#6-operability--alerting-guide-health)

---

## 1. Architecture Overview

Peblo TV Mini is structured as three decoupled, highly operable layers:

```
┌──────────────────────────────┐        ┌──────────────────────────────┐
│       CMS Console (React)    │        │      Viewer UI (React)       │
│  - Show & Episode CRUD       │        │  - Netflix-Style Home        │
│  - 3 Artwork Upload Slots    │        │  - Horizontal Section Rows   │
│  - Validation Report Engine  │        │  - Multilingual Audio Switch │
│  - Role Switcher (Admin/Ed.) │        │  - Composable Search & Filter│
└──────────────┬───────────────┘        └──────────────▲───────────────┘
               │                                       │
               │ HTTP REST (FastAPI)                   │ HTTP GET (CDN / Storage)
               ▼                                       │
┌──────────────────────────────┐        ┌──────────────┴───────────────┐
│     Backend API & Pipeline   │        │     Static Storage / CDN     │
│  - FastAPI + SQLAlchemy 2.0  │───────►│  - /catalog/catalogue.json   │
│  - SQLite (Local) / Postgres │ Publish│  - /uploads/poster/*.jpg     │
│  - Atomic Publisher Service  │   Job  │  - /uploads/banner/*.jpg     │
│  - Strict Artwork Validator  │        │  - /uploads/thumbnail/*.jpg  │
└──────────────────────────────┘        └──────────────────────────────┘
```

### Core Specifications Implemented:
* **Backend (`FastAPI` + `SQLAlchemy 2.0 Async`)**:
  * **Strict Artwork Validation**: Validates aspect ratio (tolerance within $\pm 0.05$), dimensions (Poster $\approx 600\times 900$, Banner $\approx 1280\times 720$, Thumbnail $\approx 640\times 360$), file size ($\le 200\text{ KB}$), and format (`JPEG`, `PNG`, `WebP`) using Pillow. Returns editor-friendly guidance.
  * **Language Variant Collapsing**: Episodes sharing a `content_group` are deduplicated and collapsed into a single viewer item with a `languages: ["en", "hi"]` array and audio variant records.
  * **Trailers Isolation**: Season 0 episodes are extracted from regular seasons and mounted to `show.trailers` for dedicated UI rendering.
  * **Role-Based Access Control (RBAC)**: Strict header-based authentication (`X-User-Role: admin | editor`). `admin` has full publish and rollback authority; `editor` is strictly forbidden (`HTTP 403`) from publishing.
* **Frontend (`React 18` + `TypeScript` + `TanStack Query` + `Vite`)**:
  * **Internal CMS (`/cms`)**: Search, filter by section/status/language, pagination, show/episode drawers with 3 labelled drag-and-drop artwork upload slots, and live validation report.
  * **Viewer Browse UI (`/`)**: Netflix-style dark layout with cinematic hero banner, horizontal scrolling carousels by section (`Featured`, `Series`, `Minisodes`, `Songs`), show detail modal with language variant pill switcher, and trailer player simulator.
  * **Role Switcher in Header**: 1-click switcher between Admin and Editor roles to test live RBAC enforcement.

---

## 2. Quickstart Guide

### Option A: Local Development (Python + Vite)

#### Prerequisites:
* Python 3.10+
* Node.js 18+

#### 1. Backend Setup:
```bash
# In the project root directory
python -m venv .venv
# Activate virtual environment (Windows):
.venv\Scripts\activate
# (Linux/macOS): source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Generate test image assets
python backend/scripts/generate_assets.py

# Seed the database (populates 8 shows, 95 episodes, 302 artwork assets)
python -m backend.seed_data.seed

# Start FastAPI server on port 8000
uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Frontend Setup:
```bash
# In a new terminal
cd frontend
npm install
npm run dev
```
* **Viewer UI**: [http://localhost:5173/](http://localhost:5173/)
* **CMS Console**: [http://localhost:5173/cms](http://localhost:5173/cms)
* **Validation & Publish**: [http://localhost:5173/cms/publish](http://localhost:5173/cms/publish)
* **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Docker Compose (PostgreSQL + FastAPI + Nginx)

Run the full production stack in isolated containers:
```bash
docker-compose up --build
```
* **Frontend (Nginx)**: [http://localhost:5173](http://localhost:5173)
* **Backend (FastAPI)**: [http://localhost:8000](http://localhost:8000)
* **PostgreSQL 16**: Port `5432`

---

## 3. Automated Test Suite

The test suite covers artwork validation, pipeline language collapsing, Season 0 trailer isolation, RBAC role enforcement, and composable search.

Run the test suite:
```bash
python -m pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing
```

### Test Coverage Highlights:
* `test_artwork_validation.py`:
  * `test_valid_poster_passes`: Validates standard $600\times 900$ 2:3 poster.
  * `test_poster_wrong_ratio_fails_with_editor_message`: Verifies landscape image uploaded to poster slot is rejected with editor-friendly aspect ratio error.
  * `test_oversized_banner_fails`: Rejects images exceeding 200 KB.
  * `test_tiny_thumbnail_fails`: Rejects undersized images below minimum resolution.
  * `test_corrupted_file_fails`: Rejects corrupt/non-image payloads.
* `test_publish_pipeline.py`:
  * `test_publish_collapses_language_variants`: Validates that English and Hindi variants of `content_group: "motis-many-lives-s01e01"` collapse into one entry with `languages: ["en", "hi"]`.
  * `test_publish_blocked_by_missing_duration`: Verifies validation gate blocks publishing when duration is invalid.
* `test_rbac_and_api.py`:
  * `test_editor_cannot_publish_catalog`: Asserts `POST /admin/catalog/publish` returns `HTTP 403 Forbidden` for editor role.
  * `test_admin_can_call_publish_endpoint`: Asserts `admin` role can trigger atomic publish.
  * `test_composable_catalog_search`: Tests multi-parameter query composition (`q`, `category`, `language`).
  * `test_validation_report_endpoint`: Verifies report surfaces blocking errors and remediation steps.

---

## 4. Written Analysis & Architectural Questions

### Q1: How the atomic publish works end-to-end, and what could go wrong

#### End-to-End Publish Pipeline:
```
1. Validation Pre-flight (DB Scan)
   ├── Scan published shows, episodes, and artwork
   └── Abort with HTTP 400 & error report if blocking errors exist (unless force=True)
2. In-Memory Graph Assembly
   ├── Query all Published Shows with eager-loaded Seasons, Episodes, and Artwork
   ├── Deduplicate & Collapse: Group episodes by (show_id, season_number, content_group)
   │   └── Merge ['en', 'hi'] audio variants into a single entry with languages array
   ├── Season 0 Isolation: Separate trailers into show.trailers; discard season 0 from regular list
   └── Deterministic Sorting: Sort sections by spec, shows by title, episodes by episode_number
3. JSON Serialization & Version Stamping
   └── Compute catalogue_version (e.g. 20260817-153000-a1b2), metadata, and summary counts
4. Atomic Storage Swap
   ├── Write payload to temporary file: catalogue.json.tmp.<uuid>
   ├── Flush & fsync to ensure disk persistence
   └── Atomic Rename: os.replace("catalogue.json.tmp.<uuid>", "catalogue.json")
5. PublishRun Ledger & Snapshot Archival
   └── Record DB audit record with execution status, counts, and backup copy for instant rollback
```

#### What Could Go Wrong & Mitigations:
1. **Partial / Half-Written File Reads**:
   * *Risk*: A child viewer client fetching `catalogue.json` while the server is writing bytes gets a truncated JSON payload, crashing the viewer UI.
   * *Mitigation*: We **never write directly to the live destination path**. We write to a unique temporary file (`catalogue.json.tmp.<uuid>`) and execute `os.replace()` (POSIX `rename` syscall / Windows atomic swap). On modern filesystems, `rename` is an atomic directory table pointer swap. A reader either sees the old version or the new version; never an intermediate byte.
2. **Concurrent Publish Race Conditions**:
   * *Risk*: Two content admins click "Publish" simultaneously; Run A and Run B overwrite each other's temporary files or record interleaved versions in the database.
   * *Mitigation*: Implemented a database advisory lock / transaction isolation on `PublishRun`. If a publish run is currently with `status: running`, subsequent publish requests are queued or rejected with `409 Conflict`.
3. **Stale CDN Cache vs. Atomically Swapped Storage**:
   * *Risk*: Storage has the new catalogue, but Cloudflare edge caches return a 1-hour-old cached copy.
   * *Mitigation*: Cache tags and versioned URLs. We emit an `ETag` header matching the `catalogue_version` hash, set `Cache-Control: public, max-age=60, s-maxage=300, stale-while-revalidate=60`, and trigger a Cloudflare Cache Purge API webhook upon successful publication.

---

### Q2: How you'd migrate the storage abstraction to Cloudflare R2 in production

#### Step-by-Step Migration Plan:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        StorageService (ABC Interface)                  │
├───────────────────────────────────┬────────────────────────────────────┤
│       LocalStorageService         │    CloudflareR2StorageService      │
│  - os.replace atomic rename       │  - S3 / Boto3 / HTTP API           │
│  - Local disk filesystem          │  - Multi-part atomic PUT           │
│  - URL: /storage/uploads/*        │  - URL: https://media.peblo.tv/*   │
└───────────────────────────────────┴────────────────────────────────────┘
```

1. **Leverage the Implemented Storage Interface**:
   * The codebase implements an abstract `StorageService` (`backend/app/services/storage.py`) with full `LocalStorageService` and `CloudflareR2StorageService` implementations.
   * In production, toggling `STORAGE_BACKEND=r2` activates boto3/S3-compatible client connected to Cloudflare R2 endpoint `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
2. **Direct Browser-to-R2 Pre-signed Uploads**:
   * Currently, the CMS uploads image bytes through the FastAPI backend.
   * For production scale, the CMS calls `POST /api/v1/artwork/presign-upload` to get an S3 pre-signed `PUT` URL.
   * The browser uploads the artwork directly to Cloudflare R2.
   * A lightweight Cloudflare Worker or backend webhook validates the uploaded image dimensions/size and confirms the database record. This eliminates backend network I/O and RAM saturation during large bulk asset uploads.
3. **Zero Egress & Global CDN Edge Distribution**:
   * Bind the R2 bucket to a custom domain (`https://media.peblo.tv`) protected by Cloudflare Edge CDN.
   * Benefit: Cloudflare R2 charges **$0.00 egress bandwidth fees**, saving 90%+ on bandwidth compared to AWS S3/CloudFront.
4. **Catalogue Invalidation Pipeline**:
   * When `publish_catalogue()` writes to `catalog/catalogue.json` in R2, the publisher fires an asynchronous Cloudflare API call to purge `https://media.peblo.tv/catalog/catalogue.json` across all global edge data centers in $<300\text{ms}$.

---

### Q3: Where search will bottleneck as the catalogue grows to 50k episodes, and what you'd change

#### Current Bottlenecks at 50k Episodes:
1. **Client-Side Catalogue Parsing**:
   * A static `catalogue.json` containing 50,000 episodes and 8,000 shows would weigh $\approx 15\text{MB}$ uncompressed ($\approx 2.2\text{MB}$ gzipped).
   * Downloading, decompressing, and parsing a 15MB JSON file on low-end mobile devices or Smart TVs will cause browser memory pressure and main-thread UI jank.
2. **SQL `ILIKE` / Substring Scanning**:
   * Direct database queries using `ILIKE '%query%'` result in full table scans on 50k rows, defeating standard B-Tree index lookups.
3. **Lack of Typo-Tolerance & Child Voice Search**:
   * Children frequently misspell titles (e.g. *"peblo moti"*, *"rhyme rangrs"*, *"animl song"*). Plain string matching fails to return relevant content.

#### Architectural Evolution & Redesign:

```
[50k+ Episodes Scale Architecture]

CMS Publish Run ──► 1. Split Catalogue by Section & Language
                    │  ├── catalogue-featured.json (150 KB)
                    │  ├── catalogue-series.json (400 KB)
                    │  └── catalogue-songs.json (200 KB)
                    │
                    └──► 2. Sync to Meilisearch / Typesense Cluster
                                │
                                ▼
Viewer UI ──────────► Instant Search Bar (Typo-Tolerant, <15ms response)
```

1. **Partitioned Section Slicing**:
   * Instead of one monolithic `catalogue.json`, the publish job writes partitioned files:
     * `/catalog/sections/featured.json`
     * `/catalog/sections/series.json`
     * `/catalog/sections/songs.json`
     * `/catalog/index-summary.json` (lightweight metadata for home screen initial paint)
   * The viewer app fetches only the sections needed for immediate viewport rendering, lazy-loading additional rows as the user scrolls.
2. **Dedicated Search Index (Meilisearch / Typesense / Postgres FTS)**:
   * **Phase 1 (Up to 100k items)**: Enable PostgreSQL Full-Text Search with `tsvector` columns, English/Hindi dictionary stemmers, and GIN indices.
   * **Phase 2 (Production Scale)**: Deploy a managed **Meilisearch** or **Typesense** instance. The publish pipeline streams show and episode documents to the search index. Features:
     * Typo-tolerant prefix search within $<15\text{ms}$.
     * Automatic synonym mapping (e.g. *"nursery rhymes"* $\leftrightarrow$ *"kids songs"*).
     * Faceted filtering by category, age group, and audio language.

---

### Q4: The trade-offs of the "static catalogue in storage" pattern vs. querying a database directly

| Attribute | Static Catalogue in Storage (CDN / R2) | Direct Database Queries (API / Postgres) |
| :--- | :--- | :--- |
| **Viewer Latency** | **Ultra-Low ($<25\text{ms}$)** served from nearest CDN edge. | **Moderate ($80\text{--}300\text{ms}$)** depending on DB load, network hops, connection pooling. |
| **Traffic Spike Resilience** | **Near Infinite**: $100{,}000$ concurrent child viewers hit edge cache. Zero load on DB. | **Vulnerable**: Traffic spikes can exhaust DB connection pools, trigger lock contention, or crash instances. |
| **System Availability** | **99.999%**: If the database crashes or undergoes maintenance, viewers continue streaming uninterrupted. | **Coupled**: DB downtime directly produces `500 Internal Server Error` for all viewers. |
| **Infrastructure Cost** | **Near Zero**: Static JSON hosting on Cloudflare R2 has zero egress fees and minimal compute. | **High**: Requires large DB clusters, read replicas, Redis caching layers, and autoscale API pods. |
| **Data Freshness** | **Eventually Consistent**: Changes appear only after a publish job completes. | **Immediately Consistent**: CMS edits reflect instantly in real-time. |
| **Personalization** | **Low**: All viewers in a locale receive the identical catalogue snapshot. | **High**: Allows real-time per-user personalization ("Continue Watching", user watch history, A/B testing). |

#### Conclusion & Hybrid Recommendation:
For a streaming platform like Peblo TV, the **static catalogue pattern is objectively superior for content discovery** (95% of traffic: browsing home rows, show details, and episode lists). Real-time user-specific state (watch progress, user profile, resume timestamps) is separated into lightweight dynamic microservices (`/user/continue-watching`), giving the best of both worlds: infinite scalability for catalog delivery and high agility for user state.

---

### Q5: AI Usage Disclosure

* **What AI was used for**:
  * Scaffolding initial boilerplate code for FastAPI routes, Pydantic schemas, and Vite frontend component structure.
  * Accelerating test fixture creation and synthetic image generation scripts (`Pillow` scripts generating aspect-ratio test fixtures).
* **What was human-architected & engineered**:
  * **Domain Logic & Data Modeling**: Designing the composite index `ix_episodes_content_group_lang` to handle language variant deduplication while allowing CMS ingestion of deliberate seed imperfections (`ep_9001`, `ep_0036`).
  * **Collapsing Algorithm**: Structuring the deterministic grouping in `publisher.py` that merges multilingual episodes into a single entry with `languages: ["en", "hi"]` while isolating Season 0 trailers.
  * **Atomic File Swap Mechanics**: Implementing safe temp-file creation and `os.replace` filesystem semantics to prevent partial reads during high-concurrency requests.
  * **RBAC & Security Posture**: Enforcing server-side 403 Forbidden barriers on publish routes rather than relying on UI-only button hiding.

---

## 5. Key Design Decisions & Omissions

### What Was Built:
1. **Full-featured 3-surface platform**: Fast, typed backend, professional CMS console with live validation report and 3 artwork upload slots, and Netflix-style Viewer browsing experience.
2. **Seed Data Ingestion & Correction Engine**: Seeder successfully imports all 8 shows, 95 episodes, and 302 artwork assets. The validation engine flags missing artwork on `ep_0036`, duplicate content_group on `ep_9001`, and missing section on `Rhyme Rangers`.
3. **Interactive Role Switching**: CMS header allows 1-click role toggling between `Admin` and `Editor` to demonstrate real 403 Forbidden handling.
4. **Resilient Frontend**: Added skeleton loading states, image fallback handlers, and interactive multilingual audio variant selectors.

### What Was Deliberately Skipped & Why:
1. **OAuth2 / SSO Provider (e.g. Auth0 / Google SSO)**: Replaced with API keys + `X-User-Role` headers. For a 6-8 hour take-home challenge, implementing external OAuth redirects adds setup friction for reviewers without testing core platform engineering judgment.
2. **Live Video Transcoding Engine (FFmpeg / HLS)**: Streamed mock MP4/WebM video players with real audio language track toggling. Real HLS transcoding pipelines belong in a separate worker cluster and would require external cloud dependencies.
3. **Database Migration Tooling (Alembic)**: Database schema is initialized via `SQLAlchemy Base.metadata.create_all` for instant, zero-friction local and Docker startup.

---

## 6. Operability & Alerting Guide (`/health`)

The backend exposes a health check endpoint at `GET /health` designed for uptime monitors (DataDog, Prometheus, AWS Route53).

### Health Check Response:
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "latency_ms": 1.42
  },
  "storage": {
    "status": "writable",
    "backend": "local"
  },
  "catalogue": {
    "status": "published",
    "version": "20260817-153000-a1b2",
    "path": "catalog/catalogue.json"
  },
  "validation": {
    "blocking_errors_count": 0,
    "warnings_count": 2
  }
}
```

### Alerting Rules for Ops:
| Condition | Severity | Action |
| :--- | :--- | :--- |
| `database.status != "connected"` | **P1 Critical** | Page on-call database engineer. API cannot serve CMS writes. |
| `storage.status != "writable"` | **P1 Critical** | Page on-call platform engineer. Disk full or S3 credentials expired. |
| `catalogue.status == "missing"` | **P2 Warning** | Trigger auto-publish run or notify content ops team. |
| `database.latency_ms > 200` | **P3 Warning** | Check DB connection pool saturation and active query locks. |
