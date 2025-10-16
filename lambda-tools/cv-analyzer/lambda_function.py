"""
CV Analyzer Lambda Function
Extracts and analyzes resume/CV information
Supports PDF and text extraction
"""

import json
import boto3
import re
from typing import Dict, Any, List
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Main Lambda handler for CV analysis

    Bedrock Agent event structure or direct invocation
    """

    try:
        # Check if this is a Bedrock Agent request or direct invocation
        is_bedrock_agent = 'messageVersion' in event

        if is_bedrock_agent:
            # Extract parameters from Bedrock Agent format
            parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
            request_body = event.get('requestBody', {}).get('content', {}).get('application/json', {})

            # Merge parameters and request body
            if isinstance(request_body, str):
                request_body = json.loads(request_body)

            params = {**request_body, **parameters}
        else:
            # Direct invocation format
            params = event

        # Get CV text either from S3 or direct input
        cv_text = params.get('cvText', '')

        if not cv_text:
            s3_bucket = params.get('s3Bucket')
            s3_key = params.get('s3Key')

            if not s3_bucket or not s3_key:
                error_response = {
                    'success': False,
                    'error': 'Either cvText or s3Bucket+s3Key required'
                }
                return format_response(event, error_response, 400)

            # Download CV from S3
            cv_text = download_cv_from_s3(s3_bucket, s3_key)

        # Analyze CV
        analysis = analyze_cv_text(cv_text, params.get('extractSkills', True))

        return format_response(event, analysis, 200)

    except Exception as e:
        error_response = {
            'success': False,
            'error': f'Analysis error: {str(e)}'
        }
        return format_response(event, error_response, 500)


def format_response(event: Dict, body: Dict, status_code: int = 200) -> Dict:
    """
    Format response for both Bedrock Agent and direct invocation
    """
    is_bedrock_agent = 'messageVersion' in event

    if is_bedrock_agent:
        # Bedrock Agent format
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', ''),
                "apiPath": event.get('apiPath', ''),
                "httpMethod": event.get('httpMethod', 'POST'),
                "httpStatusCode": status_code,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps(body)
                    }
                }
            }
        }
    else:
        # Direct invocation format
        return {
            'statusCode': status_code,
            'body': json.dumps(body)
        }


def download_cv_from_s3(bucket: str, key: str) -> str:
    """
    Download CV file from S3 and extract text
    """
    try:
        # Download file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()

        # Determine file type and extract text
        if key.lower().endswith('.pdf'):
            return extract_text_from_pdf(file_content)
        elif key.lower().endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            raise ValueError(f'Unsupported file type: {key}')

    except Exception as e:
        raise Exception(f'Failed to download CV from S3: {str(e)}')


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF using PyPDF2
    """
    try:
        import PyPDF2
        import io

        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ''

        for page in pdf_reader.pages:
            text += page.extract_text() + '\n'

        return text

    except ImportError:
        # Fallback: Return message if PyPDF2 not available
        return "PDF parsing requires PyPDF2 library. Using text fallback."
    except Exception as e:
        raise Exception(f'PDF extraction failed: {str(e)}')


def analyze_cv_text(text: str, extract_skills: bool = True) -> Dict[str, Any]:
    """
    Analyze CV text and extract structured information
    """
    analysis = {
        'success': True,
        'candidateName': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills': extract_skills_keywords(text) if extract_skills else [],
        'experience': extract_experience(text),
        'education': extract_education(text),
        'totalYearsExperience': calculate_years_experience(text),
        'technologies': extract_technologies(text),
        'summary': generate_summary(text)
    }

    return analysis


def extract_name(text: str) -> str:
    """
    Extract candidate name (usually at the top)
    """
    lines = text.strip().split('\n')
    if lines:
        # First non-empty line is usually the name
        first_line = lines[0].strip()
        if len(first_line) < 50 and not '@' in first_line:
            return first_line

    return "Name not found"


