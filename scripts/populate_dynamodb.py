"""
One-time script to populate the portfolio DynamoDB table with Ron's info.
Run with: python3 scripts/populate_dynamodb.py
"""
import boto3
import uuid
import time

session = boto3.Session(profile_name="portfolio-admin", region_name="us-east-1")
dynamodb = session.resource("dynamodb")
table = dynamodb.Table("portfolio")


def put(pk, sk, fields):
    table.put_item(Item={"PK": pk, "SK": sk, **fields})
    print(f"  ✓ {pk} / {sk}")


# ── ABOUT ─────────────────────────────────────────────────────────────────────
put("CONTENT", "ABOUT", {
    "bio": (
        "Ron Harifiyati is an Integration Engineering intern at Jamf, "
        "building and maintaining the integrations that allow enterprise software systems to communicate. "
        "He was first introduced to programming at the Innovation Hub at Mosi oa Tunya School in Victoria Falls, Zimbabwe, "
        "and has since gone on to build iOS apps, REST APIs, cloud infrastructure, and full-stack web projects. "
        "A graduate of the Matter Career Readiness Institute (MCRI), Ron is driven by a relentless work ethic "
        "and a commitment to growing into new technologies."
    ),
    "mission": "I might not be the smartest in the room — but I'll be the hardest worker in it.",
    "contact": {
        "email": "personal-ronshadreck@gmail.com",
        "location": "Victoria Falls, Zimbabwe",
    },
    "social_links": {
        "github": "https://github.com/ron-harifiyati",
        "linkedin": "https://www.linkedin.com/in/ron-harifiyati-723391350/",
    },
})

# ── SKILLS ────────────────────────────────────────────────────────────────────
put("CONTENT", "SKILLS", {
    "languages":    ["Python", "Swift", "JavaScript", "Bash/Shell", "SQL", "HTML/CSS"],
    "backend_apis": ["REST", "Node.js", "Express", "Flask", "FastAPI", "GraphQL", "JWT/Auth"],
    "frontend":     ["Alpine.js", "React", "SwiftUI"],
    "mobile":       ["iOS/SwiftUI", "UIKit", "Xcode"],
    "cloud_infra":  ["AWS Lambda", "API Gateway", "S3", "CloudFront", "DynamoDB", "IAM",
                     "Docker", "Linux", "GitHub Actions", "CI/CD"],
    "databases":    ["DynamoDB", "SQLite", "MongoDB"],
    "tools":        ["Git", "GitHub", "Postman", "Atlassian"],
})

# ── TIMELINE ──────────────────────────────────────────────────────────────────
put("CONTENT", "TIMELINE", {
    "events": [
        {
            "date": "2022",
            "title": "First Line of Code",
            "description": "Introduced to programming at the Innovation Hub at Mosi oa Tunya School in Victoria Falls.",
        },
        {
            "date": "2023",
            "title": "Continued Education",
            "description": "Deepened my studies at Mosi oa Tunya, building on my early interest in technology.",
        },
        {
            "date": "2024",
            "title": "O'Level Examinations",
            "description": "Sat and completed O'Level exams — a major academic milestone.",
        },
        {
            "date": "Feb 2025",
            "title": "Joined MCRI",
            "description": "Enrolled at the Matter Career Readiness Institute, accelerating my technical and professional development.",
        },
        {
            "date": "2025",
            "title": "iOS & API Development",
            "description": "Built my first iOS app (Parity) using Swift and UIKit, and started building REST APIs with Node.js.",
        },
        {
            "date": "2026",
            "title": "Integration Engineer Intern at Jamf",
            "description": "Joined Jamf as an Integration Engineering intern — building and maintaining integrations between enterprise systems.",
        },
    ]
})

# ── CURRENTLY LEARNING ────────────────────────────────────────────────────────
put("CONTENT", "CURRENTLY_LEARNING", {
    "items": [
        "AWS", "Cybersecurity", "Architecture Design", "Prompt Engineering",
        "Ethical Hacking", "Automation", "Scripting", "Containerisation",
    ]
})

