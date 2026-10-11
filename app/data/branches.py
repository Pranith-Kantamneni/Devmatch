"""Canonical branch / department list for profiles."""

BRANCHES: list[str] = [
    "Computer Science and Engineering",
    "Computer Science (Artificial Intelligence and Machine Learning)",
    "Computer Science (Data Science)",
    "Computer Science (Cyber Security)",
    "Computer Science (Internet of Things)",
    "Artificial Intelligence and Machine Learning",
    "Artificial Intelligence and Data Science",
    "Data Science and Engineering",
    "Information Technology",
    "Software Engineering",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "Electrical Engineering",
    "Electronics and Instrumentation Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Chemical Engineering",
    "Biotechnology",
    "Biomedical Engineering",
    "Aerospace Engineering",
    "Aeronautical Engineering",
    "Automobile Engineering",
    "Mechatronics Engineering",
    "Robotics and Automation",
    "Metallurgical and Materials Engineering",
    "Mining Engineering",
    "Petroleum Engineering",
    "Food Technology",
    "Textile Technology",
    "Agricultural Engineering",
    "Architecture",
    "Mathematics and Computing",
    "Engineering Physics",
    "Computer Applications (BCA / MCA)",
    "Computer Science (B.Sc / M.Sc)",
    "Data Science (B.Sc / M.Sc)",
    "Business Administration (BBA / MBA)",
    "Commerce (B.Com / M.Com)",
    "Economics",
    "Other",
]


def is_known_branch(branch: str | None) -> bool:
    if not branch:
        return False
    lowered = branch.strip().lower()
    return any(b.lower() == lowered for b in BRANCHES)
