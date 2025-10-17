"""
Code Submission Models
Tracks code submissions, test results, and quality metrics
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TestCaseResult:
    """Individual test case result"""
    test_case: int
    passed: bool
    input: str
    expected: str
    actual: str
    error: Optional[str] = None

@dataclass
class CodeQualityMetrics:
    """Code quality analysis metrics"""
    lines_of_code: int
    cyclomatic_complexity: int
    num_functions: int
    num_comments: int
    avg_line_length: float
    has_type_hints: bool
    quality_score: float  # 0-10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CodeSubmission:
    """Complete code submission with results and metrics"""
    submission_id: str
    session_id: str
    timestamp: str
    code: str
    language: str
    function_name: str
    test_results: List[TestCaseResult]
    all_tests_passed: bool
    execution_time: float
    quality_metrics: Optional[CodeQualityMetrics] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "submission_id": self.submission_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "code": self.code,
            "language": self.language,
            "function_name": self.function_name,
            "test_results": [asdict(tr) for tr in self.test_results],
            "all_tests_passed": self.all_tests_passed,
            "execution_time": self.execution_time,
            "quality_metrics": self.quality_metrics.to_dict() if self.quality_metrics else None,
            "error": self.error
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CodeSubmission':
        """Create from dictionary"""
        test_results = [TestCaseResult(**tr) for tr in data.get('test_results', [])]

        quality_data = data.get('quality_metrics')
        quality_metrics = CodeQualityMetrics(**quality_data) if quality_data else None

        return CodeSubmission(
            submission_id=data['submission_id'],
            session_id=data['session_id'],
            timestamp=data['timestamp'],
            code=data['code'],
            language=data['language'],
            function_name=data['function_name'],
            test_results=test_results,
            all_tests_passed=data['all_tests_passed'],
            execution_time=data['execution_time'],
            quality_metrics=quality_metrics,
            error=data.get('error')
        )


class CodeSubmissionTracker:
    """Track and analyze code submissions"""

    @staticmethod
    def calculate_quality_metrics(code: str, language: str) -> CodeQualityMetrics:
        """
        Calculate code quality metrics

        Metrics:
        - Lines of code (excluding blanks and comments)
        - Cyclomatic complexity (simplified)
        - Number of functions/methods
        - Comment ratio
        - Average line length
        - Type hints usage (Python)
        - Overall quality score
        """
        lines = code.split('\n')
        non_blank_lines = [l for l in lines if l.strip()]

        # Basic metrics
        loc = len([l for l in non_blank_lines if not l.strip().startswith('#') and not l.strip().startswith('//')])
        num_comments = len([l for l in non_blank_lines if l.strip().startswith('#') or l.strip().startswith('//')])
        avg_line_length = sum(len(l) for l in non_blank_lines) / max(len(non_blank_lines), 1)

        # Count functions
        if language == 'python':
            num_functions = code.count('def ')
            has_type_hints = '->' in code or ': ' in code
        else:  # javascript
            num_functions = code.count('function ') + code.count('=>')
            has_type_hints = False

        # Simplified cyclomatic complexity (count decision points)
        complexity = (
            code.count('if ') +
            code.count('for ') +
            code.count('while ') +
            code.count('case ') +
            code.count('&&') +
            code.count('||')
        ) + 1  # Base complexity

        # Calculate quality score (0-10)
        quality_score = 5.0  # Base score

        # Bonus for good practices
        if 10 <= loc <= 100:
            quality_score += 1.0  # Appropriate length
        if num_comments > 0:
            quality_score += 0.5  # Has comments
        if has_type_hints:
            quality_score += 1.0  # Uses type hints
        if complexity <= 10:
            quality_score += 1.0  # Low complexity
        if 40 <= avg_line_length <= 80:
            quality_score += 0.5  # Good line length
        if num_functions > 0:
            quality_score += 1.0  # Modular code

        # Penalties
        if loc > 200:
            quality_score -= 1.0  # Too long
        if complexity > 20:
            quality_score -= 1.0  # Too complex
        if avg_line_length > 120:
            quality_score -= 0.5  # Lines too long

        quality_score = max(0.0, min(10.0, quality_score))

        return CodeQualityMetrics(
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            num_functions=num_functions,
            num_comments=num_comments,
            avg_line_length=round(avg_line_length, 2),
            has_type_hints=has_type_hints,
            quality_score=round(quality_score, 2)
        )

    @staticmethod
    def get_submission_summary(submissions: List[CodeSubmission]) -> Dict[str, Any]:
        """Generate summary statistics for submissions"""
        if not submissions:
            return {
                "total_submissions": 0,
                "total_passed": 0,
                "pass_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_quality_score": 0.0,
                "languages_used": []
            }

        total_passed = sum(1 for s in submissions if s.all_tests_passed)
        avg_exec_time = sum(s.execution_time for s in submissions) / len(submissions)

        quality_scores = [s.quality_metrics.quality_score for s in submissions if s.quality_metrics]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        languages = list(set(s.language for s in submissions))

        return {
            "total_submissions": len(submissions),
            "total_passed": total_passed,
            "pass_rate": round(total_passed / len(submissions) * 100, 2),
            "avg_execution_time": round(avg_exec_time, 3),
            "avg_quality_score": round(avg_quality, 2),
            "languages_used": languages,
            "first_attempt_success": submissions[0].all_tests_passed if submissions else False
        }