# ── FUN FACTS ─────────────────────────────────────────────────────────────────
put("CONTENT", "FUNFACTS", {
    "facts": [
        "I wrote my first line of code at an Innovation Hub in Victoria Falls — home of one of the 7 Natural Wonders of the World.",
        "I build integrations for a living — essentially a translator for systems that don't speak the same language.",
        "I've built in Python, JavaScript, and Swift — sometimes all in the same week.",
        "My motto: not the smartest in the room, but definitely the hardest working.",
        "I wrote a Python course specifically for Swift developers looking to branch out.",
        "Victoria Falls is one of the largest waterfalls in the world. I grew up hearing it in the background.",
    ]
})

# ── PROJECTS ──────────────────────────────────────────────────────────────────
projects = [
    {
        "title": "Portfolio Site",
        "description": (
            "A live, interactive, API-first personal portfolio running on AWS. "
            "The backend is a standalone Python Lambda API (usable via Postman/curl), "
            "the frontend is an Alpine.js SPA served from S3/CloudFront."
        ),
        "tech_stack": ["Python", "Alpine.js", "AWS Lambda", "DynamoDB", "API Gateway", "S3", "CloudFront"],
        "links": {
            "github": "https://github.com/ron-harifiyati/about-me",
            "live": "https://dkdwnfmhg75yf.cloudfront.net",
        },
    },
    {
        "title": "Parity",
        "description": (
            "Digital platform for managing informal savings groups (mukando/round) with member verification, "
            "contribution tracking, mobile money integration, and automated loan calculations."
        ),
        "tech_stack": ["Swift", "iOS", "UIKit", "Xcode"],
        "links": {"github": "https://github.com/ron-harifiyati/Parity"},
    },
    {
        "title": "Parity API",
        "description": (
            "RESTful API backend for the Parity savings platform — handles authentication, "
            "member management, contribution tracking, and loan calculations."
        ),
        "tech_stack": ["JavaScript", "Node.js", "Express", "JWT"],
        "links": {"github": "https://github.com/ron-harifiyati/parity-api"},
    },
    {
        "title": "Personal Expense Tracker API",
        "description": (
            "A personal finance API for tracking daily expenses, managing multiple account balances "
            "(cash, bank, mobile money), setting budgets, and visualizing spending habits."
        ),
        "tech_stack": ["JavaScript", "Node.js", "SQLite", "Express"],
        "links": {"github": "https://github.com/ron-harifiyati/Personal-Expense-Tracker-API"},
    },
    {
        "title": "API with Database & Auth",
        "description": (
            "A REST API demonstrating SQLite-backed storage with Sequelize ORM and JWT authentication — "
            "built as a learning project for full auth + database patterns."
        ),
        "tech_stack": ["JavaScript", "Node.js", "SQLite", "Sequelize", "JWT"],
        "links": {"github": "https://github.com/ron-harifiyati/API-with-Database-Auth"},
    },
]

for p in projects:
    pid = str(uuid.uuid4())
    table.put_item(Item={
        "PK": f"PROJECT#{pid}",
        "SK": "META",
        "id": pid,
        "created_at": int(time.time()),
        **p,
    })
    print(f"  ✓ PROJECT / {p['title']}")

# ── COURSES ───────────────────────────────────────────────────────────────────
courses = [
    {
        "title": "Python for Swift Developers",
        "platform": "Self-published (GitHub)",
        "description": (
            "A Python course designed to bridge iOS/Swift developers into general-purpose programming. "
            "Covers three sections: Values (basics, strings, naming), "
            "Algorithms (functions, types, parameters, decision-making), "
            "and Complex Data (instances, methods, properties, lists and loops). "
            "Makes Python intuitive by connecting it to familiar Swift concepts."
        ),
        "link": "https://github.com/ron-harifiyati/Python_Tutorials",
    },
]

for c in courses:
    cid = str(uuid.uuid4())
    table.put_item(Item={
        "PK": f"COURSE#{cid}",
        "SK": "META",
        "id": cid,
        "created_at": int(time.time()),
        **c,
    })
    print(f"  ✓ COURSE / {c['title']}")

print("\nDone. All data written to DynamoDB table 'portfolio'.")
