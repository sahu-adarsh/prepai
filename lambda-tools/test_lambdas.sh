#!/bin/bash

# Test PrepAI Lambda Functions
# Tests all three Lambda functions with sample payloads

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PrepAI Lambda Tools Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"

REGION=${AWS_REGION:-us-east-1}

# Test 1: Code Executor
echo -e "\n${YELLOW}Test 1: Code Executor${NC}"
echo "Testing Python code execution with Two Sum problem..."

cat > /tmp/code-executor-payload.json <<'EOF'
{
  "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
  "language": "python",
  "functionName": "two_sum",
  "testCases": [
    {"input": "[[2, 7, 11, 15], 9]", "expected": "[0, 1]"},
    {"input": "[[3, 2, 4], 6]", "expected": "[1, 2]"}
  ]
}
EOF

aws lambda invoke \
  --function-name prepai-code-executor \
  --payload file:///tmp/code-executor-payload.json \
  --region $REGION \
  /tmp/code-executor-response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Code Executor invoked successfully${NC}"
    echo "Response:"
    cat /tmp/code-executor-response.json | jq '.'
else
    echo -e "${RED}✗ Code Executor failed${NC}"
fi

# Test 2: CV Analyzer
echo -e "\n${YELLOW}Test 2: CV Analyzer${NC}"
echo "Testing CV analysis with sample resume text..."

cat > /tmp/cv-analyzer-payload.json <<'EOF'
{
  "cvText": "John Doe\njohn.doe@example.com | +1-555-123-4567\n\nEXPERIENCE\nSenior Software Engineer, Tech Corp (2020 - Present)\n- Developed microservices using Python and AWS\n- Led team of 5 engineers\n\nSoftware Engineer, StartupCo (2018 - 2020)\n- Built React applications\n- Implemented CI/CD pipelines\n\nEDUCATION\nB.Tech Computer Science, MIT (2018)\n\nSKILLS\nPython, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL",
  "extractSkills": true
}
EOF

aws lambda invoke \
  --function-name prepai-cv-analyzer \
  --payload file:///tmp/cv-analyzer-payload.json \
  --region $REGION \
  /tmp/cv-analyzer-response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CV Analyzer invoked successfully${NC}"
    echo "Response:"
    cat /tmp/cv-analyzer-response.json | jq '.'
else
    echo -e "${RED}✗ CV Analyzer failed${NC}"
fi

# Test 3: Performance Evaluator
echo -e "\n${YELLOW}Test 3: Performance Evaluator${NC}"
echo "Testing performance evaluation..."

cat > /tmp/performance-evaluator-payload.json <<'EOF'
{
  "sessionId": "test-session-123",
  "candidateName": "Jane Smith",
  "interviewType": "Google SDE",
  "duration": 1800,
  "conversationHistory": [
    {"role": "assistant", "content": "Tell me about yourself?"},
    {"role": "user", "content": "I have 3 years of experience in Python and AWS, building scalable microservices."},
    {"role": "assistant", "content": "Can you explain the Two Sum problem?"},
    {"role": "user", "content": "I would use a hash map to store complements. Time complexity O(n), space O(n)."}
  ],
  "codeSubmissions": [
    {
      "allTestsPassed": true,
      "executionTime": 0.05,
      "language": "python"
    }
  ],
  "saveToS3": false
}
EOF

aws lambda invoke \
  --function-name prepai-performance-evaluator \
  --payload file:///tmp/performance-evaluator-payload.json \
  --region $REGION \
  /tmp/performance-evaluator-response.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Performance Evaluator invoked successfully${NC}"
    echo "Response:"
    cat /tmp/performance-evaluator-response.json | jq '.'
else
    echo -e "${RED}✗ Performance Evaluator failed${NC}"
fi

# Cleanup
rm -f /tmp/*-payload.json /tmp/*-response.json

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Test Suite Complete${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}All Lambda functions tested!${NC}"
echo "If all tests passed, you can proceed to add Action Groups to your Bedrock Agent."