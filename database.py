"""
database.py - MongoDB Connection, Collection Setup, and Schema Validation Rules
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System using PyMongo & MongoDB
"""

import pymongo
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure
import datetime
import sys

# MongoDB Connection Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "voting_system_db"

def get_client():
    """Returns a MongoClient instance."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Verify connection
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB at {MONGO_URI}: {e}")
        return None

def get_db():
    """Returns the database instance."""
    client = get_client()
    if client is not None:
        return client[DB_NAME]
    return None

# ==============================================================================
# MONGODB $jsonSchema VALIDATION RULES
# ==============================================================================

# 1. Voters Schema Validation
# Ensures voter_id is unique, email has valid syntax, age >= 18, department is specified
VOTER_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["voter_id", "name", "email", "department", "year_of_study", "age", "status"],
        "properties": {
            "voter_id": {
                "bsonType": "string",
                "pattern": "^[A-Z0-9_-]{3,20}$",
                "description": "Must be a string between 3 and 20 alphanumeric characters"
            },
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 80,
                "description": "Must be a string between 2 and 80 characters"
            },
            "email": {
                "bsonType": "string",
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "description": "Must be a valid email address matching standard email format"
            },
            "department": {
                "bsonType": "string",
                "enum": ["Computer Science", "Electronics", "Mechanical", "Management", "Biotechnology", "Civil"],
                "description": "Must be one of the recognized university departments"
            },
            "year_of_study": {
                "bsonType": "int",
                "minimum": 1,
                "maximum": 5,
                "description": "Year of study must be between 1 and 5"
            },
            "age": {
                "bsonType": "int",
                "minimum": 18,
                "maximum": 100,
                "description": "Voter must be at least 18 years old to vote"
            },
            "status": {
                "bsonType": "string",
                "enum": ["active", "suspended", "graduated", "pending"],
                "description": "Status must be active, suspended, graduated, or pending approval"
            },
            "password_hash": {
                "bsonType": "string",
                "description": "Hashed password for voter authentication"
            },
            "created_at": {
                "bsonType": "date",
                "description": "Creation timestamp"
            }
        }
    }
}

# 2. Elections Schema Validation
# Validates election fields and enforces lifecycle status
ELECTION_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["election_id", "title", "category", "status", "start_date", "end_date"],
        "properties": {
            "election_id": {
                "bsonType": "string",
                "description": "Unique election identifier"
            },
            "title": {
                "bsonType": "string",
                "minLength": 3,
                "maxLength": 120,
                "description": "Title must be between 3 and 120 characters"
            },
            "category": {
                "bsonType": "string",
                "enum": ["Student Council", "Departmental", "Club & Society", "Sports Board"],
                "description": "Category must belong to official election types"
            },
            "status": {
                "bsonType": "string",
                "enum": ["draft", "active", "completed", "closed"],
                "description": "Status must be draft, active, completed, or closed"
            },
            "start_date": {
                "bsonType": "date",
                "description": "Start timestamp of the election"
            },
            "end_date": {
                "bsonType": "date",
                "description": "End timestamp of the election"
            },
            "description": {
                "bsonType": "string"
            }
        }
    }
}

# 3. Candidates Schema Validation
CANDIDATE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["candidate_id", "election_id", "name", "party_or_slate", "manifesto", "department", "vote_count"],
        "properties": {
            "candidate_id": {
                "bsonType": "string",
                "description": "Unique candidate identifier"
            },
            "election_id": {
                "bsonType": "string",
                "description": "Foreign reference to elections collection"
            },
            "name": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 80
            },
            "party_or_slate": {
                "bsonType": "string",
                "minLength": 2,
                "maxLength": 60
            },
            "manifesto": {
                "bsonType": "string",
                "minLength": 10
            },
            "department": {
                "bsonType": "string"
            },
            "vote_count": {
                "bsonType": "int",
                "minimum": 0,
                "description": "Non-negative vote tally, updated atomically"
            }
        }
    }
}

# 4. Votes Schema Validation
VOTE_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["vote_id", "election_id", "candidate_id", "voter_id_hash", "department", "year_of_study", "timestamp", "receipt_token"],
        "properties": {
            "vote_id": {
                "bsonType": "string",
                "description": "Unique vote GUID"
            },
            "election_id": {
                "bsonType": "string",
                "description": "Reference to election"
            },
            "candidate_id": {
                "bsonType": "string",
                "description": "Reference to candidate"
            },
            "voter_id_hash": {
                "bsonType": "string",
                "description": "SHA-256 hash of voter ID ensuring ballot secrecy while preventing double voting"
            },
            "department": {
                "bsonType": "string"
            },
            "year_of_study": {
                "bsonType": "int"
            },
            "timestamp": {
                "bsonType": "date"
            },
            "receipt_token": {
                "bsonType": "string",
                "description": "Cryptographic receipt proof for the voter"
            }
        }
    }
}

# 5. Audit Log Schema Validation
AUDIT_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["log_id", "action", "timestamp", "details"],
        "properties": {
            "log_id": { "bsonType": "string" },
            "action": { "bsonType": "string" },
            "timestamp": { "bsonType": "date" },
            "details": { "bsonType": "object" }
        }
    }
}


def setup_database(drop_existing=False):
    """
    Initializes the database, creates collections with $jsonSchema validation,
    and establishes compound and unique indexes.
    """
    client = get_client()
    if client is None:
        raise ConnectionError("Cannot reach MongoDB service.")
    
    db = client[DB_NAME]
    
    if drop_existing:
        print(f"[SETUP] Dropping existing database '{DB_NAME}' for clean installation...")
        client.drop_database(DB_NAME)
    
    collection_configs = [
        ("voters", VOTER_VALIDATOR),
        ("elections", ELECTION_VALIDATOR),
        ("candidates", CANDIDATE_VALIDATOR),
        ("votes", VOTE_VALIDATOR),
        ("audit_logs", AUDIT_VALIDATOR)
    ]
    
    existing_collections = db.list_collection_names()
    
    for coll_name, validator in collection_configs:
        if coll_name not in existing_collections:
            try:
                db.create_collection(
                    coll_name,
                    validator=validator,
                    validationLevel="strict",
                    validationAction="error"
                )
                print(f"[SETUP] Created collection '{coll_name}' with $jsonSchema validator.")
            except CollectionInvalid:
                pass
        else:
            # Update validator if collection already exists
            try:
                db.command({
                    "collMod": coll_name,
                    "validator": validator,
                    "validationLevel": "strict",
                    "validationAction": "error"
                })
                print(f"[SETUP] Updated validator for existing collection '{coll_name}'.")
            except Exception as e:
                print(f"[SETUP] Note on updating validator for {coll_name}: {e}")
                
    # ==============================================================================
    # CREATE INDEXES FOR INTEGRITY AND QUERY PERFORMANCE
    # ==============================================================================
    
    # Voters: Unique index on voter_id and email
    db.voters.create_index([("voter_id", pymongo.ASCENDING)], unique=True, name="idx_unique_voter_id")
    db.voters.create_index([("email", pymongo.ASCENDING)], unique=True, name="idx_unique_email")
    db.voters.create_index([("department", pymongo.ASCENDING)], name="idx_voter_department")

    # Elections: Unique election_id
    db.elections.create_index([("election_id", pymongo.ASCENDING)], unique=True, name="idx_unique_election_id")
    db.elections.create_index([("status", pymongo.ASCENDING)], name="idx_election_status")

    # Candidates: Unique candidate_id
    db.candidates.create_index([("candidate_id", pymongo.ASCENDING)], unique=True, name="idx_unique_candidate_id")
    db.candidates.create_index([("election_id", pymongo.ASCENDING)], name="idx_candidate_election")

    # Votes: CRITICAL COMPOUND UNIQUE INDEX!
    # Enforces at MongoDB database engine level that ONE voter can vote at most ONCE in a specific election!
    db.votes.create_index(
        [("election_id", pymongo.ASCENDING), ("voter_id_hash", pymongo.ASCENDING)],
        unique=True,
        name="idx_unique_election_voter_hash"
    )
    db.votes.create_index([("candidate_id", pymongo.ASCENDING)], name="idx_vote_candidate")
    db.votes.create_index([("department", pymongo.ASCENDING)], name="idx_vote_department")
    db.votes.create_index([("timestamp", pymongo.DESCENDING)], name="idx_vote_timestamp")

    # Audit Logs
    db.audit_logs.create_index([("timestamp", pymongo.DESCENDING)], name="idx_audit_timestamp")

    print("[SETUP] Indexes verified successfully.")
    return db

if __name__ == "__main__":
    drop_flag = "--reset" in sys.argv
    db = setup_database(drop_existing=drop_flag)
    print(f"[SUCCESS] Database '{DB_NAME}' initialized with collections: {db.list_collection_names()}")