def extract_email(text: str) -> str:
    """
    Extract email address using regex
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else "Email not found"


def extract_phone(text: str) -> str:
    """
    Extract phone number
    """
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\+?\d{10,15}'  # International
    ]

    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return "Phone not found"


def extract_skills_keywords(text: str) -> List[str]:
    """
    Extract technical skills using keyword matching
    """
    # Common technical skills keywords
    skill_keywords = [
        # Programming Languages
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'TypeScript',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R',

        # Web Frameworks
        'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask',
        'FastAPI', 'Spring Boot', 'ASP.NET', 'Next.js',

        # Databases
        'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'DynamoDB', 'Cassandra',
        'Oracle', 'SQL Server', 'SQLite', 'Elasticsearch',

        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI',
        'Terraform', 'Ansible', 'CI/CD', 'Microservices',

        # Data & ML
        'Machine Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy',
        'Scikit-learn', 'Spark', 'Hadoop', 'Kafka', 'Airflow',

        # Other
        'Git', 'REST API', 'GraphQL', 'Agile', 'Scrum', 'Linux', 'Bash'
    ]

    found_skills = []
    text_lower = text.lower()

    for skill in skill_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return found_skills


def extract_technologies(text: str) -> List[str]:
    """
    Extract technology stack (similar to skills but more focused)
    """
    return extract_skills_keywords(text)  # Same as skills for now


def extract_experience(text: str) -> List[Dict[str, str]]:
    """
    Extract work experience sections
    This is a simplified version - production would use NLP
    """
    experiences = []

    # Look for common experience section headers
    experience_section = extract_section(text, ['experience', 'work history', 'employment'])

    if experience_section:
        # Look for year patterns (2020-2023, 2020-Present, etc.)
        year_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
        matches = re.finditer(year_pattern, experience_section, re.IGNORECASE)

        for match in matches:
            start_year = match.group(1)
            end_year = match.group(2)

            # Extract context around the date (company, role)
            context_start = max(0, match.start() - 200)
            context_end = min(len(experience_section), match.end() + 200)
            context = experience_section[context_start:context_end]

            experiences.append({
                'duration': f'{start_year}-{end_year}',
                'context': context.strip()[:200]  # Limit length
            })

    return experiences[:5]  # Limit to 5 most recent


def extract_education(text: str) -> List[Dict[str, str]]:
    """
    Extract education information
    """
    education = []

    education_section = extract_section(text, ['education', 'academic', 'qualification'])

    if education_section:
        # Look for degree keywords
        degree_keywords = ['B.Tech', 'B.E.', 'M.Tech', 'M.S.', 'B.S.', 'MBA', 'PhD',
                          'Bachelor', 'Master', 'Doctorate']

        for keyword in degree_keywords:
            if keyword.lower() in education_section.lower():
                # Extract context around degree
                idx = education_section.lower().find(keyword.lower())
                context_start = max(0, idx - 50)
                context_end = min(len(education_section), idx + 150)
                context = education_section[context_start:context_end]

                education.append({
                    'degree': keyword,
                    'context': context.strip()
                })

    return education[:3]  # Limit to 3 entries


def extract_section(text: str, section_keywords: List[str]) -> str:
    """
    Extract a specific section from CV based on keywords
    """
    text_lower = text.lower()

    for keyword in section_keywords:
        idx = text_lower.find(keyword)
        if idx != -1:
            # Extract from keyword to next 1000 characters
            section_end = min(len(text), idx + 1000)
            return text[idx:section_end]

    return ""


def calculate_years_experience(text: str) -> float:
    """
    Calculate total years of professional experience
    """
    current_year = datetime.now().year
    total_years = 0

    # Find all year ranges
    year_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)'
    matches = re.finditer(year_pattern, text, re.IGNORECASE)

    for match in matches:
        start_year = int(match.group(1))
        end_str = match.group(2).lower()

        if end_str in ['present', 'current']:
            end_year = current_year
        else:
            end_year = int(end_str)

        years = end_year - start_year
        if years > 0 and years < 50:  # Sanity check
            total_years += years

    return round(total_years, 1)


def generate_summary(text: str) -> str:
    """
    Generate a brief summary of the candidate
    """
    skills = extract_skills_keywords(text)
    years_exp = calculate_years_experience(text)

    if years_exp > 0 and skills:
        top_skills = ', '.join(skills[:3])
        return f"Experienced professional with {years_exp} years in {top_skills}"
    elif skills:
        return f"Technical professional with skills in {', '.join(skills[:3])}"
    else:
        return "Professional candidate"


# For local testing
if __name__ == '__main__':
    test_cv = """
    John Doe
    john.doe@example.com | +1-555-123-4567

    EXPERIENCE
    Senior Software Engineer, Tech Corp (2020 - Present)
    - Developed microservices using Python and AWS
    - Led team of 5 engineers

    Software Engineer, StartupCo (2018 - 2020)
    - Built React applications
    - Implemented CI/CD pipelines

    EDUCATION
    B.Tech Computer Science, MIT (2018)

    SKILLS
    Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL
    """

    event = {
        'cvText': test_cv,
        'extractSkills': True
    }

    result = lambda_handler(event, None)
    print(json.dumps(json.loads(result['body']), indent=2))