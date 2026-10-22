"""
crud.py - CRUD (Create, Read, Update, Delete) Operations using PyMongo
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System
"""

import hashlib
import uuid
from datetime import datetime
from pymongo.errors import DuplicateKeyError, WriteError
from database import get_db

# ==============================================================================
# CREATE OPERATIONS (C)
# ==============================================================================

def hash_password(password):
    """Generates salted SHA-256 hash for voter password."""
    if not password:
        return ""
    return hashlib.sha256(f"SECUREVOTE-PWD-SALT-2026:{password.strip()}".encode()).hexdigest()

def generate_next_voter_id():
    """
    Automatically generates the next sequential unique Voter ID (e.g. VTR-1001, VTR-1002, ...).
    Eliminates manual guessing or random ID generation by the user.
    """
    db = get_db()
    cursor = db.voters.find({"voter_id": {"$regex": r"^VTR-\d+$"}}, {"voter_id": 1, "_id": 0})
    highest_num = 1000
    for doc in cursor:
        vid = doc.get("voter_id", "")
        parts = vid.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            num = int(parts[1])
            if num > highest_num:
                highest_num = num

    total_count = db.voters.count_documents({})
    if 1000 + total_count > highest_num:
        highest_num = 1000 + total_count

    next_num = highest_num + 1
    while db.voters.find_one({"voter_id": f"VTR-{next_num}"}):
        next_num += 1

    return f"VTR-{next_num}"

