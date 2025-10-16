# PrepAI Lambda Tools

AWS Lambda functions that extend the Bedrock Agent with code execution, CV analysis, and performance evaluation capabilities.

## Overview

These Lambda functions are added to the Bedrock Agent as **Action Groups**, enabling the AI interviewer to:

1. **Execute Code** - Run and validate candidate code submissions
2. **Analyze CVs** - Extract information from resumes
3. **Evaluate Performance** - Generate comprehensive interview reports

---

## Directory Structure

```
lambda-tools/
├── code-executor/              # Code execution Lambda
│   ├── lambda_function.py
│   └── requirements.txt
├── cv-analyzer/                # CV analysis Lambda
│   ├── lambda_function.py
│   └── requirements.txt
├── performance-evaluator/      # Performance evaluation Lambda
│   ├── lambda_function.py
│   └── requirements.txt
├── action-groups/              # OpenAPI schemas for Bedrock
│   ├── code-executor-schema.json
│   ├── cv-analyzer-schema.json
│   └── performance-evaluator-schema.json
├── template.yaml               # SAM template for deployment
├── deploy.sh                   # Deployment script
├── test_lambdas.sh             # Test script
└── README.md                   # This file
```

---

## Quick Start

### Prerequisites

- AWS CLI configured
- SAM CLI installed (for SAM deployment) OR just AWS CLI
- Python 3.11+
- Bedrock Agent created (from Phase 2)

### Option 1: Deploy with SAM (Recommended)

```bash
cd lambda-tools

# Install SAM CLI if needed
# brew install aws-sam-cli  # macOS
# Or follow: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Deploy all functions
./deploy.sh
```

### Option 2: Deploy with AWS CLI

```bash
# Deploy each function manually
cd code-executor
pip install -r requirements.txt -t .
zip -r ../code-executor.zip .
cd ..

aws lambda create-function \
  --function-name prepai-code-executor \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/prepai-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://code-executor.zip \
  --timeout 30 \
  --memory-size 512

# Repeat for cv-analyzer and performance-evaluator
```

### Test Lambda Functions

```bash
# Test all functions
./test_lambdas.sh

# Or test individually
aws lambda invoke \
  --function-name prepai-code-executor \
  --payload '{"code":"def solution(arr): return sorted(arr)","language":"python","testCases":[{"input":"[3,1,2]","expected":"[1,2,3]"}],"functionName":"solution"}' \
  response.json

cat response.json
```

---

## Lambda Functions

### 1. Code Executor

**Function Name:** `prepai-code-executor`

**Purpose:** Execute candidate code in a sandboxed environment

**Input:**
```json
{
  "code": "def two_sum(nums, target): ...",
  "language": "python",
  "functionName": "two_sum",
  "testCases": [
    {"input": "[[2,7,11,15], 9]", "expected": "[0, 1]"}
  ]
}
```

**Output:**
```json
{
  "success": true,
  "allTestsPassed": true,
  "testResults": [...],
  "executionTime": 0.05
}
```

**Features:**
- Python support (JavaScript partially implemented)
- Sandboxed execution (restricted imports)
- Test case validation
- Timeout protection (5 seconds)
- Syntax and runtime error handling

**Security:**
- No file system access
- No network access
- Limited built-in functions
- Execution timeout enforced

---

### 2. CV Analyzer

**Function Name:** `prepai-cv-analyzer`

**Purpose:** Extract structured information from candidate resumes

**Input (S3):**
```json
{
  "s3Bucket": "prepai-user-data",
  "s3Key": "cvs/session123/resume.pdf",
  "extractSkills": true
}
```

**Input (Direct Text):**
```json
{
  "cvText": "John Doe\njohn@example.com\n...",
  "extractSkills": true
}
```

**Output:**
```json
{
  "success": true,
  "candidateName": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "skills": ["Python", "AWS", "React"],
  "totalYearsExperience": 3.5,
  "experience": [...],
  "education": [...],
  "summary": "Experienced engineer with 3+ years..."
}
```

**Features:**
- PDF text extraction (PyPDF2)
- Skills keyword matching (70+ technologies)
- Experience timeline extraction
- Education parsing
- Years of experience calculation
- Professional summary generation

**Supported Formats:**
- PDF (via PyPDF2)
- Plain text
- Future: DOCX (via python-docx)

---

### 3. Performance Evaluator

**Function Name:** `prepai-performance-evaluator`

**Purpose:** Generate comprehensive interview performance reports

**Input:**
```json
{
  "sessionId": "session123",
  "candidateName": "Jane Smith",
  "interviewType": "Google SDE",
  "conversationHistory": [...],
  "codeSubmissions": [...],
  "duration": 1800
}
```

**Output:**
```json
{
  "success": true,
  "overallScore": 7.8,
  "scores": {
    "technicalKnowledge": 8.0,
    "problemSolving": 7.5,
    "communication": 8.0,
    "codeQuality": 7.0,
    "culturalFit": 8.5
  },
  "strengths": [
    "Strong technical knowledge",
    "Clear communication"
  ],
  "improvements": [
    "Consider edge cases more thoroughly"
  ],
  "recommendation": "HIRE",
  "detailedFeedback": "...",
  "reportUrl": "s3://..."
}
```

**Evaluation Criteria:**
1. **Technical Knowledge** (30% weight)
   - Accuracy of answers
   - Depth of understanding
   - Technical terminology usage

2. **Problem Solving** (25% weight)
   - Approach and methodology
   - Code test pass rate
   - Optimization awareness

3. **Communication** (20% weight)
   - Clarity of explanations
   - Response structure
   - Active listening

4. **Code Quality** (15% weight)
   - Test pass rate
   - Execution efficiency
   - Error handling

