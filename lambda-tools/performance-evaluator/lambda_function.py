"""
Performance Evaluator Lambda Function
Generates comprehensive interview performance reports
Scores candidates across multiple criteria
"""

import json
import boto3
import time
from typing import Dict, Any, List
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Main Lambda handler for performance evaluation

    Event structure:
    {
        "sessionId": "session123",
        "conversationHistory": [...],
        "codeSubmissions": [...],
        "interviewType": "Google SDE",
        "duration": 1800,
        "candidateName": "John Doe"
    }
    """

    try:
        # Parse event
        if isinstance(event, str):
            event = json.loads(event)

        session_id = event.get('sessionId')
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'sessionId is required'
                })
            }

        # Generate performance report
        report = generate_performance_report(event)

        # Save report to S3
        if event.get('saveToS3', True):
            save_report_to_s3(session_id, report)

        return {
            'statusCode': 200,
            'body': json.dumps(report)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Evaluation error: {str(e)}'
            })
        }


def generate_performance_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive performance report
    """
    session_id = data.get('sessionId')
    interview_type = data.get('interviewType', 'Technical Interview')
    candidate_name = data.get('candidateName', 'Candidate')
    conversation_history = data.get('conversationHistory', [])
    code_submissions = data.get('codeSubmissions', [])
    duration = data.get('duration', 0)

    # Calculate scores
    scores = calculate_scores(
        conversation_history,
        code_submissions,
        interview_type
    )

    # Calculate overall score (weighted average)
    overall_score = calculate_overall_score(scores)

    # Generate feedback
    strengths = identify_strengths(scores, conversation_history, code_submissions)
    improvements = identify_improvements(scores, conversation_history, code_submissions)
    recommendation = get_recommendation(overall_score)

    # Generate detailed feedback
    detailed_feedback = generate_detailed_feedback(
        scores,
        strengths,
        improvements,
        interview_type
    )

    report = {
        'success': True,
        'sessionId': session_id,
        'candidateName': candidate_name,
        'interviewType': interview_type,
        'timestamp': datetime.utcnow().isoformat(),
        'duration': duration,
        'overallScore': round(overall_score, 1),
        'scores': scores,
        'strengths': strengths,
        'improvements': improvements,
        'recommendation': recommendation,
        'detailedFeedback': detailed_feedback,
        'metrics': {
            'totalQuestions': count_questions(conversation_history),
            'codeSubmissions': len(code_submissions),
            'averageResponseTime': calculate_avg_response_time(conversation_history)
        }
    }

    return report


def calculate_scores(
    conversation_history: List[Dict],
    code_submissions: List[Dict],
    interview_type: str
) -> Dict[str, float]:
    """
    Calculate scores across different criteria
    """
    scores = {
        'technicalKnowledge': 0.0,
        'problemSolving': 0.0,
        'communication': 0.0,
        'codeQuality': 0.0,
        'culturalFit': 0.0
    }

    # Technical Knowledge (based on correctness of answers)
    scores['technicalKnowledge'] = evaluate_technical_knowledge(
        conversation_history,
        interview_type
    )

    # Problem Solving (based on approach and reasoning)
    scores['problemSolving'] = evaluate_problem_solving(
        conversation_history,
        code_submissions
    )

    # Communication (based on clarity and responsiveness)
    scores['communication'] = evaluate_communication(conversation_history)

    # Code Quality (based on code submissions)
    if code_submissions:
        scores['codeQuality'] = evaluate_code_quality(code_submissions)
    else:
        scores['codeQuality'] = 5.0  # Neutral if no code

    # Cultural Fit (based on behavioral responses)
    scores['culturalFit'] = evaluate_cultural_fit(
        conversation_history,
        interview_type
    )

    return scores


def evaluate_technical_knowledge(
    conversation_history: List[Dict],
    interview_type: str
) -> float:
    """
    Evaluate technical knowledge based on conversation
    """
    # Simplified scoring: Count user responses
    user_responses = [msg for msg in conversation_history if msg.get('role') == 'user']

    if not user_responses:
        return 5.0

    # Heuristics:
    # - Longer, detailed responses = higher score
    # - Technical terms = higher score

    total_score = 0
    count = 0

    technical_keywords = [
        'algorithm', 'complexity', 'data structure', 'optimize', 'performance',
        'scalability', 'database', 'api', 'architecture', 'design pattern',
        'aws', 'cloud', 'microservices', 'cache', 'queue'
    ]

    for response in user_responses[-10:]:  # Last 10 responses
        content = response.get('content', '').lower()
        words = len(content.split())

        # Base score from length
        if words > 50:
            score = 8
        elif words > 30:
            score = 7
        elif words > 15:
            score = 6
        else:
            score = 5

        # Bonus for technical terms
        technical_count = sum(1 for kw in technical_keywords if kw in content)
        score += min(technical_count * 0.5, 2)  # Max +2 bonus

        total_score += min(score, 10)
        count += 1

    return round(total_score / count if count > 0 else 5.0, 1)


