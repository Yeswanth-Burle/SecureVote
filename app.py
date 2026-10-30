"""
app.py - Flask Web Application for SecureVote
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System using PyMongo & MongoDB
"""

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import json
from database import get_db, setup_database
import crud
import analytics
import seed_data
import mailer

app = Flask(__name__)
app.secret_key = "securevote_cse494_secret_session_key_2026_nosql"

# ==============================================================================
# DESIGNATED ELECTORAL COMMISSION ADMINISTRATOR
# ==============================================================================
ADMIN_EMAIL = "yeswanthburle1432@gmail.com"
ADMIN_PASSWORD = "Yash@1432"

# ==============================================================================
# AUTHENTICATION & ROLE-BASED ACCESS CONTROL ROUTES
# ==============================================================================

@app.route("/api/auth/current-user", methods=["GET"])
def get_current_user():
    """Returns current active session details (guest, voter, or admin)."""
    role = session.get("role", "guest")
    is_admin = session.get("is_admin", False)
    voter_id = session.get("voter_id")
    voter_info = None
    if voter_id:
        voter_info = crud.get_voter(voter_id)
        if voter_info:
            voter_info.pop("password_hash", None)
    return jsonify({
        "success": True,
        "logged_in": role != "guest",
        "role": role,
        "is_admin": is_admin,
        "voter": voter_info,
        "admin_email": session.get("admin_email") if is_admin else None
    })

# --- ADMIN PASSWORD AUTHENTICATION ---

