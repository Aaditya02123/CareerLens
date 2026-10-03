from __future__ import annotations

import json

from app.models.match_explaination import MatchEvidence


JOB_EXPLANATION_SYSTEM_PROMPT = """
You are CareerLens, a career intelligence assistant.

Generate only the candidate-facing WHY IT FITS content for an already-computed
job match. The deterministic CareerLens matching system is authoritative.

Never invent skills, resume evidence, qualifications, or experience.
Use only supplied resume evidence when discussing the candidate.
Never use the job title, company, location, or other job metadata as evidence.
Never use job metadata as evidence that the candidate possesses a skill.
Preserve supplied evidence source_type, source_title, excerpt, and strength.
Never describe supporting evidence as direct evidence.
Never reinterpret scores 
Never change matched/missing skill status.
Do not make hiring, employability, success, or selection predictions.
Do not recommend external courses, websites, certifications, products,
companies, or learning platforms unless explicitly supplied.
Do not expose internal field names.
Return only the WHY IT FITS content, without a heading.
Keep it to one or two concise sentences.
Plain text only. Do not use Markdown.
Do not include any additional sections.
""".strip()


def build_job_explanation_prompt(
    *,
    job_title: str,
    company: str | None,
    match_level: str,
    hybrid_score: float,
    required_skill_score: float,
    preferred_skill_score: float,
    semantic_score: float,
    matched_required_skills: list[str],
    missing_required_skills: list[str],
    matched_preferred_skills: list[str],
    evidence: list[MatchEvidence],
) -> str:
    evidence_payload = [
        {
            "skill": item.skill,
            "source_type": item.source_type,
            "source_title": item.source_title,
            "excerpt": item.excerpt,
            "strength": item.strength,
        }
        for item in evidence
    ]

    context = {
        "role": {
            "title": job_title,
            "company": company,
        },
        "matched_skills": {
            "required": matched_required_skills,
            "preferred": matched_preferred_skills,
        },
        "resume_evidence": evidence_payload,
    }

    return f"""
Write only the WHY IT FITS content for this candidate-to-job match.

Return one or two concise plain-text sentences explaining why the match
fits. Do not output the "WHY IT FITS" heading itself.

Use only the supplied matched skills and resume evidence. The role metadata
describes the target role but is never evidence that the candidate possesses
a skill. Preserve the evidence source and strength accurately. Do not invent
facts, qualifications, scores, or external recommendations. Do not add a
heading, Markdown, or any additional sections.

Context:
{json.dumps(context, ensure_ascii=False, indent=2)}
""".strip()


def build_deterministic_gap(
    missing_required_skills: list[str],
) -> str:
    skills = [
        skill.strip()
        for skill in missing_required_skills
        if skill and skill.strip()
    ]

    if not skills:
        return "No required skill gaps were detected."

    if len(skills) == 1:
        return (
            f"{skills[0]} is a required skill that is currently "
            "missing from the resume analysis."
        )

    if len(skills) == 2:
        joined = f"{skills[0]} and {skills[1]}"
    else:
        joined = (
            f"{', '.join(skills[:-1])}, and {skills[-1]}"
        )

    return (
        "The required skills currently missing from the resume "
        f"analysis are {joined}."
    )


def build_deterministic_next_step(
    missing_required_skills: list[str],
    matched_required_skills: list[str],
    evidence: list[MatchEvidence],
) -> str:
    missing = [
        skill.strip()
        for skill in missing_required_skills
        if skill and skill.strip()
    ]

    if missing:
        if len(missing) == 1:
            joined = missing[0]
        elif len(missing) == 2:
            joined = f"{missing[0]} and {missing[1]}"
        else:
            joined = (
                f"{', '.join(missing[:-1])}, and {missing[-1]}"
            )

        plural = "skill gap" if len(missing) == 1 else "skill gaps"

        return (
            f"Prioritize developing {joined} because "
            f"{'it is the remaining required-skill gap' if len(missing) == 1 else f'they are the remaining required-skill {plural}' }."
        )

    source_types = {
        item.source_type.strip().lower()
        for item in evidence
        if item.source_type and item.source_type.strip()
    }

    if {"project", "experience"} & source_types:
        return (
            "Focus on demonstrating your existing resume evidence through "
            "concrete project outcomes and implementation details."
        )

    if {"education", "certification", "skill"} & source_types:
        return (
            "Focus on communicating the existing resume evidence clearly "
            "through concrete examples."
        )

    return (
        "Focus on communicating the existing resume alignment clearly "
        "through concrete examples from your resume."
    )


def _is_section_heading(line: str, heading: str) -> bool:
    normalized = line.strip().upper()
    return normalized in {
        heading,
        f"**{heading}**",
        f"## {heading}",
    }


def _sanitize_why_it_fits(value: str) -> str:
    lines = [
        line.strip()
        for line in value.replace("\r\n", "\n").split("\n")
        if line.strip()
    ]

    if not lines:
        return (
            "The supplied resume evidence supports the deterministic "
            "match."
        )

    why_start = next(
        (
            index
            for index, line in enumerate(lines)
            if _is_section_heading(line, "WHY IT FITS")
        ),
        None,
    )

    if why_start is not None:
        lines = lines[why_start + 1 :]

    for index, line in enumerate(lines):
        if _is_section_heading(line, "GAP") or _is_section_heading(
            line,
            "NEXT STEP",
        ):
            lines = lines[:index]
            break

    cleaned = " ".join(lines)
    cleaned = cleaned.replace("```", "").strip()

    return cleaned or (
        "The supplied resume evidence supports the deterministic match."
    )


def compose_job_explanation(
    *,
    why_it_fits: str,
    missing_required_skills: list[str],
    matched_required_skills: list[str],
    evidence: list[MatchEvidence],
) -> str:
    why = _sanitize_why_it_fits(why_it_fits)
    gap = build_deterministic_gap(
        missing_required_skills
    )
    next_step = build_deterministic_next_step(
        missing_required_skills,
        matched_required_skills,
        evidence,
    )

    return (
        f"WHY IT FITS\n{why}\n\n"
        f"GAP\n{gap}\n\n"
        f"NEXT STEP\n{next_step}"
    )