def evaluate_problem_solving(
    conversation_history: List[Dict],
    code_submissions: List[Dict]
) -> float:
    """
    Evaluate problem-solving skills
    """
    score = 5.0  # Base score

    # Check code submissions
    if code_submissions:
        passed_tests = sum(1 for sub in code_submissions if sub.get('allTestsPassed'))
        total_submissions = len(code_submissions)

        if total_submissions > 0:
            pass_rate = passed_tests / total_submissions
            score = 4 + (pass_rate * 6)  # 4-10 scale

    # Check for problem-solving keywords in conversation
    problem_solving_keywords = [
        'approach', 'strategy', 'solution', 'optimize', 'tradeoff',
        'edge case', 'complexity', 'efficient', 'alternative'
    ]

    user_responses = [msg.get('content', '').lower()
                     for msg in conversation_history
                     if msg.get('role') == 'user']

    keyword_count = sum(
        1 for response in user_responses
        for keyword in problem_solving_keywords
        if keyword in response
    )

    # Boost score based on problem-solving discussion
    if keyword_count > 5:
        score += 1
    if keyword_count > 10:
        score += 0.5

    return round(min(score, 10), 1)


def evaluate_communication(conversation_history: List[Dict]) -> float:
    """
    Evaluate communication skills
    """
    user_responses = [msg for msg in conversation_history if msg.get('role') == 'user']

    if not user_responses:
        return 5.0

    total_score = 0
    count = 0

    for response in user_responses:
        content = response.get('content', '')
        words = len(content.split())
        sentences = content.count('.') + content.count('!') + content.count('?')

        # Good communication: 20-100 words, 2-5 sentences
        if 20 <= words <= 100 and 2 <= sentences <= 5:
            score = 8
        elif words < 10:
            score = 5  # Too brief
        elif words > 150:
            score = 6  # Too verbose
        else:
            score = 7

        total_score += score
        count += 1

    return round(total_score / count if count > 0 else 5.0, 1)


def evaluate_code_quality(code_submissions: List[Dict]) -> float:
    """
    Evaluate code quality from submissions
    """
    if not code_submissions:
        return 5.0

    total_score = 0
    count = 0

    for submission in code_submissions:
        score = 5.0

        # Passed all tests
        if submission.get('allTestsPassed'):
            score = 8

        # Check execution time (efficiency)
        exec_time = submission.get('executionTime', 0)
        if exec_time < 0.1:
            score += 1
        elif exec_time > 1.0:
            score -= 0.5

        # Check for errors
        if submission.get('error'):
            score = min(score, 6)

        total_score += score
        count += 1

    return round(total_score / count if count > 0 else 5.0, 1)


def evaluate_cultural_fit(
    conversation_history: List[Dict],
    interview_type: str
) -> float:
    """
    Evaluate cultural fit based on behavioral indicators
    """
    # Look for positive indicators in conversation
    positive_indicators = [
        'learn', 'grow', 'collaborate', 'team', 'feedback',
        'challenge', 'passionate', 'excited', 'interested'
    ]

    user_content = ' '.join([
        msg.get('content', '').lower()
        for msg in conversation_history
        if msg.get('role') == 'user'
    ])

    indicator_count = sum(1 for indicator in positive_indicators if indicator in user_content)

    # Base score of 6, increase with positive indicators
    score = 6.0 + min(indicator_count * 0.3, 4)

    return round(min(score, 10), 1)


def calculate_overall_score(scores: Dict[str, float]) -> float:
    """
    Calculate weighted overall score
    """
    weights = {
        'technicalKnowledge': 0.30,
        'problemSolving': 0.25,
        'communication': 0.20,
        'codeQuality': 0.15,
        'culturalFit': 0.10
    }

    overall = sum(scores[key] * weights[key] for key in scores)
    return round(overall, 1)


def identify_strengths(
    scores: Dict[str, float],
    conversation_history: List[Dict],
    code_submissions: List[Dict]
) -> List[str]:
    """
    Identify candidate strengths
    """
    strengths = []

    # Check high scores
    for criterion, score in scores.items():
        if score >= 8.0:
            strength_map = {
                'technicalKnowledge': 'Strong technical knowledge and understanding of concepts',
                'problemSolving': 'Excellent problem-solving approach and logical thinking',
                'communication': 'Clear and effective communication skills',
                'codeQuality': 'High-quality, efficient code implementation',
                'culturalFit': 'Great cultural fit and alignment with team values'
            }
            strengths.append(strength_map.get(criterion, f'Strong {criterion}'))

    # Check code submissions
    if code_submissions and all(sub.get('allTestsPassed') for sub in code_submissions):
        strengths.append('Consistently passed all test cases on first attempt')

    # Ensure at least one strength
    if not strengths:
        strengths.append('Demonstrated solid technical foundation')

    return strengths[:5]  # Top 5 strengths


