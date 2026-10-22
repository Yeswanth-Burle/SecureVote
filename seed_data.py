"""
seed_data.py - Populates Realistic Demo Data for SecureVote
Course: CSE494 - Intelligent NoSQL Databases
Project: SecureVote - Online Voting System
"""

from datetime import datetime, timedelta
import random
from database import setup_database, get_db
from crud import cast_vote, register_voter, create_election, add_candidate

def seed_all():
    print("[SEED] Resetting database and re-creating collections with $jsonSchema...")
    db = setup_database(drop_existing=True)

    # ==========================================================================
    # 1. ELECTIONS
    # ==========================================================================
    now = datetime.now()
    elections_data = [
        {
            "election_id": "ELEC-2026-PRES",
            "title": "University Student Council Presidential Election 2026",
            "category": "Student Council",
            "start_date": (now - timedelta(days=2)).isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
            "description": "General election for university-wide student body president to represent all faculties in the academic senate."
        },
        {
            "election_id": "ELEC-2026-SPORTS",
            "title": "Campus Sports Board Secretary Election 2026",
            "category": "Sports Board",
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=4)).isoformat(),
            "description": "Annual election to appoint student leadership overseeing inter-college athletics and gym facilities."
        }
    ]

    for ele in elections_data:
        res = create_election(
            election_id=ele["election_id"],
            title=ele["title"],
            category=ele["category"],
            start_date=ele["start_date"],
            end_date=ele["end_date"],
            description=ele["description"]
        )
        print(f"  -> Election created: {ele['election_id']} ({res.get('success')})")

    # ==========================================================================
    # 2. CANDIDATES
    # ==========================================================================
    candidates_data = [
        # Presidential Election Candidates
        {
            "candidate_id": "CAND-01",
            "election_id": "ELEC-2026-PRES",
            "name": "Aarav Sharma",
            "party_or_slate": "Tech Innovators Slate",
            "manifesto": "Digital campus modernization, 24/7 AI lab infrastructure, open-source hackathons, and transparent student representation.",
            "department": "Computer Science"
        },
        {
            "candidate_id": "CAND-02",
            "election_id": "ELEC-2026-PRES",
            "name": "Ananya Patel",
            "party_or_slate": "Green Campus Alliance",
            "manifesto": "100% solar-powered cafeterias, mental wellness days, zero plastic initiative, and community eco-grants.",
            "department": "Biotechnology"
        },
        {
            "candidate_id": "CAND-03",
            "election_id": "ELEC-2026-PRES",
            "name": "Rohan Verma",
            "party_or_slate": "Students United Coalition",
            "manifesto": "Corporate mentorship drives, guaranteed internship stipends, upgraded campus transit, and peer-to-peer tutoring network.",
            "department": "Management"
        },
        {
            "candidate_id": "CAND-04",
            "election_id": "ELEC-2026-PRES",
            "name": "Priya Nair",
            "party_or_slate": "Arts & Tech Vanguard",
            "manifesto": "Advanced hardware fab labs, robotics sponsorships, equal cultural funding, and a 24-hr grievance redressal portal.",
            "department": "Electronics"
        },
        # Sports Board Candidates
        {
            "candidate_id": "CAND-SP-01",
            "election_id": "ELEC-2026-SPORTS",
            "name": "Kabir Singh",
            "party_or_slate": "Athletics Syndicate",
            "manifesto": "Olympic standard training equipment, dedicated coaches, and round-the-clock stadium lighting.",
            "department": "Mechanical"
        },
        {
            "candidate_id": "CAND-SP-02",
            "election_id": "ELEC-2026-SPORTS",
            "name": "Sneha Rao",
            "party_or_slate": "Fitness First Coalition",
            "manifesto": "Inclusive sports for all genders, subsidized nutrition bars, and modern swimming pool heating.",
            "department": "Civil"
        }
    ]

    for cand in candidates_data:
        res = add_candidate(
            candidate_id=cand["candidate_id"],
            election_id=cand["election_id"],
            name=cand["name"],
            party_or_slate=cand["party_or_slate"],
            manifesto=cand["manifesto"],
            department=cand["department"]
        )
        print(f"  -> Candidate added: {cand['candidate_id']} - {cand['name']}")

    # ==========================================================================
    # 3. REGISTERED VOTERS (30 realistic students across departments & years)
    # ==========================================================================
    voters_list = [
        ("STU1001", "Aditya Joshi", "aditya.j@univ.edu", "Computer Science", 3, 21),
        ("STU1002", "Diya Sengupta", "diya.s@univ.edu", "Computer Science", 2, 20),
        ("STU1003", "Ishaan Malhotra", "ishaan.m@univ.edu", "Electronics", 4, 22),
        ("STU1004", "Meera Krishnan", "meera.k@univ.edu", "Management", 1, 19),
        ("STU1005", "Tanmay Kulkarni", "tanmay.k@univ.edu", "Mechanical", 3, 21),
        ("STU1006", "Sanya Kapoor", "sanya.k@univ.edu", "Biotechnology", 2, 20),
        ("STU1007", "Vikram Reddy", "vikram.r@univ.edu", "Computer Science", 4, 22),
        ("STU1008", "Neha Sundaram", "neha.s@univ.edu", "Electronics", 3, 21),
        ("STU1009", "Arjun Choudhury", "arjun.c@univ.edu", "Management", 2, 20),
        ("STU1010", "Pooja Hegde", "pooja.h@univ.edu", "Civil", 1, 18),
        ("STU1011", "Kunal Bhasin", "kunal.b@univ.edu", "Mechanical", 4, 23),
        ("STU1012", "Rhea Deshmukh", "rhea.d@univ.edu", "Biotechnology", 3, 21),
        ("STU1013", "Manish Tiwari", "manish.t@univ.edu", "Computer Science", 1, 18),
        ("STU1014", "Shweta Menon", "shweta.m@univ.edu", "Electronics", 2, 20),
        ("STU1015", "Gaurav Singhal", "gaurav.s@univ.edu", "Management", 4, 22),
        ("STU1016", "Ankita Roy", "ankita.r@univ.edu", "Computer Science", 3, 21),
        ("STU1017", "Rahul Nambiar", "rahul.n@univ.edu", "Mechanical", 2, 20),
        ("STU1018", "Tanya Bakshi", "tanya.b@univ.edu", "Biotechnology", 1, 19),
        ("STU1019", "Abhishek Bose", "abhishek.b@univ.edu", "Civil", 3, 21),
        ("STU1020", "Kavya Murthy", "kavya.m@univ.edu", "Electronics", 4, 22),
        ("STU1021", "Nikhil Chopra", "nikhil.c@univ.edu", "Computer Science", 2, 20),
        ("STU1022", "Simran Gill", "simran.g@univ.edu", "Management", 3, 21),
        ("STU1023", "Pranav Nair", "pranav.n@univ.edu", "Mechanical", 1, 19),
        ("STU1024", "Ritu Saxena", "ritu.s@univ.edu", "Biotechnology", 4, 22),
        ("STU1025", "Harsh Vardhan", "harsh.v@univ.edu", "Computer Science", 3, 21),
        ("STU1026", "Deepa Pillai", "deepa.p@univ.edu", "Civil", 2, 20),
        ("STU1027", "Siddharth Jain", "siddharth.j@univ.edu", "Electronics", 1, 19),
        ("STU1028", "Natasha Sen", "natasha.s@univ.edu", "Management", 2, 20),
        ("STU1029", "Varun Bhatia", "varun.b@univ.edu", "Mechanical", 3, 21),
        ("STU1030", "Zoya Khan", "zoya.k@univ.edu", "Computer Science", 4, 22)
    ]

    print("[SEED] Registering 30 university voters...")
    for v_id, name, email, dept, yr, age in voters_list:
        register_voter(v_id, name, email, dept, yr, age)

    # ==========================================================================
    # 4. CAST INITIAL VOTES (for election ELEC-2026-PRES)
    # Pre-populates 20 votes with simulated staggered timestamps for timeline chart!
    # ==========================================================================
    print("[SEED] Casting simulated votes to populate analytics charts...")
    vote_plan = [
        # (Voter ID, Candidate ID, Hours Ago)
        ("STU1001", "CAND-01", 6),
        ("STU1002", "CAND-01", 6),
        ("STU1003", "CAND-04", 5),
        ("STU1004", "CAND-03", 5),
        ("STU1005", "CAND-02", 5),
        ("STU1006", "CAND-02", 4),
        ("STU1007", "CAND-01", 4),
        ("STU1008", "CAND-04", 4),
        ("STU1009", "CAND-03", 3),
        ("STU1010", "CAND-02", 3),
        ("STU1011", "CAND-01", 3),
        ("STU1012", "CAND-02", 2),
        ("STU1013", "CAND-01", 2),
        ("STU1014", "CAND-04", 2),
        ("STU1015", "CAND-03", 1),
        ("STU1016", "CAND-01", 1),
        ("STU1017", "CAND-02", 1),
        ("STU1018", "CAND-02", 1),
        ("STU1019", "CAND-03", 0),
        ("STU1020", "CAND-04", 0)
    ]

    for v_id, cand_id, hours_ago in vote_plan:
        res = cast_vote(v_id, "ELEC-2026-PRES", cand_id)
        if res.get("success"):
            # Backdate timestamp for realistic timeline analytics
            fake_time = now - timedelta(hours=hours_ago, minutes=random.randint(5, 55))
            db.votes.update_one({"vote_id": res["vote_id"]}, {"$set": {"timestamp": fake_time}})

    # Cast a few votes for the sports election too
    cast_vote("STU1001", "ELEC-2026-SPORTS", "CAND-SP-01")
    cast_vote("STU1002", "ELEC-2026-SPORTS", "CAND-SP-02")
    cast_vote("STU1003", "ELEC-2026-SPORTS", "CAND-SP-01")

    total_votes = db.votes.count_documents({})
    total_voters = db.voters.count_documents({})
    total_candidates = db.candidates.count_documents({})
    print(f"\n[SUCCESS] Seed complete!")
    print(f"  • Registered Voters: {total_voters} (STU1021 - STU1030 are unvoted and ready for live demo!)")
    print(f"  • Candidates: {total_candidates}")
    print(f"  • Ballots Cast: {total_votes}")
    print(f"  • Try voting with ID: 'STU1021', 'STU1022', or register a new one!")

if __name__ == "__main__":
    seed_all()
