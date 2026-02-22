"""Core configuration and constants."""

import os
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
BUILD_DIR = BASE_DIR / "build"
TEST_OUTPUT_DIR = BASE_DIR / "test_output"
TEMP_UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_TEMP_DIR", "temp_uploads")

# Data files
BASE_SKILLS_FILE = BASE_DIR / "base_skills.json"
LATEX_TEMPLATE_FILE = BASE_DIR / "template.tex"

# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# File Upload Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 50))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# OpenRouter Configuration (legacy, kept for compatibility)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "Resume Optimiser")

# NVIDIA API Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-r1-distill-qwen-14b")

# CORS Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# LaTeX Configuration
LATEX_TIMEOUT = 30  # seconds
LATEX_INTERACTION_MODE = "nonstopmode"

# Skill Matching Configuration
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # BGE (BAAI General Embedding) model for skill similarity
MIN_TRANSFERABLE_SIMILARITY = 0.5
MIN_DIRECT_SIMILARITY = 0.95

# Scoring Thresholds
SCORE_GREEN_THRESHOLD = 80.0
SCORE_YELLOW_THRESHOLD = 60.0

# Tech Stack Definitions
CORE_TECH_STACK = {
    "Python", "JavaScript", "TypeScript", "Java", "C#", "Go", "Rust", "PHP", "Ruby", "Swift",
    "React", "Vue", "Angular", "Next.js", "Svelte", "Ember",
    "Node.js", "Express", "FastAPI", "Django", "Spring Boot", "Laravel", "Gin", "Echo",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB", "Cassandra",
    "AWS", "GCP", "Azure", "DigitalOcean",
    "Kubernetes", "Docker", "Docker Compose",
    "GraphQL", "REST", "gRPC", "SOAP",
    "TensorFlow", "PyTorch", "scikit-learn", "Keras", "XGBoost",
    "Git", "GitHub", "GitLab", "Bitbucket"
}

SECONDARY_TECH_STACK = {
    "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
    "Terraform", "Ansible", "CloudFormation",
    "Kafka", "RabbitMQ", "Apache Spark", "Hadoop", "Airflow",
    "HTML", "CSS", "Sass", "Tailwind", "Bootstrap", "Material UI",
    "Agile", "Scrum", "JIRA", "Confluence", "Slack"
}

DOMAIN_KEYWORDS = {
    "fintech": ["finance", "fintech", "banking", "payment", "investment"],
    "healthcare": ["healthcare", "medical", "health", "pharma", "hospital"],
    "ecommerce": ["e-commerce", "retail", "shopping", "marketplace", "product"],
    "saas": ["saas", "b2b", "subscription", "subscription model"],
    "data": ["data", "analytics", "ml", "machine learning", "ai", "big data"],
    "devops": ["devops", "infrastructure", "deployment", "cloud", "kubernetes"],
    "social": ["social", "community", "network", "messaging", "chat"],
    "gaming": ["gaming", "game", "multiplayer", "fps", "mmo"]
}


class SeniorityLevel(str, Enum):
    """Seniority level categories."""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    CTO = "cto"


class ScoreCategory(str, Enum):
    """CV score categories."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


def ensure_build_dir():
    """Ensure build directory exists."""
    BUILD_DIR.mkdir(exist_ok=True)


def ensure_test_output_dir():
    """Ensure test output directory exists."""
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)