from app.services.resume_parser import parse_resume_text


DIGIVALET_RESUME = """
Aadityaraj Soni
aadityarajsoni04@gmail.com | +91 9589391642 | Indore, India | github.com/Aaditya02123

Summary
Backend-focused Computer Science undergraduate with strong analytical and problem-solving foundations in data
structures and algorithms. Hands-on experience building REST APIs, AI-enabled applications, and fullstack systems using
Python, FastAPI, React, MongoDB, and PostgreSQL, with a track record of team-based project delivery, requirement
clarification, and API testing.

Education
Medicaps University, Indore Expected May 2027
B.Tech, Computer Science & Engineering GPA: 8.97/10
• Relevant Coursework: Data Structures & Algorithms, Design & Analysis of Algorithms, DBMS, OOP

Technical Skills
Languages: Python, C++, C
Frameworks/Libraries: FastAPI, React, PyTorch, Playwright
Databases: PostgreSQL, MongoDB, MySQL
AI/Tools: Ollama, Git, GitHub, Postman, VS Code, Jupyter, Codex, Antigravity
Core CS: Data Structures & Algorithms, OOP, DBMS, OS

Internship
Student Developer Community (SDC), Medicaps University June 2026 – July 2026
Backend Developer
• Clarified requirements and identified workflow gaps while developing and maintaining RESTful APIs for the OIA
Portal using FastAPI and MongoDB, supporting an institutional portal capable of serving 500+ students.
• Built API validation and automated test coverage across 10+ core workflows, improving regression detection and
backend reliability.
• Evaluated deployment options including Render and MongoDB Atlas, documenting infrastructure and cost
considerations for institutional projects.

Projects
Plugs – LinkedIn Outreach Assistant | Flutter / FastAPI / Playwright / MongoDB / Ollama | github.com/Aaditya02123/Plugs
• Built a Windows desktop application for controlled LinkedIn outreach using Flutter and FastAPI, with Playwright
for browser automation and MongoDB for campaign/profile tracking.
• Implemented asynchronous campaign workflows and integrated a locally hosted Llama 3.2 1B model through
Ollama for personalized outreach-message generation.

NagarSetu – AI-Powered Civic Issue Reporting Platform | FastAPI / React / PostgreSQL / PyTorch | github.com/Aaditya02123/Nagarsetu
• Built an end-to-end civic grievance platform integrating a PyTorch image-classification pipeline to categorize
reported issues and assist department-level routing.
• Designed a normalized PostgreSQL schema and separated frontend/backend repositories, migrating the frontend
build setup from CRA to Vite.

OIA Portal – Office of International Affairs | FastAPI / React / MongoDB | oia.medicaps.ac.in
• Delivered dynamic RESTful APIs and server-rendered pages for a live institutional portal serving 500+ students.
• Implemented API validation and test coverage across 10+ core workflows to improve backend stability and
regression detection.

Certifications & Achievements
NPTEL – Database Management Systems (IIT Kharagpur)
NPTEL – Introduction to Machine Learning (IIT Madras)
Smart India Hackathon 2024 – Certificate of Participation (Team Lead)
Solution Challenge – Google Developer Groups (GDG), Certificate of Participation
"""


def test_extracts_identity():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert result.name == "Aadityaraj Soni"
    assert result.email == "aadityarajsoni04@gmail.com"


def test_extracts_summary():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert result.summary is not None
    assert "Backend-focused Computer Science undergraduate" in result.summary
    assert "FastAPI" in result.summary


def test_extracts_education_as_structured_entity():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert len(result.education_entries) == 1

    education = result.education_entries[0]

    assert education.institution == "Medicaps University, Indore"
    assert education.degree == "B.Tech"
    assert education.field_of_study == "Computer Science & Engineering"
    assert education.expected_graduation == "May 2027"
    assert education.gpa == "8.97/10"

    assert education.coursework == [
        "Data Structures & Algorithms",
        "Design & Analysis of Algorithms",
        "DBMS",
        "OOP",
    ]


def test_extracts_experience_as_one_entity():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert len(result.experience_entries) == 1

    experience = result.experience_entries[0]

    assert (
        experience.organization
        == "Student Developer Community (SDC), Medicaps University"
    )

    assert experience.role == "Backend Developer"

    assert experience.start_date == "June 2026"
    assert experience.end_date == "July 2026"

    assert experience.location is None

    assert len(experience.description) == 3

    assert "Clarified requirements" in experience.description[0]
    assert "Built API validation" in experience.description[1]
    assert "Evaluated deployment options" in experience.description[2]


def test_projects_are_grouped_into_three_entities():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert len(result.project_entries) == 3


def test_plugs_project_is_structured():
    result = parse_resume_text(DIGIVALET_RESUME)

    project = result.project_entries[0]

    assert project.title == "Plugs – LinkedIn Outreach Assistant"

    assert project.technologies == [
        "Flutter",
        "FastAPI",
        "Playwright",
        "MongoDB",
        "Ollama",
    ]

    assert (
        project.url
        == "github.com/Aaditya02123/Plugs"
    )

    assert len(project.description) == 2


def test_nagarsetu_project_is_structured():
    result = parse_resume_text(DIGIVALET_RESUME)

    project = result.project_entries[1]

    assert (
        project.title
        == "NagarSetu – AI-Powered Civic Issue Reporting Platform"
    )

    assert project.technologies == [
        "FastAPI",
        "React",
        "PostgreSQL",
        "PyTorch",
    ]

    assert (
        project.url
        == "github.com/Aaditya02123/Nagarsetu"
    )

    assert len(project.description) == 2


def test_oia_project_is_structured():
    result = parse_resume_text(DIGIVALET_RESUME)

    project = result.project_entries[2]

    assert (
        project.title
        == "OIA Portal – Office of International Affairs"
    )

    assert project.technologies == [
        "FastAPI",
        "React",
        "MongoDB",
    ]

    assert project.url == "oia.medicaps.ac.in"

    assert len(project.description) == 2


def test_credentials_are_preserved():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert len(result.credential_entries) == 4

    assert (
        result.credential_entries[0].title
        == "NPTEL – Database Management Systems (IIT Kharagpur)"
    )

    assert (
        result.credential_entries[0].credential_type
        == "certification"
    )

    assert (
        result.credential_entries[2].credential_type
        == "participation"
    )


def test_unknown_sections_are_preserved():
    resume = """
Aadityaraj Soni

Education
Example University
B.Tech Computer Science

Open Source Contributions
Maintained several open-source repositories.
Contributed bug fixes and documentation.

Projects
Example Project | Python / FastAPI | github.com/example/project
• Built an API.
"""

    result = parse_resume_text(resume)

    custom_section = next(
        section
        for section in result.sections
        if section.title == "Open Source Contributions"
    )

    assert custom_section.canonical_type == "custom"
    assert (
        "Maintained several open-source repositories."
        in custom_section.raw_content
    )


def test_legacy_fields_remain_available():
    result = parse_resume_text(DIGIVALET_RESUME)

    assert result.education
    assert result.experience
    assert result.projects
    assert result.certifications


def test_missing_information_is_not_invented():
    result = parse_resume_text(DIGIVALET_RESUME)

    experience = result.experience_entries[0]

    # The resume does not explicitly give an internship location.
    # Therefore CareerLens must not infer one from the candidate's
    # contact location.
    assert experience.location is None