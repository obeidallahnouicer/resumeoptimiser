#!/usr/bin/env python3
"""Debug script to trace CV parsing with real user data."""

import sys
sys.path.insert(0, '/home/obeid/Desktop/projects/resumeshit')

from resumeoptimiser.app.agents.ocr_to_markdown import _raw_to_markdown
from resumeoptimiser.app.agents.cv_parser import _parse_markdown

# Real CV text from user's data
raw_cv = """
Obeid
obeid@example.com | +216 54 000 000 | Tunis, Tunisia | linkedin.com/in/obeid | github.com/obeid

PROFESSIONAL SUMMARY
Experienced AI/ML engineer with 3+ years building production systems. Expertise in LLM applications, multi-agent architectures, and full-stack AI solutions. Track record of delivering 60%+ performance improvements through optimization.

PROFESSIONAL EXPERIENCE
Senior AI Engineer | TechCorp
Jan 2024 – Present | Tunis, Tunisia
- Architected multi-agent LLM system reducing processing time by 65%
- Built autonomous agent workflows for document analysis
- Implemented prompt caching, reducing inference costs by 40%

AI Engineer | StartupXYZ
Sep 2022 – Dec 2023 | Remote
- Developed LangGraph-based orchestration framework
- Deployed 5+ production ML models on Azure cloud
- Led team of 2 junior engineers

EDUCATION
MSc Business Analytics & Generative AI | ESPRIT School of Business
Sep 2024 – Present | Tunis, Tunisia

BSc Computer Science | University of Tunis
2019 – 2023 | Tunis, Tunisia
GPA: 3.8/4.0

SKILLS
AI & Machine Learning
- LangGraph · Multi-Agent Systems · Autonomous Agent Workflows · Tool Calling · Memory Systems · Guardrail Engineering

Python & Backend
- FastAPI · Django · Async Programming · Microservices · Message Queues · SQLAlchemy

DevOps & Cloud
- Azure App Service · Docker · Docker Compose · GitLab CI/CD · Nginx · Git · Poetry

Data & Databases
- PostgreSQL · MongoDB · Redis · ETL Pipelines · Data Validation

LANGUAGES
- Arabic — Native
- French — Fluent
- English — Fluent

CERTIFICATIONS
- AWS Solutions Architect Associate (2023)
- Certified Kubernetes Administrator (2022)
"""

print("=" * 80)
print("STEP 1: Raw CV Text")
print("=" * 80)
print(raw_cv[:500] + "...")

print("\n" + "=" * 80)
print("STEP 2: Generated Markdown")
print("=" * 80)
markdown = _raw_to_markdown(raw_cv)
print(markdown)

print("\n" + "=" * 80)
print("STEP 3: Parsed StructuredCVSchema")
print("=" * 80)
schema = _parse_markdown(markdown)

print(f"\nName: {schema.contact.name}")
print(f"Email: {schema.contact.email}")
print(f"Location: {schema.contact.location}")
print(f"\nEducation Level: '{schema.education_level}'")
print(f"Hard Skills ({len(schema.hard_skills)}): {schema.hard_skills[:5]}")
print(f"Soft Skills ({len(schema.soft_skills)}): {schema.soft_skills}")
print(f"Tools ({len(schema.tools)}): {schema.tools[:5]}")
print(f"Languages ({len(schema.languages_spoken)}): {schema.languages_spoken}")
print(f"Total Years: {schema.total_years_experience}")
print(f"Certifications: {schema.certifications}")

print("\n" + "=" * 80)
print("STEP 4: Sections Found")
print("=" * 80)
for i, section in enumerate(schema.sections):
    print(f"\n{i+1}. {section.section_type.value}")
    print(f"   Items: {len(section.items)}")
    print(f"   First 3: {section.items[:3]}")
    if section.raw_text:
        print(f"   Raw: {section.raw_text[:100]}...")
