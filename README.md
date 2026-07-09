# PayMi - Reliable Payments Backend

A robust, concurrency-safe REST API for peer-to-peer money transfers. Built with Python and FastAPI, this system is designed around financial engineering principles to guarantee ACID compliance, prevent double-spend exploits, and handle network retry drops cleanly.

## 🏗️ Core Engineering Highlights

*   **Double-Entry Ledger (PostgreSQL):** Instead of keeping a fragile, static `balance` column that can drift out of sync, balances are dynamically calculated from immutable `debit` and `credit` ledger entries.
*   **Concurrency & Deadlock Prevention:** Utilizes database row-level locking (`SELECT ... FOR UPDATE`) on the sender's account during the transfer process to ensure atomic transactions and completely eliminate double-spend race conditions.
*   **Idempotency Engine (Redis):** Enforces strict idempotency on transfer routes using client-generated UUID keys. Cached transaction results in Redis (with a 24-hour TTL) protect the primary database from being hammered during accidental network retries or malicious double-clicks.
*   **Stateless Auth:** Secured via custom JWT-based authentication for scalable, stateless session management.

## 🛠️ Tech Stack
*   **Framework:** FastAPI (Python 3.14)
*   **Database:** PostgreSQL (Hosted on Neon)
*   **Cache:** Redis (Hosted on Upstash)
*   **ORM:** SQLAlchemy
*   **Infrastructure:** Docker