def register_voter(voter_id=None, name="", email="", department="Computer Science", year_of_study=1, age=18, password=None, status="pending"):
    """
    Inserts a new voter into the 'voters' collection.
    If voter_id is not provided, automatically assigns the next sequential ID (e.g. VTR-1001).
    Sets status to 'pending' awaiting administrator verification.
    """
    db = get_db()
    if not voter_id:
        voter_id = generate_next_voter_id()
    else:
        voter_id = voter_id.strip().upper()

    voter_doc = {
        "voter_id": voter_id,
        "name": name.strip(),
        "email": email.strip().lower(),
        "department": department,
        "year_of_study": int(year_of_study),
        "age": int(age),
        "status": status,
        "created_at": datetime.now()
    }
    if password:
        voter_doc["password_hash"] = hash_password(password)

    try:
        result = db.voters.insert_one(voter_doc)
        log_audit_action("VOTER_REGISTERED", {"voter_id": voter_id, "email": email, "status": status})
        return {
            "success": True,
            "inserted_id": str(result.inserted_id),
            "voter_id": voter_id,
            "email": email.strip().lower(),
            "status": status,
            "message": f"Registration successful! Your official Voter ID is {voter_id}. Account is pending administrator verification."
        }
    except DuplicateKeyError as e:
        return {"success": False, "error": "Duplicate voter: An account with this Email address already exists."}
    except WriteError as e:
        return {"success": False, "error": f"MongoDB Schema Validation Failed: {e.details.get('errmsg', str(e))}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_voter_credentials(voter_id_or_email, password):
    """
    Authenticates a voter using their voter ID or email and password.
    Checks verification status.
    """
    db = get_db()
    identifier = voter_id_or_email.strip()
    voter = db.voters.find_one({
        "$or": [
            {"voter_id": identifier.upper()},
            {"email": identifier.lower()}
        ]
    })
    if not voter:
        return {"success": False, "error": f"No registered voter account found for '{identifier}'."}

    # Verify password if password_hash exists
    if voter.get("password_hash"):
        if hash_password(password) != voter.get("password_hash"):
            return {"success": False, "error": "Incorrect password. Please try again."}

    # Check status
    status = voter.get("status", "pending")
    if status == "pending":
        return {
            "success": False,
            "error": "Account Pending Verification: Your registration is currently awaiting verification by the Admin. You will be able to vote once approved.",
            "is_pending": True
        }
    if status == "suspended":
        return {"success": False, "error": "This voter account is currently suspended by the electoral commission."}
    if status != "active":
        return {"success": False, "error": f"Voter account status is '{status}'. Only active voters may enter the polling booth."}

    # Remove internal _id for JSON serialization
    voter_clean = dict(voter)
    voter_clean.pop("_id", None)
    voter_clean.pop("password_hash", None)
    return {"success": True, "voter": voter_clean}

def approve_voter(voter_id):
    """Approves a pending voter, making them eligible to vote."""
    db = get_db()
    res = db.voters.update_one(
        {"voter_id": voter_id.strip().upper()},
        {"$set": {"status": "active"}}
    )
    if res.matched_count == 0:
        return {"success": False, "error": f"Voter '{voter_id}' not found."}
    log_audit_action("VOTER_APPROVED", {"voter_id": voter_id, "approved_by": "yeswanthburle1432@gmail.com"})
    return {"success": True, "message": f"Voter '{voter_id}' successfully approved and granted voting eligibility!"}

def reject_voter(voter_id):
    """Rejects / deletes a voter application."""
    db = get_db()
    res = db.voters.delete_one({"voter_id": voter_id.strip().upper()})
    if res.deleted_count == 0:
        return {"success": False, "error": f"Voter '{voter_id}' not found."}
    log_audit_action("VOTER_REJECTED", {"voter_id": voter_id, "rejected_by": "yeswanthburle1432@gmail.com"})
    return {"success": True, "message": f"Voter registration '{voter_id}' rejected and removed."}

def list_pending_voters():
    """Lists all voters awaiting admin verification."""
    db = get_db()
    return list(db.voters.find({"status": "pending"}, {"_id": 0, "password_hash": 0}).sort("created_at", -1))

def clear_all_voters_and_votes():
    """
    Clears all existing voters and cast ballots as requested,
    allowing a clean fresh start where voters sign up individually.
    """
    db = get_db()
    db.voters.delete_many({})
    db.votes.delete_many({})
    db.candidates.update_many({}, {"$set": {"vote_count": 0}})
    log_audit_action("DATABASE_PURGED", {"action": "All existing voters and ballots reset for user-driven signup"})
    return {"success": True, "message": "All existing voters and cast votes have been cleared. Ready for fresh voter sign-ups!"}

def create_election(election_id, title, category, start_date, end_date, description=""):
    """
    Creates an election document.
    Demonstrates: db.elections.insert_one()
    """
    db = get_db()
    election_doc = {
        "election_id": election_id.strip().upper(),
        "title": title.strip(),
        "category": category,
        "status": "active",
        "start_date": start_date if isinstance(start_date, datetime) else datetime.fromisoformat(start_date),
        "end_date": end_date if isinstance(end_date, datetime) else datetime.fromisoformat(end_date),
        "description": description.strip()
    }
    try:
        result = db.elections.insert_one(election_doc)
        log_audit_action("ELECTION_CREATED", {"election_id": election_id, "title": title})
        return {"success": True, "inserted_id": str(result.inserted_id)}
    except DuplicateKeyError:
        return {"success": False, "error": f"Election ID '{election_id}' already exists."}
    except WriteError as e:
        return {"success": False, "error": f"Validation Error: {e.details.get('errmsg', str(e))}"}

def add_candidate(candidate_id, election_id, name, party_or_slate, manifesto, department):
    """
    Inserts a candidate for an election.
    Demonstrates: db.candidates.insert_one()
    """
    db = get_db()
    # Check that election exists
    if not db.elections.find_one({"election_id": election_id}):
        return {"success": False, "error": f"Election '{election_id}' does not exist."}

    candidate_doc = {
        "candidate_id": candidate_id.strip().upper(),
        "election_id": election_id.strip().upper(),
        "name": name.strip(),
        "party_or_slate": party_or_slate.strip(),
        "manifesto": manifesto.strip(),
        "department": department.strip(),
        "vote_count": int(0)
    }
    try:
        result = db.candidates.insert_one(candidate_doc)
        log_audit_action("CANDIDATE_ADDED", {"candidate_id": candidate_id, "election_id": election_id})
        return {"success": True, "inserted_id": str(result.inserted_id)}
    except DuplicateKeyError:
        return {"success": False, "error": f"Candidate ID '{candidate_id}' already exists."}
    except WriteError as e:
        return {"success": False, "error": f"Validation Error: {e.details.get('errmsg', str(e))}"}

def cast_vote(voter_id, election_id, candidate_id):
    """
    Records a vote with voter anonymity and double-vote protection.
    Demonstrates:
      - Voter verification with find_one()
      - SHA-256 voter ID hashing
      - Compound unique index conflict handling (DuplicateKeyError)
      - Atomic $inc update on candidates collection
      - Audit trail logging
    """
    db = get_db()
    voter_id_clean = voter_id.strip().upper()
    election_id_clean = election_id.strip().upper()
    candidate_id_clean = candidate_id.strip().upper()

    # 1. Verify Voter eligibility
    voter = db.voters.find_one({"voter_id": voter_id_clean})
    if not voter:
        return {"success": False, "error": f"Voter ID '{voter_id_clean}' not found in registry."}
    if voter.get("status") != "active":
        return {"success": False, "error": f"Voter account is '{voter.get('status')}', not eligible."}

    # 2. Verify Election status
    election = db.elections.find_one({"election_id": election_id_clean, "status": "active"})
    if not election:
        return {"success": False, "error": "Election is not active or does not exist."}

    # 3. Verify Candidate
    candidate = db.candidates.find_one({"candidate_id": candidate_id_clean, "election_id": election_id_clean})
    if not candidate:
        return {"success": False, "error": "Selected candidate does not exist in this election."}

    # 4. Generate Anonymized Voter Hash & Digital Receipt
    # Hash prevents ballot linkability while preserving uniqueness per election
    voter_hash = hashlib.sha256(f"{voter_id_clean}:{election_id_clean}:SALT-SECUREVOTE-2026".encode()).hexdigest()
    receipt_token = "RCPT-" + uuid.uuid4().hex[:12].upper()
    vote_id = "VOTE-" + uuid.uuid4().hex[:10].upper()

    vote_doc = {
        "vote_id": vote_id,
        "election_id": election_id_clean,
        "candidate_id": candidate_id_clean,
        "voter_id_hash": voter_hash,
        "department": voter.get("department"),
        "year_of_study": voter.get("year_of_study"),
        "timestamp": datetime.now(),
        "receipt_token": receipt_token
    }

    try:
        # Atomic Insert: Protected by Unique Compound Index (election_id + voter_id_hash)
        db.votes.insert_one(vote_doc)

        # Atomic Update: Increment Candidate Vote Count via PyMongo $inc operator
        db.candidates.update_one(
            {"candidate_id": candidate_id_clean, "election_id": election_id_clean},
            {"$inc": {"vote_count": 1}}
        )

        log_audit_action("VOTE_CAST", {
            "election_id": election_id_clean,
            "vote_id": vote_id,
            "department": voter.get("department")
        })

        return {
            "success": True,
            "message": "Vote successfully cast and cryptographically recorded!",
            "receipt_token": receipt_token,
            "vote_id": vote_id,
            "timestamp": vote_doc["timestamp"].isoformat(),
            "candidate_name": candidate["name"],
            "election_title": election["title"]
        }

    except DuplicateKeyError:
        return {
            "success": False,
            "error": "DUPLICATE VOTE REJECTED: You have ALREADY cast a vote in this election! One-person-one-vote rule enforced."
        }
    except Exception as e:
        return {"success": False, "error": f"Transaction failed: {str(e)}"}

def log_audit_action(action, details):
    """Logs system security and operation event."""
    db = get_db()
    try:
        db.audit_logs.insert_one({
            "log_id": "LOG-" + uuid.uuid4().hex[:8].upper(),
            "action": action,
            "timestamp": datetime.now(),
            "details": details
        })
    except Exception:
        pass

# ==============================================================================
# READ OPERATIONS (R)
# ==============================================================================

def get_voter(voter_id):
    """
    Finds a single voter by ID.
    Demonstrates: db.voters.find_one() with projection.
    """
    db = get_db()
    return db.voters.find_one({"voter_id": voter_id.strip().upper()}, {"_id": 0})

def list_voters(department=None, status="active", search=None, limit=50):
    """
    Queries voters with filters and projection.
    Demonstrates: db.voters.find() with $eq, $regex, projection, and sort.
    """
    db = get_db()
    query = {}
    if department and department != "All":
        query["department"] = department
    if status and status != "All":
        query["status"] = status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"voter_id": {"$regex": search, "$options": "i"}}
        ]
    
    # Projection: excluding MongoDB internal _id
    projection = {"_id": 0, "voter_id": 1, "name": 1, "email": 1, "department": 1, "year_of_study": 1, "age": 1, "status": 1}
    voters = list(db.voters.find(query, projection).sort("name", 1).limit(limit))
    return voters

