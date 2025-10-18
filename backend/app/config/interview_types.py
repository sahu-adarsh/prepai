"""
Interview type configurations for Bedrock Agent session attributes.
These are passed as context instead of being embedded in the agent instruction.
"""

INTERVIEW_CONFIGS = {
    "google_sde": {
        "display_name": "Google India - SDE",
        "focus_areas": "algorithms,data_structures,system_design,coding",
        "key_topics": "arrays,trees,graphs,dynamic_programming,complexity_analysis",
        "difficulty_range": "medium_to_hard",
        "evaluation_weight": "technical:40,problem_solving:30,communication:20,code_quality:10"
    },

    "amazon_sde": {
        "display_name": "Amazon India - SDE",
        "focus_areas": "leadership_principles,coding,system_design,behavioral",
        "key_topics": "ownership,customer_obsession,oop,scalability,STAR_method",
        "difficulty_range": "medium_to_hard",
        "evaluation_weight": "technical:35,problem_solving:25,communication:20,leadership:20"
    },

    "microsoft_sde": {
        "display_name": "Microsoft - SDE",
        "focus_areas": "problem_solving,coding,collaboration,design",
        "key_topics": "data_structures,algorithms,api_design,debugging,testing",
        "difficulty_range": "medium",
        "evaluation_weight": "technical:40,problem_solving:30,communication:20,teamwork:10"
    },

    "aws_solutions_architect": {
        "display_name": "AWS Solutions Architect",
        "focus_areas": "cloud_architecture,aws_services,best_practices,cost_optimization",
        "key_topics": "well_architected,high_availability,disaster_recovery,security,compliance",
        "difficulty_range": "medium_to_hard",
        "evaluation_weight": "technical:50,problem_solving:30,communication:20"
    },

    "azure_solutions_architect": {
        "display_name": "Azure Solutions Architect",
        "focus_areas": "azure_services,hybrid_cloud,enterprise_solutions",
        "key_topics": "compute,storage,networking,iam,migration,cost_management",
        "difficulty_range": "medium_to_hard",
        "evaluation_weight": "technical:50,problem_solving:30,communication:20"
    },

    "gcp_solutions_architect": {
        "display_name": "GCP Solutions Architect",
        "focus_areas": "gcp_services,data_analytics,ml_integration",
        "key_topics": "compute_engine,kubernetes,cloud_functions,bigquery,iam,networking",
        "difficulty_range": "medium_to_hard",
        "evaluation_weight": "technical:50,problem_solving:30,communication:20"
    },

    "cv_grilling": {
        "display_name": "CV Grilling / Behavioral",
        "focus_areas": "resume_deep_dive,project_experience,behavioral_competencies",
        "key_topics": "project_details,challenges,teamwork,conflict_resolution,STAR_method",
        "difficulty_range": "medium",
        "evaluation_weight": "communication:40,experience:30,problem_solving:20,cultural_fit:10"
    },

    "coding_practice": {
        "display_name": "Coding Round Practice",
        "focus_areas": "pure_coding,algorithms,optimization",
        "key_topics": "leetcode_style,multiple_approaches,complexity_analysis,code_quality",
        "difficulty_range": "easy_to_hard",
        "evaluation_weight": "code_quality:40,problem_solving:40,communication:20"
    }
}


# Interview flow phases
INTERVIEW_PHASES = {
    "introduction": {
        "duration_minutes": "1-2",
        "guidelines": "greet,introduce_yourself,explain_format,ask_introduction"
    },
    "background": {
        "duration_minutes": "3-5",
        "guidelines": "current_role,projects,technologies,motivation"
    },
    "technical": {
        "duration_minutes": "15-20",
        "guidelines": "adapt_difficulty,one_question_at_a_time,provide_hints_when_stuck"
    },
    "problem_solving": {
        "duration_minutes": "10-15",
        "guidelines": "coding_problems,think_aloud,edge_cases,complexity_discussion"
    },
    "candidate_questions": {
        "duration_minutes": "3-5",
        "guidelines": "invite_questions,thoughtful_answers,evaluate_question_quality"
    },
    "closing": {
        "duration_minutes": "1-2",
        "guidelines": "thank_candidate,next_steps,brief_positive_feedback"
    }
}


def get_interview_config(interview_type: str) -> dict:
    """
    Get configuration for a specific interview type.

    Args:
        interview_type: Type of interview (e.g., "google_sde", "aws_solutions_architect")

    Returns:
        Configuration dictionary for the interview type
    """
    # Normalize the interview type (remove spaces, lowercase)
    normalized_type = interview_type.lower().replace(" ", "_").replace("-", "_")

    # Try exact match first
    if normalized_type in INTERVIEW_CONFIGS:
        return INTERVIEW_CONFIGS[normalized_type]

    # Try partial match
    for key, config in INTERVIEW_CONFIGS.items():
        if normalized_type in key or key in normalized_type:
            return config

    # Default to general technical interview
    return {
        "display_name": interview_type,
        "focus_areas": "technical,problem_solving,communication",
        "key_topics": "general_technical_questions",
        "difficulty_range": "medium",
        "evaluation_weight": "technical:40,problem_solving:30,communication:30"
    }