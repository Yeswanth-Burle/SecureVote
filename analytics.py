"""
analytics.py - MongoDB Aggregation Pipelines for SecureVote
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System
"""

import json
from database import get_db

# ==============================================================================
# PIPELINE 1: Election Results & Candidate Ranking with $lookup
# Real-World Purpose: Anonymously tallies verified cast votes, joins candidate
# metadata via $lookup, and produces certified leaderboard sorted descending.
# ==============================================================================
def get_pipeline_results(election_id):
    return [
        {
            "$match": {
                "election_id": election_id
            }
        },
        {
            "$group": {
                "_id": "$candidate_id",
                "verified_votes": { "$sum": 1 }
            }
        },
        {
            "$lookup": {
                "from": "candidates",
                "localField": "_id",
                "foreignField": "candidate_id",
                "as": "candidate_info"
            }
        },
        {
            "$unwind": "$candidate_info"
        },
        {
            "$project": {
                "_id": 0,
                "candidate_id": "$_id",
                "name": "$candidate_info.name",
                "party_or_slate": "$candidate_info.party_or_slate",
                "department": "$candidate_info.department",
                "manifesto": "$candidate_info.manifesto",
                "votes": "$verified_votes"
            }
        },
        {
            "$sort": {
                "votes": -1
            }
        }
    ]

# ==============================================================================
# PIPELINE 2: Department-wise Voter Turnout & Participation
# Real-World Purpose: Measures which university faculty or department had
# the highest turnout in the democratic election.
# ==============================================================================
def get_pipeline_department_turnout(election_id):
    return [
        {
            "$match": {
                "election_id": election_id
            }
        },
        {
            "$group": {
                "_id": "$department",
                "total_votes_cast": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "department": "$_id",
                "total_votes": "$total_votes_cast"
            }
        },
        {
            "$sort": {
                "total_votes": -1
            }
        }
    ]

# ==============================================================================
# PIPELINE 3: Temporal Voting Timeline & Peak Activity
# Real-World Purpose: Groups votes by hourly timestamp intervals using $dateToString
# to analyze voter surge patterns, peak hours, and system capacity.
# ==============================================================================
def get_pipeline_timeline(election_id):
    return [
        {
            "$match": {
                "election_id": election_id
            }
        },
        {
            "$project": {
                "hour_bucket": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:00",
                        "date": "$timestamp"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$hour_bucket",
                "votes_in_hour": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "_id": 0,
                "time_slot": "$_id",
                "vote_count": "$votes_in_hour"
            }
        },
        {
            "$sort": {
                "time_slot": 1
            }
        }
    ]