def identify_improvements(
    scores: Dict[str, float],
    conversation_history: List[Dict],
    code_submissions: List[Dict]
) -> List[str]:
    """
    Identify areas for improvement
    """
    improvements = []

    # Check low scores
    for criterion, score in scores.items():
        if score < 6.0:
            improvement_map = {
                'technicalKnowledge': 'Deepen understanding of core technical concepts',
                'problemSolving': 'Practice more algorithmic problem-solving',
                'communication': 'Work on explaining solutions more clearly',
                'codeQuality': 'Focus on writing cleaner, more optimized code',
                'culturalFit': 'Demonstrate more enthusiasm and alignment with values'
            }
            improvements.append(improvement_map.get(criterion, f'Improve {criterion}'))

    # Check code issues
    if code_submissions:
        failed_submissions = [sub for sub in code_submissions if not sub.get('allTestsPassed')]
        if len(failed_submissions) > len(code_submissions) / 2:
            improvements.append('Practice more coding problems to improve accuracy')

    # Ensure at least one improvement area
    if not improvements:
        improvements.append('Continue practicing to maintain strong performance')

    return improvements[:5]  # Top 5 improvements


def get_recommendation(overall_score: float) -> str:
    """
    Get hiring recommendation based on overall score
    """
    if overall_score >= 8.5:
        return 'STRONG_HIRE'
    elif overall_score >= 7.5:
        return 'HIRE'
    elif overall_score >= 6.5:
        return 'BORDERLINE'
    elif overall_score >= 5.5:
        return 'NO_HIRE'
    else:
        return 'STRONG_NO_HIRE'


def generate_detailed_feedback(
    scores: Dict[str, float],
    strengths: List[str],
    improvements: List[str],
    interview_type: str
) -> str:
    """
    Generate detailed narrative feedback
    """
    feedback_parts = []

    feedback_parts.append(f"Interview Type: {interview_type}")
    feedback_parts.append("")

    feedback_parts.append("Performance Summary:")
    feedback_parts.append(f"The candidate demonstrated {get_performance_level(scores['technicalKnowledge'])} technical knowledge, "
                         f"{get_performance_level(scores['problemSolving'])} problem-solving abilities, and "
                         f"{get_performance_level(scores['communication'])} communication skills.")
    feedback_parts.append("")

    feedback_parts.append("Key Strengths:")
    for i, strength in enumerate(strengths, 1):
        feedback_parts.append(f"{i}. {strength}")
    feedback_parts.append("")

    feedback_parts.append("Areas for Improvement:")
    for i, improvement in enumerate(improvements, 1):
        feedback_parts.append(f"{i}. {improvement}")
    feedback_parts.append("")

    feedback_parts.append("Next Steps:")
    feedback_parts.append("Continue practicing interview questions, focus on the improvement areas mentioned above, "
                         "and maintain your strengths.")

    return '\n'.join(feedback_parts)


def get_performance_level(score: float) -> str:
    """
    Convert score to performance level description
    """
    if score >= 8.5:
        return "excellent"
    elif score >= 7.5:
        return "strong"
    elif score >= 6.5:
        return "good"
    elif score >= 5.5:
        return "satisfactory"
    else:
        return "developing"


def count_questions(conversation_history: List[Dict]) -> int:
    """
    Count questions asked by interviewer
    """
    assistant_messages = [msg for msg in conversation_history if msg.get('role') == 'assistant']
    return sum(1 for msg in assistant_messages if '?' in msg.get('content', ''))


def calculate_avg_response_time(conversation_history: List[Dict]) -> float:
    """
    Calculate average response time (if timestamps available)
    """
    if len(conversation_history) < 2:
        return 0.0

    # Simplified - assumes alternating messages
    return 30.0  # Placeholder: 30 seconds average


def save_report_to_s3(session_id: str, report: Dict[str, Any]) -> None:
    """
    Save report to S3
    """
    try:
        bucket = 'prepai-user-data'
        key = f'reports/{session_id}/performance_report.json'

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )

        report['reportUrl'] = f's3://{bucket}/{key}'

    except Exception as e:
        print(f'Failed to save report to S3: {str(e)}')


# For local testing
if __name__ == '__main__':
    test_event = {
        'sessionId': 'test123',
        'candidateName': 'John Doe',
        'interviewType': 'Google SDE',
        'duration': 1800,
        'conversationHistory': [
            {'role': 'assistant', 'content': 'Tell me about yourself?'},
            {'role': 'user', 'content': 'I have 3 years of experience in Python and AWS, building scalable microservices.'},
            {'role': 'assistant', 'content': 'Can you explain the Two Sum problem?'},
            {'role': 'user', 'content': 'I would use a hash map to store complements. Time complexity O(n), space O(n).'}
        ],
        'codeSubmissions': [
            {
                'allTestsPassed': True,
                'executionTime': 0.05,
                'language': 'python'
            }
        ],
        'saveToS3': False
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result['body']), indent=2))