def list_elections(status=None):
    """
    Lists elections with optional status filter.
    Demonstrates: db.elections.find()
    """
    db = get_db()
    query = {}
    if status and status != "All":
        query["status"] = status
    elections = list(db.elections.find(query, {"_id": 0}).sort("start_date", -1))
    # Convert datetime to ISO string for JSON serialization
    for ele in elections:
        if "start_date" in ele and isinstance(ele["start_date"], datetime):
            ele["start_date"] = ele["start_date"].strftime("%Y-%m-%d %H:%M")
        if "end_date" in ele and isinstance(ele["end_date"], datetime):
            ele["end_date"] = ele["end_date"].strftime("%Y-%m-%d %H:%M")
    return elections

def get_election(election_id):
    """Returns single election detail."""
    db = get_db()
    ele = db.elections.find_one({"election_id": election_id.strip().upper()}, {"_id": 0})
    if ele:
        if "start_date" in ele and isinstance(ele["start_date"], datetime):
            ele["start_date"] = ele["start_date"].strftime("%Y-%m-%d %H:%M")
        if "end_date" in ele and isinstance(ele["end_date"], datetime):
            ele["end_date"] = ele["end_date"].strftime("%Y-%m-%d %H:%M")
    return ele

def list_candidates_by_election(election_id):
    """
    Lists all candidates for an election, sorted by candidate_id.
    Demonstrates: db.candidates.find()
    """
    db = get_db()
    return list(db.candidates.find({"election_id": election_id.strip().upper()}, {"_id": 0}).sort("candidate_id", 1))