5. **Cultural Fit** (10% weight)
   - Growth mindset indicators
   - Collaboration mentions
   - Enthusiasm and passion

**Recommendations:**
- `STRONG_HIRE` (8.5+)
- `HIRE` (7.5-8.4)
- `BORDERLINE` (6.5-7.4)
- `NO_HIRE` (5.5-6.4)
- `STRONG_NO_HIRE` (<5.5)

---

## Action Groups

Action Groups connect Lambda functions to the Bedrock Agent using OpenAPI 3.0 schemas.

### Adding Action Groups to Agent

1. **AWS Console → Bedrock → Agents → Your Agent**
2. Click **Edit in Agent Builder**
3. Scroll to **Action groups** section
4. Click **Add** for each tool:

**Code Executor:**
- Name: `CodeExecutor`
- Schema: Copy from `action-groups/code-executor-schema.json`
- Lambda: `prepai-code-executor`

**CV Analyzer:**
- Name: `CVAnalyzer`
- Schema: Copy from `action-groups/cv-analyzer-schema.json`
- Lambda: `prepai-cv-analyzer`

**Performance Evaluator:**
- Name: `PerformanceEvaluator`
- Schema: Copy from `action-groups/performance-evaluator-schema.json`
- Lambda: `prepai-performance-evaluator`

5. Click **Save** and **Prepare** agent

---

## Testing with Bedrock Agent

### Test Code Executor

**In Agent Test Panel:**
```
User: Here's my solution to reverse a string:
def reverse(s):
    return s[::-1]

Can you test it?
```

Expected: Agent uses CodeExecutor tool, returns test results

### Test CV Analyzer

**In Agent Test Panel:**
```
User: I uploaded my resume. Can you analyze it and ask relevant questions based on my experience?
```

Expected: Agent uses CVAnalyzer tool, extracts info, asks targeted questions

### Test Performance Evaluator

**In Agent Test Panel:**
```
User: Can you give me feedback on how I did in this interview?
```

Expected: Agent uses PerformanceEvaluator tool, generates comprehensive report

---

## Local Testing

### Test Code Executor Locally

```bash
cd code-executor
python lambda_function.py
```

### Test CV Analyzer Locally

```bash
cd cv-analyzer
python lambda_function.py
```

### Test Performance Evaluator Locally

```bash
cd performance-evaluator
python lambda_function.py
```

Each function has test code in `if __name__ == '__main__':` block.

---

## Monitoring & Logs

### View Lambda Logs

```bash
# Code Executor logs
aws logs tail /aws/lambda/prepai-code-executor --follow

# CV Analyzer logs
aws logs tail /aws/lambda/prepai-cv-analyzer --follow

# Performance Evaluator logs
aws logs tail /aws/lambda/prepai-performance-evaluator --follow
```

### CloudWatch Metrics

- Invocations
- Errors
- Duration
- Throttles

Access via: AWS Console → CloudWatch → Lambda → Your Function

---

## Cost Estimation

**Lambda Invocations (100 interviews/month):**
- Code Executor: ~200 invocations
- CV Analyzer: ~100 invocations
- Performance Evaluator: ~100 invocations

**Total: 400 invocations/month**

**Cost Breakdown:**
- Invocations: 400 × $0.20/1M = $0.00008
- Compute: 400 × 0.5 GB × 1s × $0.0000166667 = $0.003

**Total Monthly Cost: < $0.01** (essentially free!)

---

## Troubleshooting

### Issue: Lambda not found
**Solution:** Check function name matches exactly
```bash
aws lambda list-functions --query 'Functions[?contains(FunctionName, `prepai`)].FunctionName'
```

### Issue: Permission denied from Bedrock
**Solution:** Add Lambda invoke permission
```bash
aws lambda add-permission \
  --function-name prepai-code-executor \
  --statement-id AllowBedrockInvoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com
```

### Issue: Code execution timeout
**Solution:** Increase Lambda timeout
```bash
aws lambda update-function-configuration \
  --function-name prepai-code-executor \
  --timeout 60
```

### Issue: CV PDF parsing fails
**Solution:** Install PyPDF2 in deployment package
```bash
cd cv-analyzer
pip install PyPDF2 -t .
zip -r ../cv-analyzer.zip .
aws lambda update-function-code --function-name prepai-cv-analyzer --zip-file fileb://cv-analyzer.zip
```

---

## Security Considerations

### Code Executor
- ✅ Sandboxed execution (RestrictedPython)
- ✅ No file system access
- ✅ No network access
- ✅ Timeout enforced
- ✅ Limited built-in functions

### CV Analyzer
- ✅ S3 access restricted to prepai buckets
- ✅ No code execution from CV content
- ✅ Input validation

### Performance Evaluator
- ✅ No sensitive data exposure
- ✅ Reports stored securely in S3
- ✅ Read-only access to session data

---

## Updating Lambda Functions

### Update Code

```bash
# After modifying code
cd code-executor
zip -r ../code-executor.zip .

aws lambda update-function-code \
  --function-name prepai-code-executor \
  --zip-file fileb://code-executor.zip
```

### Update with SAM

```bash
# Modify code, then:
sam build
sam deploy
```

---

## Next Steps

1. ✅ Deploy all Lambda functions
2. ✅ Test functions individually
3. ✅ Add Action Groups to Bedrock Agent
4. ✅ Test tools via agent
5. ⬜ Integrate with voice pipeline
6. ⬜ Add more programming languages
7. ⬜ Enhance CV parsing with Textract
8. ⬜ Add code quality metrics

---

## Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Bedrock Action Groups](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-groups.html)
- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
- [OpenAPI 3.0 Spec](https://swagger.io/specification/)

---

**Questions?** See [PHASE3_SETUP_GUIDE.md](../PHASE3_SETUP_GUIDE.md) for detailed setup instructions.