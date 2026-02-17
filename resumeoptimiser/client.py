"""
FastAPI client for Resume Optimiser
Example usage of the API
"""
import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


class ResumeOptimiserClient:
    """Client for Resume Optimiser API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_base_skills(self) -> Dict[str, Any]:
        """Get base skills data."""
        response = self.session.get(f"{self.base_url}/api/v1/base-skills")
        response.raise_for_status()
        return response.json()
    
    def validate_base_skills(self) -> Dict[str, Any]:
        """Validate base skills."""
        response = self.session.post(f"{self.base_url}/api/v1/base-skills/validate")
        response.raise_for_status()
        return response.json()
    
    def parse_jd(self, jd_text: str) -> Dict[str, Any]:
        """Parse job description."""
        response = self.session.post(
            f"{self.base_url}/api/v1/parse-jd",
            json={"jd_text": jd_text}
        )
        response.raise_for_status()
        return response.json()
    
    def match_skills(self, jd_json: Dict[str, Any]) -> Dict[str, Any]:
        """Match skills to JD."""
        response = self.session.post(
            f"{self.base_url}/api/v1/match-skills",
            json={"jd_json": jd_json}
        )
        response.raise_for_status()
        return response.json()
    
    def score_cv(self, skill_match_json: Dict[str, Any], jd_json: Dict[str, Any]) -> Dict[str, Any]:
        """Score CV."""
        response = self.session.post(
            f"{self.base_url}/api/v1/score-cv",
            json={"skill_match_json": skill_match_json, "jd_json": jd_json}
        )
        response.raise_for_status()
        return response.json()
    
    def rewrite_cv(
        self,
        jd_json: Dict[str, Any],
        skill_match_json: Dict[str, Any],
        cv_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rewrite CV to LaTeX."""
        response = self.session.post(
            f"{self.base_url}/api/v1/rewrite-cv",
            json={
                "jd_json": jd_json,
                "skill_match_json": skill_match_json,
                "cv_score": cv_score
            }
        )
        response.raise_for_status()
        return response.json()
    
    def compile_pdf(self, latex_content: str) -> bytes:
        """Compile LaTeX to PDF."""
        response = self.session.post(
            f"{self.base_url}/api/v1/compile-pdf",
            json={"latex_content": latex_content}
        )
        response.raise_for_status()
        return response.content
    
    def generate_cv(self, jd_text: str) -> Dict[str, Any]:
        """Complete end-to-end CV generation."""
        response = self.session.post(
            f"{self.base_url}/api/v1/generate-cv",
            json={"jd_text": jd_text}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


def demo_workflow():
    """Demonstrate the complete workflow."""
    client = ResumeOptimiserClient()
    
    # Check health
    print("Checking server health...")
    health = client.health_check()
    print(f"✓ Server health: {health}\n")
    
    # Get base skills
    print("Fetching base skills...")
    skills = client.get_base_skills()
    print(f"✓ Loaded {len(skills['skills'])} skills for {skills['name']}\n")
    
    # Validate base skills
    print("Validating base skills...")
    validation = client.validate_base_skills()
    print(f"✓ Validation: {validation['message']}\n")
    
    # Sample JD
    sample_jd = """
    Senior Full-Stack Engineer
    
    We're looking for a Senior Full-Stack Engineer with 5+ years of experience.
    
    Requirements:
    - Expert in Python and FastAPI
    - Advanced React and TypeScript skills
    - PostgreSQL database design
    - AWS deployment experience
    - Docker and Kubernetes
    - CI/CD pipeline implementation
    
    Nice to have:
    - TensorFlow / Machine Learning
    - Microservices architecture
    - Team leadership experience
    """
    
    # End-to-end generation
    print("Generating CV from job description...")
    print(f"JD: {sample_jd[:50]}...\n")
    
    result = client.generate_cv(sample_jd)
    
    print("✓ End-to-end generation complete!\n")
    
    # Display results
    print("Results:")
    print(f"  Parsed JD: {len(result['parsed_jd']['core_stack'])} core skills")
    print(f"  Skill Match: {result['skill_match']['total_matched']}/{result['skill_match']['total_jd_requirements']} matched")
    print(f"  CV Score: {result['cv_score']['total_score']:.1f}/100 ({result['cv_score']['category'].upper()})")
    print(f"  LaTeX Generated: {len(result['rewritten_cv']['latex_content'])} chars")
    print(f"  PDF Path: {result['pdf_path']}")
    
    print("\n" + "="*60)
    print("WORKFLOW LOGS:")
    print("="*60)
    for log in result['logs']:
        print(f"  {log}")
    
    # Save results
    output_file = "api_response.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✓ Full response saved to {output_file}")


if __name__ == "__main__":
    try:
        demo_workflow()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to server.")
        print("  Make sure FastAPI server is running: python main.py")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()