def check_if_voted(voter_id, election_id):
    """
    Checks whether a voter has already cast a ballot in the specified election.
    """
    db = get_db()
    voter_hash = hashlib.sha256(f"{voter_id.strip().upper()}:{election_id.strip().upper()}:SALT-SECUREVOTE-2026".encode()).hexdigest()
    vote = db.votes.find_one({"election_id": election_id.strip().upper(), "voter_id_hash": voter_hash}, {"_id": 0, "receipt_token": 1, "timestamp": 1})
    if vote:
        return {
            "has_voted": True,
            "receipt_token": vote.get("receipt_token"),
            "timestamp": vote["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(vote.get("timestamp"), datetime) else str(vote.get("timestamp"))
        }
    return {"has_voted": False}

def list_audit_logs(limit=25):
    """Returns latest audit log entries."""
    db = get_db()
    logs = list(db.audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    for log in logs:
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return logs

# ==============================================================================
# UPDATE OPERATIONS (U)
# ==============================================================================

def update_candidate_manifesto(candidate_id, new_manifesto):
    """
    Updates a candidate's manifesto using $set operator.
    Demonstrates: db.candidates.update_one() with $set
    """
    db = get_db()
    result = db.candidates.update_one(
        {"candidate_id": candidate_id.strip().upper()},
        {"$set": {"manifesto": new_manifesto.strip()}}
    )
    if result.matched_count == 0:
        return {"success": False, "error": f"Candidate '{candidate_id}' not found."}
    log_audit_action("CANDIDATE_MANIFESTO_UPDATED", {"candidate_id": candidate_id})
    return {"success": True, "modified_count": result.modified_count}

def update_election_status(election_id, new_status):
    """
    Updates election lifecycle status (draft, active, completed).
    Demonstrates: db.elections.update_one() with $set
    """
    db = get_db()
    if new_status not in ["draft", "active", "completed"]:
        return {"success": False, "error": "Invalid status. Must be draft, active, or completed."}
    result = db.elections.update_one(
        {"election_id": election_id.strip().upper()},
        {"$set": {"status": new_status}}
    )
    if result.matched_count == 0:
        return {"success": False, "error": f"Election '{election_id}' not found."}
    log_audit_action("ELECTION_STATUS_CHANGED", {"election_id": election_id, "new_status": new_status})
    return {"success": True, "modified_count": result.modified_count}

def update_voter_department(voter_id, new_department):
    """
    Updates voter's department with schema enum validation.
    Demonstrates: db.voters.update_one() with $set
    """
    db = get_db()
    try:
        result = db.voters.update_one(
            {"voter_id": voter_id.strip().upper()},
            {"$set": {"department": new_department}}
        )
        if result.matched_count == 0:
            return {"success": False, "error": f"Voter '{voter_id}' not found."}
        log_audit_action("VOTER_UPDATED", {"voter_id": voter_id, "new_department": new_department})
        return {"success": True, "modified_count": result.modified_count}
    except WriteError as e:
        return {"success": False, "error": f"Schema Validation Error: {e.details.get('errmsg', str(e))}"}

def update_election(election_id, title=None, category=None, description=None, start_date=None, end_date=None):
    """
    Updates election metadata (title, category, description, dates).
    Demonstrates: db.elections.update_one() with $set
    """
    db = get_db()
    update_doc = {}
    if title:
        update_doc["title"] = title.strip()
    if category:
        update_doc["category"] = category.strip()
    if description is not None:
        update_doc["description"] = description.strip()
    if start_date:
        update_doc["start_date"] = start_date if isinstance(start_date, datetime) else datetime.fromisoformat(start_date)
    if end_date:
        update_doc["end_date"] = end_date if isinstance(end_date, datetime) else datetime.fromisoformat(end_date)
    
    if not update_doc:
        return {"success": False, "error": "No update fields provided."}

    try:
        result = db.elections.update_one(
            {"election_id": election_id.strip().upper()},
            {"$set": update_doc}
        )
        if result.matched_count == 0:
            return {"success": False, "error": f"Election '{election_id}' not found."}
        log_audit_action("ELECTION_UPDATED", {"election_id": election_id, "updated_fields": list(update_doc.keys())})
        return {"success": True, "modified_count": result.modified_count}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_voter_status(voter_id, new_status):
    """
    Updates a voter's status ('active', 'suspended', 'graduated').
    Demonstrates: db.voters.update_one() with $set
    """
    db = get_db()
    if new_status not in ["active", "suspended", "graduated"]:
        return {"success": False, "error": "Invalid status. Must be active, suspended, or graduated."}
    try:
        result = db.voters.update_one(
            {"voter_id": voter_id.strip().upper()},
            {"$set": {"status": new_status}}
        )
        if result.matched_count == 0:
            return {"success": False, "error": f"Voter '{voter_id}' not found."}
        log_audit_action("VOTER_STATUS_CHANGED", {"voter_id": voter_id, "new_status": new_status})
        return {"success": True, "modified_count": result.modified_count}
    except WriteError as e:
        return {"success": False, "error": f"Schema Validation Error: {e.details.get('errmsg', str(e))}"}

def get_voter_ballots(voter_id):
    """
    Retrieves all elections with status for a specific voter.
    Checks voting history and returns receipt token if ballot cast.
    """
    db = get_db()
    voter_id_clean = voter_id.strip().upper()
    elections = list_elections(status="All")
    result = []
    for ele in elections:
        ele_id = ele["election_id"]
        v_status = check_if_voted(voter_id_clean, ele_id)
        candidate_count = db.candidates.count_documents({"election_id": ele_id})
        total_votes = db.votes.count_documents({"election_id": ele_id})
        ele_copy = dict(ele)
        ele_copy["has_voted"] = v_status["has_voted"]
        ele_copy["receipt_token"] = v_status.get("receipt_token")
        ele_copy["voted_timestamp"] = v_status.get("timestamp")
        ele_copy["candidate_count"] = candidate_count
        ele_copy["total_votes"] = total_votes
        result.append(ele_copy)
    return result

# ==============================================================================
# DELETE OPERATIONS (D)
# ==============================================================================

def delete_election(election_id):
    """
    Deletes an election if zero votes have been cast.
    Also cleans up associated candidates.
    Demonstrates: db.elections.delete_one(), db.candidates.delete_many()
    """
    db = get_db()
    election_id_clean = election_id.strip().upper()
    ele = db.elections.find_one({"election_id": election_id_clean})
    if not ele:
        return {"success": False, "error": f"Election '{election_id_clean}' not found."}
    
    votes_count = db.votes.count_documents({"election_id": election_id_clean})
    if votes_count > 0:
        return {"success": False, "error": f"Cannot delete election: {votes_count} ballot(s) have already been recorded!"}
    
    # Delete election and its candidates
    db.candidates.delete_many({"election_id": election_id_clean})
    result = db.elections.delete_one({"election_id": election_id_clean})
    log_audit_action("ELECTION_DELETED", {"election_id": election_id_clean})
    return {"success": True, "deleted_count": result.deleted_count}

def delete_candidate(candidate_id):
    """
    Deletes a candidate if the election has not started or has zero votes.
    Demonstrates: db.candidates.delete_one()
    """
    db = get_db()
    cand = db.candidates.find_one({"candidate_id": candidate_id.strip().upper()})
    if not cand:
        return {"success": False, "error": f"Candidate '{candidate_id}' not found."}
    if cand.get("vote_count", 0) > 0:
        return {"success": False, "error": "Cannot delete candidate after votes have been received!"}
    
    result = db.candidates.delete_one({"candidate_id": candidate_id.strip().upper()})
    log_audit_action("CANDIDATE_DELETED", {"candidate_id": candidate_id})
    return {"success": True, "deleted_count": result.deleted_count}

def delete_voter(voter_id):
    """
    Removes an unverified or inactive voter from the registry.
    Demonstrates: db.voters.delete_one()
    """
    db = get_db()
    result = db.voters.delete_one({"voter_id": voter_id.strip().upper()})
    if result.deleted_count == 0:
        return {"success": False, "error": f"Voter '{voter_id}' not found."}
    log_audit_action("VOTER_DELETED", {"voter_id": voter_id})
    return {"success": True, "deleted_count": result.deleted_count}