# ==============================================================================
# PIPELINE 4: Demographic Matrix (Year of Study Distribution)
# Real-World Purpose: Evaluates participation by student seniority
# (1st, 2nd, 3rd, 4th Year) and department diversity.
# ==============================================================================
def get_pipeline_demographics(election_id):
    return [
        {
            "$match": {
                "election_id": election_id
            }
        },
        {
            "$group": {
                "_id": {
                    "year": "$year_of_study",
                    "department": "$department"
                },
                "subtotal": { "$sum": 1 }
            }
        },
        {
            "$group": {
                "_id": "$_id.year",
                "total_year_votes": { "$sum": "$subtotal" },
                "department_breakdown": {
                    "$push": {
                        "dept": "$_id.department",
                        "count": "$subtotal"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year_of_study": "$_id",
                "total_votes": "$total_year_votes",
                "departments": "$department_breakdown"
            }
        },
        {
            "$sort": {
                "year_of_study": 1
            }
        }
    ]

# ==============================================================================
# PIPELINE 5: Comprehensive Real-Time Metrics using $facet
# Real-World Purpose: Computes multiple analytics branches (summary KPI,
# candidate shares, and department breakdown) in a single database roundtrip.
# ==============================================================================
def get_pipeline_facet_summary(election_id):
    return [
        {
            "$match": {
                "election_id": election_id
            }
        },
        {
            "$facet": {
                "election_summary": [
                    {
                        "$group": {
                            "_id": None,
                            "total_ballots_cast": { "$sum": 1 },
                            "first_vote_time": { "$min": "$timestamp" },
                            "last_vote_time": { "$max": "$timestamp" }
                        }
                    }
                ],
                "candidate_tally": [
                    {
                        "$group": {
                            "_id": "$candidate_id",
                            "vote_count": { "$sum": 1 }
                        }
                    },
                    {
                        "$sort": { "vote_count": -1 }
                    }
                ],
                "department_stats": [
                    {
                        "$group": {
                            "_id": "$department",
                            "count": { "$sum": 1 }
                        }
                    },
                    {
                        "$sort": { "count": -1 }
                    }
                ]
            }
        }
    ]


# ==============================================================================
# PYMONGO EXECUTION FUNCTIONS
# ==============================================================================

def execute_results_pipeline(election_id):
    """Executes Pipeline 1 via PyMongo aggregate() and determines winner."""
    db = get_db()
    pipeline = get_pipeline_results(election_id)
    results = list(db.votes.aggregate(pipeline))
    
    # If no votes in votes collection yet, fallback to candidate collection for display
    if not results:
        candidates = list(db.candidates.find({"election_id": election_id}, {"_id": 0}))
        results = [
            {
                "candidate_id": c["candidate_id"],
                "name": c["name"],
                "party_or_slate": c["party_or_slate"],
                "department": c["department"],
                "manifesto": c["manifesto"],
                "votes": c.get("vote_count", 0)
            }
            for c in candidates
        ]
        results.sort(key=lambda x: x["votes"], reverse=True)

    total_votes = sum(r["votes"] for r in results)
    for r in results:
        r["percentage"] = round((r["votes"] / total_votes * 100), 1) if total_votes > 0 else 0
        
    return {
        "election_id": election_id,
        "total_votes": total_votes,
        "leader": results[0] if results and results[0]["votes"] > 0 else None,
        "candidates": results,
        "pipeline_mql": pipeline
    }

def execute_department_turnout(election_id):
    """Executes Pipeline 2 via PyMongo aggregate()."""
    db = get_db()
    pipeline = get_pipeline_department_turnout(election_id)
    results = list(db.votes.aggregate(pipeline))
    return {
        "election_id": election_id,
        "turnout": results,
        "pipeline_mql": pipeline
    }

def execute_timeline(election_id):
    """Executes Pipeline 3 via PyMongo aggregate()."""
    db = get_db()
    pipeline = get_pipeline_timeline(election_id)
    results = list(db.votes.aggregate(pipeline))
    return {
        "election_id": election_id,
        "timeline": results,
        "pipeline_mql": pipeline
    }

def execute_demographics(election_id):
    """Executes Pipeline 4 via PyMongo aggregate()."""
    db = get_db()
    pipeline = get_pipeline_demographics(election_id)
    results = list(db.votes.aggregate(pipeline))
    return {
        "election_id": election_id,
        "demographics": results,
        "pipeline_mql": pipeline
    }

def execute_facet_summary(election_id):
    """Executes Pipeline 5 via PyMongo aggregate()."""
    db = get_db()
    pipeline = get_pipeline_facet_summary(election_id)
    raw = list(db.votes.aggregate(pipeline))
    data = raw[0] if raw else {}
    
    # Format timestamps
    summary = data.get("election_summary", [])
    if summary and summary[0].get("first_vote_time"):
        summary[0]["first_vote_time"] = summary[0]["first_vote_time"].strftime("%Y-%m-%d %H:%M:%S")
        summary[0]["last_vote_time"] = summary[0]["last_vote_time"].strftime("%Y-%m-%d %H:%M:%S")

    return {
        "election_id": election_id,
        "facet_data": data,
        "pipeline_mql": pipeline
    }

# Viva dictionary detailing all 5 pipelines for display in the Aggregation Viva Lab
PIPELINE_DESCRIPTIONS = {
    "results": {
        "title": "Pipeline 1: Election Results & Leaderboard ($lookup)",
        "stages": ["$match", "$group", "$lookup", "$unwind", "$project", "$sort"],
        "purpose": "Calculates certified vote totals directly from immutable ballot records, joins candidate profile data from the candidates collection, formats the output, and sorts descending by votes.",
        "why_chosen": "Prevents data denormalization inconsistencies and ensures ballot integrity cannot be spoofed by merely modifying candidate vote counts."
    },
    "turnout": {
        "title": "Pipeline 2: Department-wise Voter Turnout ($group)",
        "stages": ["$match", "$group", "$project", "$sort"],
        "purpose": "Aggregates voter turnout classified by academic faculties (Computer Science, Electronics, Mechanical, Management, etc.).",
        "why_chosen": "Demonstrates high-performance categorical grouping on indexed document fields."
    },
    "timeline": {
        "title": "Pipeline 3: Hourly Voting Wave Analysis ($dateToString & $group)",
        "stages": ["$match", "$project ($dateToString)", "$group", "$project", "$sort"],
        "purpose": "Groups votes into chronological hourly buckets to visualize voter participation peaks during polling hours.",
        "why_chosen": "Demonstrates date extraction operators and time-series aggregation without external libraries."
    },
    "demographics": {
        "title": "Pipeline 4: Multi-Dimensional Student Year Matrix ($push)",
        "stages": ["$match", "$group (composite)", "$group ($push accumulator)", "$project", "$sort"],
        "purpose": "Two-level hierarchical grouping: groups by year of study, then accumulates department counts into nested document arrays using $push.",
        "why_chosen": "Demonstrates advanced document restructuring and accumulator operators ($push, $sum)."
    },
    "facet": {
        "title": "Pipeline 5: Multi-Faceted Executive Dashboard ($facet)",
        "stages": ["$match", "$facet (3 sub-pipelines)"],
        "purpose": "Executes 3 independent aggregation pipelines concurrently in a single database call: Overall KPI summary, Candidate tally, and Department shares.",
        "why_chosen": "Maximizes network efficiency and showcases advanced MongoDB 8.x pipeline optimization."
    }
}