@app.route("/api/auth/admin-login", methods=["POST"])
def admin_login():
    """
    Authenticates the designated Electoral Commission Administrator using
    their permanent password (Yash@1432).
    """
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or "yeswanth" in email:
        email = ADMIN_EMAIL.lower()

    if email != ADMIN_EMAIL.lower():
        return jsonify({
            "success": False,
            "error": f"Access Restricted: Only the registered Electoral Administrator ({ADMIN_EMAIL}) is authorized to access the Commission Portal."
        }), 403

    if password != ADMIN_PASSWORD:
        return jsonify({
            "success": False,
            "error": "Invalid administrator password. Access denied."
        }), 401

    # Password Verified! Unlock Admin Session
    session["role"] = "admin"
    session["is_admin"] = True
    session["admin_email"] = ADMIN_EMAIL
    session["voter_id"] = None
    session.modified = True

    crud.log_audit_action("ADMIN_AUTHENTICATED", {
        "email": ADMIN_EMAIL,
        "method": "permanent_password",
        "status": "authorized",
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({
        "success": True,
        "message": "Administrator authenticated successfully. Commission portal unlocked.",
        "admin_email": ADMIN_EMAIL
    })

@app.route("/api/auth/admin-verify-otp", methods=["POST"])
def admin_verify_otp():
    """
    Backward-compatibility route that accepts permanent password as well.
    """
    data = request.json or {}
    password = (data.get("password") or data.get("otp") or "").strip()
    if password == ADMIN_PASSWORD:
        session["role"] = "admin"
        session["is_admin"] = True
        session["admin_email"] = ADMIN_EMAIL
        session["voter_id"] = None
        session.modified = True
        crud.log_audit_action("ADMIN_AUTHENTICATED", {
            "email": ADMIN_EMAIL,
            "method": "permanent_password_compat",
            "status": "authorized",
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({
            "success": True,
            "message": "Administrator authenticated successfully. Commission portal unlocked.",
            "admin_email": ADMIN_EMAIL
        })
    return admin_login()

@app.route("/api/auth/admin-request-otp", methods=["POST"])
def admin_request_otp():
    """Deprecated endpoint notice."""
    return jsonify({
        "success": True,
        "message": "OTP verification has been replaced with permanent password authentication.",
        "email": ADMIN_EMAIL
    })

# --- VOTER SIGNUP & LOGIN ---

@app.route("/api/auth/voter-signup", methods=["POST"])
def voter_signup():
    """
    Allows a student / citizen to create their voter account.
    The account is saved with status 'pending' awaiting administrator verification.
    """
    data = request.json or {}
    voter_id = (data.get("voter_id") or "").strip().upper()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    dept = data.get("department", "Computer Science")
    year = int(data.get("year_of_study", 1))
    age = int(data.get("age", 18))

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Please provide your Full Legal Name, University Email, and Password."}), 400

    if len(password) < 4:
        return jsonify({"success": False, "error": "Password must be at least 4 characters long."}), 400

    res = crud.register_voter(
        voter_id=voter_id or None,
        name=name,
        email=email,
        department=dept,
        year_of_study=year,
        age=age,
        password=password,
        status="pending"
    )
    return jsonify(res)

@app.route("/api/auth/voter-login", methods=["POST"])
def voter_login():
    """
    Authenticates a voter using their credentials and checks admin approval.
    """
    data = request.json or {}
    identifier = (data.get("voter_id") or data.get("email") or "").strip()
    password = (data.get("password") or data.get("passcode") or "").strip()

    if not identifier:
        return jsonify({"success": False, "error": "Please enter your Voter ID or Email."})

    res = crud.verify_voter_credentials(identifier, password)
    if not res.get("success"):
        return jsonify(res), 401

    voter = res["voter"]
    session["role"] = "voter"
    session["voter_id"] = voter["voter_id"]
    session["is_admin"] = False
    session.modified = True

    crud.log_audit_action("VOTER_AUTHENTICATED", {"voter_id": voter["voter_id"], "name": voter.get("name")})
    return jsonify({
        "success": True,
        "message": f"Welcome, {voter.get('name')}! Identity verified and eligible.",
        "voter": voter
    })

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """Clears user session and logs the exit event."""
    role = session.get("role", "guest")
    user = session.get("voter_id") or session.get("admin_email") or "guest"
    session.clear()
    session.modified = True
    crud.log_audit_action("SESSION_LOGOUT", {"user": user, "previous_role": role})
    return jsonify({"success": True, "message": "Logged out successfully."})

# ==============================================================================
# ADMIN VOTER ELIGIBILITY & APPROVAL MANAGEMENT ROUTES
# ==============================================================================

@app.route("/api/admin/pending-voters", methods=["GET"])
def get_pending_voters():
    """Retrieves all voter registrations awaiting administrator approval."""
    pending = crud.list_pending_voters()
    return jsonify({"success": True, "pending_voters": pending, "count": len(pending)})

@app.route("/api/admin/approve-voter", methods=["POST"])
def post_approve_voter():
    """Approves a voter registration, enabling them to vote."""
    data = request.json or {}
    voter_id = data.get("voter_id")
    if not voter_id:
        return jsonify({"success": False, "error": "Voter ID is required."}), 400
    res = crud.approve_voter(voter_id)
    return jsonify(res)

@app.route("/api/admin/reject-voter", methods=["POST"])
def post_reject_voter():
    """Rejects / removes a voter registration application."""
    data = request.json or {}
    voter_id = data.get("voter_id")
    if not voter_id:
        return jsonify({"success": False, "error": "Voter ID is required."}), 400
    res = crud.reject_voter(voter_id)
    return jsonify(res)

@app.route("/api/admin/purge-voters", methods=["POST"])
def post_purge_voters():
    """Clears all legacy voter documents and cast votes for a fresh sign-up start."""
    res = crud.clear_all_voters_and_votes()
    return jsonify(res)

# ==============================================================================
# ADMIN ELECTION ACCEPTANCE & CLOSING LIFECYCLE
# ==============================================================================

@app.route("/api/admin/accept-election", methods=["POST"])
def post_accept_election():
    """Admin approves and opens an election for live voting."""
    data = request.json or {}
    election_id = data.get("election_id")
    if not election_id:
        return jsonify({"success": False, "error": "Election ID required."}), 400
    res = crud.update_election_status(election_id, "active")
    crud.log_audit_action("ELECTION_ACCEPTED_BY_ADMIN", {"election_id": election_id, "admin": ADMIN_EMAIL})
    return jsonify(res)

@app.route("/api/admin/close-election", methods=["POST"])
def post_close_election():
    """Admin terminates voting and closes the election to certify results."""
    data = request.json or {}
    election_id = data.get("election_id")
    if not election_id:
        return jsonify({"success": False, "error": "Election ID required."}), 400
    res = crud.update_election_status(election_id, "completed")
    crud.log_audit_action("ELECTION_CLOSED_BY_ADMIN", {"election_id": election_id, "admin": ADMIN_EMAIL})
    return jsonify(res)

# ==============================================================================
# PAGE ROUTES
# ==============================================================================

@app.route("/")
def index():
    """Renders the main single-page application dashboard."""
    return render_template("index.html")

# ==============================================================================
# API ROUTES: ELECTIONS & CANDIDATES
# ==============================================================================

@app.route("/api/elections", methods=["GET"])
def get_elections():
    status = request.args.get("status")
    if not status:
        if session.get("is_admin"):
            status = "All"
        else:
            status = "active"
    elections = crud.list_elections(status=status)
    return jsonify({"success": True, "elections": elections})

@app.route("/api/elections", methods=["POST"])
def post_election():
    data = request.json or {}
    res = crud.create_election(
        election_id=data.get("election_id", ""),
        title=data.get("title", ""),
        category=data.get("category", "Student Council"),
        start_date=data.get("start_date", datetime.now().isoformat()),
        end_date=data.get("end_date", datetime.now().isoformat()),
        description=data.get("description", "")
    )
    return jsonify(res)

@app.route("/api/elections/<election_id>", methods=["PUT"])
def put_election(election_id):
    data = request.json or {}
    res = crud.update_election(
        election_id=election_id,
        title=data.get("title"),
        category=data.get("category"),
        description=data.get("description"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date")
    )
    return jsonify(res)

@app.route("/api/elections/<election_id>/status", methods=["PUT"])
def put_election_status(election_id):
    data = request.json or {}
    new_status = data.get("status")
    res = crud.update_election_status(election_id, new_status)
    return jsonify(res)

@app.route("/api/elections/<election_id>", methods=["DELETE"])
def delete_election(election_id):
    res = crud.delete_election(election_id)
    return jsonify(res)

@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    election_id = request.args.get("election_id", "ELEC-2026-PRES")
    candidates = crud.list_candidates_by_election(election_id)
    return jsonify({"success": True, "candidates": candidates})

@app.route("/api/candidates", methods=["POST"])
def post_candidate():
    data = request.json or {}
    res = crud.add_candidate(
        candidate_id=data.get("candidate_id", ""),
        election_id=data.get("election_id", ""),
        name=data.get("name", ""),
        party_or_slate=data.get("party_or_slate", ""),
        manifesto=data.get("manifesto", ""),
        department=data.get("department", "")
    )
    return jsonify(res)

@app.route("/api/candidates/<candidate_id>/manifesto", methods=["PUT"])
def put_candidate_manifesto(candidate_id):
    data = request.json or {}
    res = crud.update_candidate_manifesto(candidate_id, data.get("manifesto", ""))
    return jsonify(res)

@app.route("/api/candidates/<candidate_id>", methods=["DELETE"])
def delete_candidate(candidate_id):
    res = crud.delete_candidate(candidate_id)
    return jsonify(res)

# ==============================================================================
# API ROUTES: VOTERS
# ==============================================================================

@app.route("/api/voters", methods=["GET"])
def get_voters():
    dept = request.args.get("department", "All")
    status = request.args.get("status", "All")
    search = request.args.get("search", "")
    voters = crud.list_voters(department=dept, status=status, search=search, limit=100)
    return jsonify({"success": True, "voters": voters})

@app.route("/api/voters", methods=["POST"])
def post_voter():
    data = request.json or {}
    try:
        res = crud.register_voter(
            voter_id=data.get("voter_id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            department=data.get("department", "Computer Science"),
            year_of_study=int(data.get("year_of_study", 1)),
            age=int(data.get("age", 18))
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/voters/<voter_id>/status", methods=["GET"])
def get_voter_status(voter_id):
    election_id = request.args.get("election_id", "ELEC-2026-PRES")
    voter = crud.get_voter(voter_id)
    if not voter:
        return jsonify({"success": False, "error": "Voter ID not found in database."})
    
    voting_status = crud.check_if_voted(voter_id, election_id)
    return jsonify({
        "success": True,
        "voter": voter,
        "has_voted": voting_status["has_voted"],
        "receipt_token": voting_status.get("receipt_token"),
        "timestamp": voting_status.get("timestamp")
    })

@app.route("/api/voters/<voter_id>/status", methods=["PUT"])
def put_voter_status(voter_id):
    data = request.json or {}
    new_status = data.get("status")
    res = crud.update_voter_status(voter_id, new_status)
    return jsonify(res)

@app.route("/api/voters/<voter_id>", methods=["DELETE"])
def delete_voter(voter_id):
    res = crud.delete_voter(voter_id)
    return jsonify(res)

@app.route("/api/voter/my-ballots", methods=["GET"])
def get_voter_my_ballots():
    voter_id = request.args.get("voter_id") or session.get("voter_id")
    if not voter_id:
        return jsonify({"success": False, "error": "Voter identity required."}), 400
    ballots = crud.get_voter_ballots(voter_id)
    return jsonify({"success": True, "voter_id": voter_id, "ballots": ballots})

# ==============================================================================
# API ROUTES: VOTING
# ==============================================================================

@app.route("/api/vote", methods=["POST"])
def post_vote():
    data = request.json or {}
    voter_id = data.get("voter_id")
    election_id = data.get("election_id")
    candidate_id = data.get("candidate_id")

    if not voter_id or not election_id or not candidate_id:
        return jsonify({"success": False, "error": "Missing voter_id, election_id, or candidate_id"})

    # If session is logged in as a voter, prevent impersonation
    if session.get("role") == "voter" and session.get("voter_id"):
        if session.get("voter_id").upper() != voter_id.strip().upper():
            return jsonify({"success": False, "error": "Identity mismatch: You may only vote using your authenticated voter credentials."}), 403

    result = crud.cast_vote(voter_id, election_id, candidate_id)
    return jsonify(result)

# ==============================================================================
# API ROUTES: ADMIN DATABASE RESET
# ==============================================================================

@app.route("/api/admin/reset-database", methods=["POST"])
def admin_reset_database():
    try:
        seed_data.seed_all()
        crud.log_audit_action("DATABASE_RESET", {"initiated_by": session.get("admin_username", "admin")})
        return jsonify({"success": True, "message": "Database reset and re-seeded with demo records!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================================================
# API ROUTES: ANALYTICS & AGGREGATIONS
# ==============================================================================

@app.route("/api/analytics/overview", methods=["GET"])
def get_analytics_overview():
    db = get_db()
    election_id = request.args.get("election_id", "ELEC-2026-PRES")

    election = db.elections.find_one({"election_id": election_id}, {"_id": 0}) or {}

    total_voters = db.voters.count_documents({"status": "active"})
    total_ballots = db.votes.count_documents({"election_id": election_id})
    turnout_pct = round((total_ballots / total_voters * 100), 1) if total_voters > 0 else 0

    results = analytics.execute_results_pipeline(election_id)
    turnout_dept = analytics.execute_department_turnout(election_id)
    timeline = analytics.execute_timeline(election_id)

    return jsonify({
        "success": True,
        "election": election,
        "metrics": {
            "total_voters": total_voters,
            "total_ballots": total_ballots,
            "turnout_pct": turnout_pct,
            "leader": results.get("leader")
        },
        "results": results["candidates"],
        "department_turnout": turnout_dept["turnout"],
        "timeline": timeline["timeline"]
    })

@app.route("/api/analytics/pipeline/<pipeline_name>", methods=["GET"])
def run_viva_pipeline(pipeline_name):
    """
    Endpoint for Aggregation Viva Lab: executes selected pipeline and returns
    its human explanation, MQL stages, and live execution output.
    """
    election_id = request.args.get("election_id", "ELEC-2026-PRES")
    desc = analytics.PIPELINE_DESCRIPTIONS.get(pipeline_name, {})

    output = {}
    mql = []

    if pipeline_name == "results":
        res = analytics.execute_results_pipeline(election_id)
        output = res["candidates"]
        mql = res["pipeline_mql"]
    elif pipeline_name == "turnout":
        res = analytics.execute_department_turnout(election_id)
        output = res["turnout"]
        mql = res["pipeline_mql"]
    elif pipeline_name == "timeline":
        res = analytics.execute_timeline(election_id)
        output = res["timeline"]
        mql = res["pipeline_mql"]
    elif pipeline_name == "demographics":
        res = analytics.execute_demographics(election_id)
        output = res["demographics"]
        mql = res["pipeline_mql"]
    elif pipeline_name == "facet":
        res = analytics.execute_facet_summary(election_id)
        output = res["facet_data"]
        mql = res["pipeline_mql"]
    else:
        return jsonify({"success": False, "error": "Unknown pipeline requested"}), 400

    return jsonify({
        "success": True,
        "pipeline_name": pipeline_name,
        "info": desc,
        "mql_stages": mql,
        "live_output": output
    })

@app.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    logs = crud.list_audit_logs(limit=30)
    return jsonify({"success": True, "logs": logs})

@app.route("/api/schema-test", methods=["POST"])
def test_schema_validation():
    """
    Intentionally attempts an insertion with arbitrary fields to test MongoDB's
    $jsonSchema validation rules and returns the exact engine response.
    """
    data = request.json or {}
    collection_name = data.get("collection", "voters")
    document = data.get("document", {})
    db = get_db()
    
    # Process types if testing voter
    if collection_name == "voters" and "age" in document:
        try:
            document["age"] = int(document["age"])
        except Exception:
            pass
    if collection_name == "voters" and "year_of_study" in document:
        try:
            document["year_of_study"] = int(document["year_of_study"])
        except Exception:
            pass
    document["created_at"] = datetime.now()

    try:
        res = db[collection_name].insert_one(document)
        # Remove it immediately so it doesn't pollute real data
        db[collection_name].delete_one({"_id": res.inserted_id})
        return jsonify({
            "success": True,
            "message": "Validation PASSED: Document conforms strictly to MongoDB $jsonSchema rules!"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "explanation": "MongoDB rejected this document because it violated the collection's $jsonSchema validator rules."
        })

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("\n" + "="*60)
    print("  [ONLINE] SecureVote Server Running on http://127.0.0.1:5000")
    print("  CSE494 Intelligent NoSQL Databases Project")
    print("="*60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
