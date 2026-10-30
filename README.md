# 🏛️ SecureVote: Enterprise-Grade Electronic Voting & Electoral Governance System
### Course: CSE494 - Intelligent NoSQL Databases | Academic Task 2
**Lovely Professional University**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/MongoDB-8.x%20%7C%20PyMongo-green.svg)](https://www.mongodb.com/)
[![Web Framework](https://img.shields.io/badge/Flask-REST%20API-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Security](https://img.shields.io/badge/Security-TLS%20SMTP%20OTP%20%7C%20SHA--256-orange.svg)](#-cybersecurity--privacy-architecture)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Executive Summary
**SecureVote** is a full-stack, privacy-preserving electronic voting platform built on **Python**, **PyMongo**, and **MongoDB 8.x**. Engineered to mirror real-world statutory electoral commissions, SecureVote enforces strict role-based access control (RBAC), multi-stage MongoDB aggregation analytics, automated voter registration with admin approval queues, engine-level schema validation, and real-time **Google TLS SMTP One-Time Passcode (OTP)** delivery.

---

## 🌟 Key Highlights & Engineering Innovations

### 1. 🔐 Multi-Factor Admin Gateway with Real-Time SMTP Mailer
- **Zero On-Screen Exposure**: No hardcoded credentials or debug autofill.
- **TLS SMTP Dispatch**: Directly interfaces with `smtp.gmail.com:587` to transmit single-use 6-digit cryptographic OTPs with responsive HTML security templates.
- **Master Audit Trail**: Every authentication attempt, dispatch status, and session generation is permanently logged in the MongoDB audit collection.

### 2. 🛡️ Database-Enforced Security ($jsonSchema & Unique Indexes)
- **Engine-Level Validation**: Uses MongoDB `$jsonSchema` validators to enforce data integrity directly in the database layer. Underage voters (Age < 18), malformed emails, and invalid election statuses are rejected before reaching storage (`WriteError 121`).
- **Mathematical Double-Voting Prevention**: Utilizes a Compound Unique Index `(election_id, voter_id_hash)` to strictly guarantee one-person-one-vote while maintaining voter anonymity.
- **Ballot Secrecy via SHA-256**: The voter's identity is cryptographically salted and hashed prior to ballot insertion.

### 3. 👥 Segregated Role-Based Portals

#### 🗳️ Voter Portal:
- **Automated Voter ID Issuance**: Automatic sequential ID generation (e.g., `VTR-1001`, `VTR-1002`) upon sign-up.
- **Eligibility Verification Queue**: New sign-ups enter a `pending` state until reviewed and approved by the Commission Admin.
- **Official Polling Booth**: Clean, candidate roster with one-click ballot casting and instant confirmation.
- **Cryptographic Ballot Receipts**: Generates unique SHA-256 verifiable receipt tokens stored in a dedicated receipts tab.
- **Sealed Results Policy**: Live tallies remain sealed and hidden until an election is officially concluded by the Admin.

#### ⚙️ Admin Commission Console:
- **Tab 1: Voter Verification Queue**: Review student applications, approve eligible voters, or reject fraudulent registrations.
- **Tab 2: Elections Management**: Create new campus elections with inline creation cards, activate voting, or seal and complete elections.
- **Tab 3: Contestants Roster**: Add official candidates with profile bios, party affiliations, and manifestos.
- **Tab 4: Live Tallies & Analytics**: Real-time turnout velocity, department-wise breakdowns, and visual charts powered by Chart.js.
- **Tab 5: Security Audit Trail**: Tamper-evident chronological log of all administrative actions and security events.

---

## 📊 5 Advanced Multi-Stage MongoDB Aggregation Pipelines

SecureVote demonstrates complex NoSQL analytical querying via PyMongo:

| Pipeline | Operators Employed | Purpose |
| :--- | :--- | :--- |
| **1. Certified Leaderboard & Winner Ranking** | `$match`, `$group`, `$sort`, `$lookup`, `$project` | Ranks candidates by total votes received and flags winner. |
| **2. Departmental Voter Turnout Breakdown** | `$lookup`, `$unwind`, `$group`, `$project`, `$sort` | Computes voter participation percentage per academic school. |
| **3. Temporal Polling Velocity** | `$project` (`$dateToString`), `$group`, `$sort` | Tracks voting traffic spikes across hourly time windows. |
| **4. Multi-Dimensional Seniority Matrix** | `$lookup`, `$unwind`, `$group` (`$push`), `$project` | Maps voter preferences across student academic years. |
| **5. Executive KPI Faceted Dashboard** | `$facet`, `$count`, `$group`, `$project` | Single-query computation of total electorate, active elections, and turnout rate. |

---

## 📁 Repository Structure
```
PYMONGO PROJECT/
├── app.py                 # Flask REST API server and session management
├── database.py            # MongoDB connection, $jsonSchema rules, indexes
├── crud.py                # PyMongo CRUD operations for voters, ballots, elections
├── analytics.py           # 5 Advanced MongoDB Aggregation Pipelines
├── mailer.py              # TLS SMTP Mailer service with HTML security templates
├── email_config.json      # SMTP configuration file (Gmail, Outlook, custom SMTP)
├── seed_data.py           # Database seeder with sample elections, candidates, voters
├── run.py                 # One-click startup script (pre-flight checks + server launch)
├── run.bat                # Windows batch launcher
├── templates/
│   └── index.html         # Responsive, glassmorphic single-page web portal
├── static/
│   ├── css/
│   │   └── style.css      # Dark-theme design system, micro-animations, glassmorphism
│   └── js/
│       └── main.js        # Dynamic UI routing, tab isolation, Chart.js integrations
├── PROJECT_REPORT.md      # Comprehensive academic report
└── README.md              # Project documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **MongoDB Community Server 7.x or 8.x** running locally on default port `27017`
- Pip packages: `pip install flask pymongo`

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/SecureVote-PyMongo.git
cd SecureVote-PyMongo
```

### 2. Configure Email OTP Dispatch (Optional for Live Inbox Delivery)
Edit `email_config.json`:
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "sender_name": "National Electoral Commission",
  "sender_email": "your_email@gmail.com",
  "sender_password": "your_16_char_google_app_password"
}
```
*(Note: If left unconfigured, passcodes are automatically written to `dispatched_emails.log` and the server console for testing).*

### 3. Launch the Application
- **On Windows**: Double-click `run.bat` or run:
  ```bash
  python run.py
  ```
- The launcher runs MongoDB connectivity checks, verifies schema indexes, starts the Flask server at `http://127.0.0.1:5000`, and opens your default browser automatically.

---

## 🛡️ Default Commission Credentials (Demo)

- **Admin Account**: Registered Commission Administrator (`yeswanthburle1432@gmail.com`)
- **Authentication**: Permanent Password: `Yash@1432`
- **Sample Voter**: Email: `rahul.verma@univ.edu` | Password: `password123`

---

## 📜 Academic Integrity & License
Developed as part of **CSE494: Intelligent NoSQL Databases** at **Lovely Professional University**. Released under the [MIT License](LICENSE).
