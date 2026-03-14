"""Test hallucination detection in MarkdownRewriteAgent."""

from app.agents.markdown_rewriter import MarkdownRewriteAgent


class TestHallucinationDetection:
    """Test the _remove_hallucinated_content method."""

    def test_remove_placeholder_company_name(self) -> None:
        """Should remove entries with 'Company Name' placeholder."""
        markdown = """\
## EXPERIENCE

**AI Agent Architect | Company Name**
Month YYYY - Month YYYY | Tunis, Tunisia
- Implemented RAG-based solutions
- Optimized AI agent performance by 40%

**Real Job | REAL COMPANY**
January 2024 - Present | Tunis, Tunisia
- Conducted real work
"""
        result = MarkdownRewriteAgent._remove_hallucinated_content(markdown)
        assert "Company Name" not in result
        assert "REAL COMPANY" in result
        assert "Conducted real work" in result

    def test_remove_placeholder_month_yyyy_pattern(self) -> None:
        """Should remove entries with 'Month YYYY' patterns."""
        markdown = """\
## EXPERIENCE

**Fake Role | Acme Corp**
Month YYYY - Month YYYY | Some City
- Some fake achievement

**Real Role | Real Corp**
January 2024 - February 2024 | Tunis, Tunisia
- Real achievement
"""
        result = MarkdownRewriteAgent._remove_hallucinated_content(markdown)
        assert "Month YYYY" not in result
        assert "Some fake achievement" not in result
        assert "Real achievement" in result

    def test_preserve_real_content_with_dates(self) -> None:
        """Should preserve real dates and content."""
        markdown = """\
## EXPERIENCE

**Developer | Microsoft**
January 2023 - December 2023 | Seattle, USA
- Built cloud solutions
- Improved performance by 25%

## SKILLS

**Languages:** Python, JavaScript
"""
        result = MarkdownRewriteAgent._remove_hallucinated_content(markdown)
        assert "Developer | Microsoft" in result
        assert "January 2023 - December 2023" in result
        assert "Built cloud solutions" in result
        assert "Languages:** Python, JavaScript" in result

    def test_is_placeholder_line(self) -> None:
        """Test placeholder line detection."""
        assert MarkdownRewriteAgent._is_placeholder_line("Company Name")
        assert MarkdownRewriteAgent._is_placeholder_line("company name")
        assert MarkdownRewriteAgent._is_placeholder_line("Month YYYY")
        assert MarkdownRewriteAgent._is_placeholder_line("month yyyy")
        assert not MarkdownRewriteAgent._is_placeholder_line("Real Company")
        assert not MarkdownRewriteAgent._is_placeholder_line("January 2024")

    def test_is_fake_company_entry(self) -> None:
        """Test fake company entry detection."""
        assert MarkdownRewriteAgent._is_fake_company_entry("**AI Engineer | Company Name**")
        assert MarkdownRewriteAgent._is_fake_company_entry("**Developer | COMPANY NAME**")
        assert not MarkdownRewriteAgent._is_fake_company_entry("**Developer | Microsoft**")
        assert not MarkdownRewriteAgent._is_fake_company_entry("**Developer | Real Corp**")

    def test_is_placeholder_date_line(self) -> None:
        """Test placeholder date line detection."""
        assert MarkdownRewriteAgent._is_placeholder_date_line("Month YYYY - Month YYYY | City")
        assert MarkdownRewriteAgent._is_placeholder_date_line("January Month YYYY | Location")
        assert not MarkdownRewriteAgent._is_placeholder_date_line("January 2024 - February 2024 | City")
        assert not MarkdownRewriteAgent._is_placeholder_date_line("January 2023 - Present | City")

    def test_remove_multiple_hallucinations(self) -> None:
        """Should remove multiple hallucinated sections."""
        markdown = """\
## EXPERIENCE

**AI Agent Architect & Financial Analyst**
*Company Name* | Month YYYY - Month YYYY | Tunis, Tunisia
- Led the development of production-ready Generative AI systems using Azure AI Search
- Engineered multi-agent architectures with Copilot Studio
- Implemented RAG-based solutions for credit risk analytics
- Optimized AI agent performance by 40% through Azure Power Platform automation

**Corporate Banking Officer | STB BANK**
January 2026 - Present | Tunis, Tunisia
- Conducted comprehensive credit analysis
- Assessed credit risk

**Generative AI Consultant | JEMS**
September 2024 - December 2025 | Tunis, Tunisia
- Architected production-grade LLM applications
- Developed AI-powered recruitment system
"""
        result = MarkdownRewriteAgent._remove_hallucinated_content(markdown)
        assert "Company Name" not in result
        assert "Month YYYY" not in result
        assert "Led the development of production-ready Generative AI systems using Azure" not in result
        assert "STB BANK" in result
        assert "JEMS" in result
        assert "Conducted comprehensive credit analysis" in result
        assert "Architected production-grade LLM applications" in result

    def test_preserve_section_headings(self) -> None:
        """Should preserve all section headings."""
        markdown = """\
## EXPERIENCE

**Fake Job | Company Name**
Month YYYY - Present | City
- Fake bullet

## EDUCATION

**BS in CS | Fake University**
Month YYYY - Month YYYY
- Fake education

## SKILLS

**Languages:** Fake Language
"""
        result = MarkdownRewriteAgent._remove_hallucinated_content(markdown)
        assert "## EXPERIENCE" in result
        assert "## EDUCATION" in result
        assert "## SKILLS" in result
