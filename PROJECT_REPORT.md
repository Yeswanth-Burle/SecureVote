# LOVELY PROFESSIONAL UNIVERSITY
## School of Computer Science & Engineering
### Academic Task 2: Project Report
**Course Code:** CSE494  
**Course Title:** INTELLIGENT NOSQL DATABASES  
**Maximum Marks:** 30  

---

# PROJECT TITLE: SecureVote – Intelligent Online Voting System using PyMongo & MongoDB

---

## TABLE OF CONTENTS
1. [Problem Statement & Real-World Relevance](#1-problem-statement--real-world-relevance)
2. [Database & Document Schema Design](#2-database--document-schema-design)
3. [MongoDB Schema Validation Rules ($jsonSchema)](#3-mongodb-schema-validation-rules-jsonschema)
4. [Indexing Strategy & Integrity Constraints](#4-indexing-strategy--integrity-constraints)
5. [CRUD Operations (MongoDB Query Language & PyMongo Code)](#5-crud-operations-mongodb-query-language--pymongo-code)
   - 5.1 Create Operations (C)
   - 5.2 Read Operations (R)
   - 5.3 Update Operations (U)
   - 5.4 Delete Operations (D)
6. [Advanced Aggregation Pipelines](#6-advanced-aggregation-pipelines)
   - 6.1 Pipeline 1: Certified Election Leaderboard & Winner Ranking ($lookup, $group, $sort)
   - 6.2 Pipeline 2: Academic Department Turnout Breakdown ($group, $sort)
   - 6.3 Pipeline 3: Temporal Voting Velocity & Peak Surge Hours ($project with $dateToString, $group)
   - 6.4 Pipeline 4: Multi-Dimensional Student Seniority Matrix ($group with $push)
   - 6.5 Pipeline 5: Multi-Faceted Executive KPI Dashboard ($facet)
7. [System Architecture & PyMongo Integration](#7-system-architecture--pymongo-integration)
8. [Sample Execution Outputs & Demonstration Evidence](#8-sample-execution-outputs--demonstration-evidence)
9. [Viva Voce Preparation & Justifications](#9-viva-voce-preparation--justifications)
10. [Conclusion & Future Work](#10-conclusion--future-work)

---

## 1. Problem Statement & Real-World Relevance

### 1.1 Problem Statement
Democratic student elections (such as Student Council, Department Representatives, and Campus Clubs) have traditionally relied either on physical paper ballots or rudimentary relational database forms. These legacy approaches suffer from critical vulnerabilities:
- **Ballot Stuffing & Duplicate Votes**: Inability to mathematically guarantee one-person-one-vote across decentralized polling stations without compromising secret-ballot privacy.
- **Slow & Error-Prone Tabulation**: Manual ballot counting takes hours or days and is prone to human transcription mistakes.
- **Rigid Data Schemas**: Relational databases enforce rigid tabular schemas that do not naturally map to semi-structured electoral documents (e.g., candidate manifestos, dynamic audit metadata, variable election formats).
- **Lack of Real-Time Demographic Insights**: Existing voting systems cannot perform high-velocity analytical slicing across departments, student years, and temporal surge hours.

### 1.2 Real-World Relevance & Solution
**SecureVote** solves these challenges by combining MongoDB 8.x with Python (PyMongo):
- **Ballot Secrecy + Integrity**: Voters cast anonymous ballots hashed with SHA-256 and salted per election. The raw voter ID is never stored on the ballot document.
- **Engine-Level Duplicate Prevention**: A MongoDB compound unique index `(election_id, voter_id_hash)` strictly guarantees at the database storage engine layer that a voter cannot vote more than once in any given election.
- **Schema Validation at Database Level**: Enforces `$jsonSchema` rules ensuring strict data types, regular expression email verification, and minimum age restrictions (age >= 18).
- **Atomic Concurrency**: Utilizes MongoDB's atomic `$inc` operator for real-time candidate tallying and atomic audit logging.
- **High-Velocity Aggregations**: 5 advanced aggregation pipelines provide certified leaderboards, department participation rates, hourly surge velocity, and multi-faceted analytics in sub-millisecond query execution.

---

## 2. Database & Document Schema Design

The application utilizes a dedicated database named **`voting_system_db`** comprising five specialized collections:

### 2.1 Collection: `voters`
Stores registered university student voters.

```json
{
  "_id": ObjectId("67167a5b3c47638afbeb5bb1"),
  "voter_id": "STU1021",
  "name": "Nikhil Chopra",
  "email": "nikhil.c@univ.edu",
  "department": "Computer Science",
  "year_of_study": 2,
  "age": 20,
  "status": "active",
  "created_at": ISODate("2026-10-21T18:47:00.000Z")
}
```

### 2.2 Collection: `elections`
Stores election instances and lifecycle parameters.

```json
{
  "_id": ObjectId("67167a5b3c47638afbeb5bb5"),
  "election_id": "ELEC-2026-PRES",
  "title": "University Student Council Presidential Election 2026",
  "category": "Student Council",
  "status": "active",
  "start_date": ISODate("2026-10-19T18:47:00.000Z"),
  "end_date": ISODate("2026-10-26T18:47:00.000Z"),
  "description": "General election for university-wide student body president."
}
```

### 2.3 Collection: `candidates`
Stores registered election contenders, slates, and manifestos.

```json
{
  "_id": ObjectId("67167a5b3c47638afbeb5bb8"),
  "candidate_id": "CAND-01",
  "election_id": "ELEC-2026-PRES",
  "name": "Aarav Sharma",
  "party_or_slate": "Tech Innovators Slate",
  "manifesto": "Digital campus modernization, 24/7 AI lab infrastructure, open-source hackathons, and transparent student representation.",
  "department": "Computer Science",
  "vote_count": 7
}
```

### 2.4 Collection: `votes`
Stores anonymous, immutable ballot records.

```json
{
  "_id": ObjectId("67167a5b3c47638afbeb5bc9"),
  "vote_id": "VOTE-8C19ACA2A0",
  "election_id": "ELEC-2026-PRES",
  "candidate_id": "CAND-01",
  "voter_id_hash": "a8793b5d3f2316e8853b006c9a304e22fe2518e38d6df0c52ee16d1bf1e2f5b9",
  "department": "Computer Science",
  "year_of_study": 2,
  "timestamp": ISODate("2026-10-21T19:09:23.390Z"),
  "receipt_token": "RCPT-CA2E3ECCF911"
}
```

### 2.5 Collection: `audit_logs`
Provides an immutable security trail of administrative actions and ballot events.

```json
{
  "_id": ObjectId("67167a5b3c47638afbeb5bdf"),
  "log_id": "LOG-3FE9A120",
  "action": "VOTE_CAST",
  "timestamp": ISODate("2026-10-21T19:09:23.401Z"),
  "details": {
    "election_id": "ELEC-2026-PRES",
    "vote_id": "VOTE-8C19ACA2A0",
    "department": "Computer Science"
  }
}
```

---

## 3. MongoDB Schema Validation Rules ($jsonSchema)

To ensure high data integrity, MongoDB collection validators are established using `$jsonSchema`. Any insert or update violating these constraints is aborted by the database engine with `WriteError (Code: 121)`.

### 3.1 Voter Validator Specification
Implemented via `db.create_collection("voters", validator=...)`:

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["voter_id", "name", "email", "department", "year_of_study", "age", "status"],
    "properties": {
      "voter_id": {
        "bsonType": "string",
        "pattern": "^[A-Z0-9_-]{3,20}$",
        "description": "Must be 3-20 alphanumeric characters"
      },
      "name": {
        "bsonType": "string",
        "minLength": 2,
        "maxLength": 80
      },
      "email": {
        "bsonType": "string",
        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
        "description": "Must match standard email regex"
      },
      "department": {
        "bsonType": "string",
        "enum": ["Computer Science", "Electronics", "Mechanical", "Management", "Biotechnology", "Civil"],
        "description": "Must belong to recognized departments"
      },
      "year_of_study": {
        "bsonType": "int",
        "minimum": 1,
        "maximum": 5
      },
      "age": {
        "bsonType": "int",
        "minimum": 18,
        "maximum": 100,
        "description": "Voter must be at least 18 years old to vote"
      },
      "status": {
        "bsonType": "string",
        "enum": ["active", "suspended", "graduated"]
      }
    }
  }
}
```

### 3.2 Candidate Validator Specification
Ensures `vote_count` is a non-negative integer and prevents negative tally corruption:

```json
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["candidate_id", "election_id", "name", "party_or_slate", "manifesto", "department", "vote_count"],
    "properties": {
      "candidate_id": { "bsonType": "string" },
      "election_id": { "bsonType": "string" },
      "name": { "bsonType": "string", "minLength": 2 },
      "vote_count": { "bsonType": "int", "minimum": 0 }
    }
  }
}
```

---

## 4. Indexing Strategy & Integrity Constraints

Indexes were strategically created to ensure `O(log N)` query execution and enforce mission-critical business rules:

| Collection | Index Key | Index Type | Purpose |
| :--- | :--- | :--- | :--- |
| **`votes`** | `{"election_id": 1, "voter_id_hash": 1}` | **Compound Unique** | **Guarantees one vote per student per election. Duplicate attempts trigger E11000 duplicate key error.** |
| **`voters`** | `{"voter_id": 1}` | Single Field Unique | Enforces distinct student IDs. |
| **`voters`** | `{"email": 1}` | Single Field Unique | Prevents duplicate voter registrations. |
| **`candidates`** | `{"candidate_id": 1}` | Single Field Unique | Enforces distinct candidate identification. |
| **`candidates`** | `{"election_id": 1}` | Standard Secondary | Speeds up candidate lookup during election filtering. |
| **`votes`** | `{"timestamp": -1}` | Secondary Descending | Optimizes timeline and velocity aggregations. |

---

## 5. CRUD Operations (MongoDB Query Language & PyMongo Code)

### 5.1 Create Operations (C)

#### 1. Registering a Student Voter
- **MQL Query:**
  ```javascript
  db.voters.insertOne({
    voter_id: "STU1035",
    name: "Tanvi Sharma",
    email: "tanvi.s@univ.edu",
    department: "Computer Science",
    year_of_study: 2,
    age: 20,
    status: "active",
    created_at: new Date()
  });
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  result = db.voters.insert_one(voter_doc)
  ```

#### 2. Casting an Anonymous Verified Vote
- **MQL Query:**
  ```javascript
  db.votes.insertOne({
    vote_id: "VOTE-8C19ACA2A0",
    election_id: "ELEC-2026-PRES",
    candidate_id: "CAND-01",
    voter_id_hash: "a8793b5d3f2316e8853b006c9a304e22fe2518e38d6df0c52ee16d1bf1e2f5b9",
    department: "Computer Science",
    year_of_study: 2,
    timestamp: new Date(),
    receipt_token: "RCPT-CA2E3ECCF911"
  });
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  db.votes.insert_one(vote_doc)
  ```

---

### 5.2 Read Operations (R)

#### 1. Finding Voter Profile & Status
- **MQL Query:**
  ```javascript
  db.voters.findOne(
    { voter_id: "STU1021" },
    { _id: 0, voter_id: 1, name: 1, department: 1, status: 1 }
  );
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  voter = db.voters.find_one({"voter_id": voter_id.strip().upper()}, {"_id": 0})
  ```

#### 2. Searching Voters with Filters, Regex, and Projection
- **MQL Query:**
  ```javascript
  db.voters.find(
    {
      department: "Computer Science",
      status: "active",
      $or: [
        { name: { $regex: "aditya", $options: "i" } },
        { voter_id: { $regex: "aditya", $options: "i" } }
      ]
    },
    { _id: 0, voter_id: 1, name: 1, email: 1, department: 1, year_of_study: 1 }
  ).sort({ name: 1 }).limit(50);
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  voters = list(db.voters.find(query, projection).sort("name", 1).limit(limit))
  ```

---

### 5.3 Update Operations (U)

#### 1. Atomic Vote Count Increment on Candidate
- **MQL Query:**
  ```javascript
  db.candidates.updateOne(
    { candidate_id: "CAND-01", election_id: "ELEC-2026-PRES" },
    { $inc: { vote_count: 1 } }
  );
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  db.candidates.update_one(
      {"candidate_id": candidate_id_clean, "election_id": election_id_clean},
      {"$inc": {"vote_count": 1}}
  )
  ```

#### 2. Updating Candidate Manifesto ($set)
- **MQL Query:**
  ```javascript
  db.candidates.updateOne(
    { candidate_id: "CAND-01" },
    { $set: { manifesto: "Updated comprehensive digital governance manifesto." } }
  );
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  result = db.candidates.update_one(
      {"candidate_id": candidate_id.strip().upper()},
      {"$set": {"manifesto": new_manifesto.strip()}}
  )
  ```

---

### 5.4 Delete Operations (D)

#### 1. Deleting Inactive/Draft Candidate
- **MQL Query:**
  ```javascript
  db.candidates.deleteOne({ candidate_id: "CAND-05" });
  ```
- **PyMongo Code (`crud.py`):**
  ```python
  result = db.candidates.delete_one({"candidate_id": candidate_id.strip().upper()})
  ```

---

## 6. Advanced Aggregation Pipelines

### 6.1 Pipeline 1: Certified Leaderboard & Winner Ranking ($lookup Join)
- **Real-World Purpose**: Directly counts authenticated votes from immutable ballots, performs an outer join with `candidates` to enrich name, party, and department, and sorts descending.
- **Pipeline Stages**:
  ```javascript
  [
    { $match: { election_id: "ELEC-2026-PRES" } },
    { $group: { _id: "$candidate_id", verified_votes: { $sum: 1 } } },
    {
      $lookup: {
        from: "candidates",
        localField: "_id",
        foreignField: "candidate_id",
        as: "candidate_info"
      }
    },
    { $unwind: "$candidate_info" },
    {
      $project: {
        _id: 0,
        candidate_id: "$_id",
        name: "$candidate_info.name",
        party_or_slate: "$candidate_info.party_or_slate",
        department: "$candidate_info.department",
        votes: "$verified_votes"
      }
    },
    { $sort: { votes: -1 } }
  ]
  ```
- **Sample Output**:
  ```json
  [
    { "candidate_id": "CAND-01", "name": "Aarav Sharma", "party_or_slate": "Tech Innovators Slate", "department": "Computer Science", "votes": 7 },
    { "candidate_id": "CAND-02", "name": "Ananya Patel", "party_or_slate": "Green Campus Alliance", "department": "Biotechnology", "votes": 6 },
    { "candidate_id": "CAND-04", "name": "Priya Nair", "party_or_slate": "Arts & Tech Vanguard", "department": "Electronics", "votes": 4 },
    { "candidate_id": "CAND-03", "name": "Rohan Verma", "party_or_slate": "Students United Coalition", "department": "Management", "votes": 4 }
  ]
  ```

---

### 6.2 Pipeline 2: Academic Department Turnout Breakdown ($group)
- **Real-World Purpose**: Measures democratic participation rates across faculties.
- **Pipeline Stages**:
  ```javascript
  [
    { $match: { election_id: "ELEC-2026-PRES" } },
    { $group: { _id: "$department", total_votes_cast: { $sum: 1 } } },
    { $project: { _id: 0, department: "$_id", total_votes: "$total_votes_cast" } },
    { $sort: { total_votes: -1 } }
  ]
  ```
- **Sample Output**:
  ```json
  [
    { "department": "Computer Science", "total_votes": 6 },
    { "department": "Electronics", "total_votes": 4 },
    { "department": "Biotechnology", "total_votes": 3 },
    { "department": "Management", "total_votes": 3 },
    { "department": "Mechanical", "total_votes": 3 },
    { "department": "Civil", "total_votes": 2 }
  ]
  ```

---

### 6.3 Pipeline 3: Temporal Voting Velocity & Surge Hours ($dateToString)
- **Real-World Purpose**: Aggregates ballots into chronological hourly intervals to analyze voting surges and network capacity.
- **Pipeline Stages**:
  ```javascript
  [
    { $match: { election_id: "ELEC-2026-PRES" } },
    {
      $project: {
        hour_bucket: {
          $dateToString: { format: "%Y-%m-%d %H:00", date: "$timestamp" }
        }
      }
    },
    { $group: { _id: "$hour_bucket", votes_in_hour: { $sum: 1 } } },
    { $project: { _id: 0, time_slot: "$_id", vote_count: "$votes_in_hour" } },
    { $sort: { time_slot: 1 } }
  ]
  ```
- **Sample Output**:
  ```json
  [
    { "time_slot": "2026-10-21 11:00", "vote_count": 1 },
    { "time_slot": "2026-10-21 12:00", "vote_count": 1 },
    { "time_slot": "2026-10-21 13:00", "vote_count": 3 },
    { "time_slot": "2026-10-21 14:00", "vote_count": 3 },
    { "time_slot": "2026-10-21 15:00", "vote_count": 3 },
    { "time_slot": "2026-10-21 16:00", "vote_count": 3 },
    { "time_slot": "2026-10-21 17:00", "vote_count": 4 },
    { "time_slot": "2026-10-21 18:00", "vote_count": 2 }
  ]
  ```

---

### 6.4 Pipeline 4: Multi-Dimensional Student Seniority Matrix ($group with $push)
- **Real-World Purpose**: Two-level hierarchical grouping analyzing voter participation by year of study (Freshman to Senior) and department.
- **Pipeline Stages**:
  ```javascript
  [
    { $match: { election_id: "ELEC-2026-PRES" } },
    {
      $group: {
        _id: { year: "$year_of_study", department: "$department" },
        subtotal: { $sum: 1 }
      }
    },
    {
      $group: {
        _id: "$_id.year",
        total_year_votes: { $sum: "$subtotal" },
        department_breakdown: {
          $push: { dept: "$_id.department", count: "$subtotal" }
        }
      }
    },
    {
      $project: {
        _id: 0,
        year_of_study: "$_id",
        total_votes: "$total_year_votes",
        departments: "$department_breakdown"
      }
    },
    { $sort: { year_of_study: 1 } }
  ]
  ```

---

### 6.5 Pipeline 5: Multi-Faceted Executive KPI Dashboard ($facet)
- **Real-World Purpose**: Calculates 3 parallel analytical metrics in a single round-trip: summary statistics, candidate shares, and department breakdown.
- **Pipeline Stages**:
  ```javascript
  [
    { $match: { election_id: "ELEC-2026-PRES" } },
    {
      $facet: {
        "election_summary": [
          {
            $group: {
              _id: null,
              total_ballots_cast: { $sum: 1 },
              first_vote_time: { $min: "$timestamp" },
              last_vote_time: { $max: "$timestamp" }
            }
          }
        ],
        "candidate_tally": [
          { $group: { _id: "$candidate_id", vote_count: { $sum: 1 } } },
          { $sort: { vote_count: -1 } }
        ],
        "department_stats": [
          { $group: { _id: "$department", count: { $sum: 1 } } },
          { $sort: { count: -1 } }
        ]
      }
    }
  ]
  ```

---

## 7. System Architecture & PyMongo Integration

### 7.1 Tech Stack
- **Database Engine**: MongoDB Community Server 8.2.3 (Port 27017)
- **Driver**: PyMongo 4.19.0 (Native Python BSON / MongoDB driver)
- **Application Server**: Python 3.14 + Flask 3.1.3
- **User Interface**: HTML5, Vanilla Modern CSS (Dark Theme + Glassmorphism), Chart.js 4.4, Native JavaScript ES6

### 7.2 Project File Structure
```
PYMONGO PROJECT/
├── database.py       # MongoDB connection, $jsonSchema rules, indexes
├── crud.py           # PyMongo CRUD implementation (C, R, U, D)
├── analytics.py      # 5 Advanced Aggregation Pipelines + viva docs
├── seed_data.py      # Populates realistic demo dataset (30 voters, ballots)
├── app.py            # Flask REST API server and routing
├── run.py            # Python one-click launcher
├── run.bat           # Windows double-click startup batch script
├── templates/
│   └── index.html    # Interactive Glassmorphic UI Dashboard
├── static/
│   ├── css/
│   │   └── style.css # Design system, gradients, cards, responsiveness
│   └── js/
│       └── main.js   # Client-side voting flow, charts, viva explorer
└── PROJECT_REPORT.md # Complete Academic Project Submission Report
```

---

## 8. Sample Execution Outputs & Demonstration Evidence

### 8.1 Successful Vote & Receipt Generation
- **Input**: Voter ID `STU1021`, Election `ELEC-2026-PRES`, Candidate `CAND-01`
- **Response**:
  ```json
  {
    "success": true,
    "message": "Vote successfully cast and cryptographically recorded!",
    "receipt_token": "RCPT-CA2E3ECCF911",
    "vote_id": "VOTE-8C19ACA2A0",
    "timestamp": "2026-10-21T19:09:23.390665",
    "candidate_name": "Aarav Sharma",
    "election_title": "University Student Council Presidential Election 2026"
  }
  ```

### 8.2 Duplicate Vote Prevention (MongoDB Compound Unique Index)
- **Input**: Second vote attempt with Voter ID `STU1021` in election `ELEC-2026-PRES`
- **Response**:
  ```json
  {
    "success": false,
    "error": "DUPLICATE VOTE REJECTED: You have ALREADY cast a vote in this election! One-person-one-vote rule enforced."
  }
  ```

### 8.3 $jsonSchema Underage Validation Rejection
- **Input**: Attempted voter document with `age: 16`
- **MongoDB Error**:
  ```
  WriteError (Code: 121): Document failed validation
  operatorName: '$jsonSchema'
  schemaRulesNotSatisfied: [
    {
      propertyName: 'age',
      description: 'Voter must be at least 18 years old to vote',
      details: [{ operatorName: 'minimum', specifiedAs: { minimum: 18 }, consideredValue: 16 }]
    }
  ]
  ```

---

## 9. Viva Voce Preparation & Justifications

### Q1: Why did you choose MongoDB instead of a Relational Database like MySQL?
**Answer:**
1. **Dynamic Schemas**: Different election types (Executive elections, sports boards, referendums) require flexible document shapes without painful schema alterations.
2. **Atomic In-Memory Updates**: The `$inc` operator allows thousands of concurrent votes to be tallied in memory without table locks.
3. **Powerful Aggregation Framework**: MongoDB replaces complex multi-table SQL JOINs with high-speed multi-stage data processing pipelines (`$match`, `$group`, `$lookup`, `$facet`).
4. **Native JSON/BSON Data Exchange**: Directly bridges with Python dictionaries and web APIs with zero object-relational impedance mismatch.

### Q2: How does your system guarantee one-person-one-vote while preserving ballot secrecy?
**Answer:**
When a vote is cast, the system hashes the voter ID with the election ID and a secure salt using SHA-256: `hash = SHA256(voter_id + election_id + salt)`.
This hash is stored in the `votes` collection alongside the ballot. Because of the **compound unique index** on `(election_id, voter_id_hash)`, any subsequent attempt to cast a ballot in the same election generates an identical hash that triggers a `DuplicateKeyError (E11000)` in MongoDB. Crucially, the voter's real identity is never linked directly to candidate choice.

### Q3: Why is $facet used in Pipeline 5?
**Answer:**
`$facet` allows executing multiple parallel sub-pipelines within a single aggregation stage on the same set of input documents. Without `$facet`, our application would have to query the database three separate times over the network (once for summary totals, once for candidate rankings, and once for department breakdowns). `$facet` completes all three in a single database round-trip.

### Q4: How does MongoDB enforce schema validation?
**Answer:**
MongoDB provides `$jsonSchema` document validators defined at collection creation. In `database.py`, we set `validationLevel="strict"` and `validationAction="error"`. When an insert or update occurs, MongoDB checks data types (`bsonType`), numeric ranges (`minimum`, `maximum`), regex patterns (`pattern`), and enum sets (`enum`). If any document violates a rule, the operation is rejected before touching disk storage.

---

## 10. Conclusion & Future Work
SecureVote successfully satisfies all requirements specified in the **CSE494 Academic Task 2 Project Specification**:
1. Realistic problem design with university relevance.
2. Well-structured document schemas with indexes.
3. Native MongoDB `$jsonSchema` validation rules.
4. Complete, hardened CRUD operations via PyMongo.
5. Five meaningful, multi-stage aggregation pipelines.
6. Responsive, visually stunning glassmorphic UI with real-time analytics and viva testing suite.

**Future Enhancements:**
- Integration of Zero-Knowledge Proofs (ZKP) for mathematical voter verification without revealing student credentials.
- Sharding the `votes` collection across distributed MongoDB replica sets for multi-campus national elections.
