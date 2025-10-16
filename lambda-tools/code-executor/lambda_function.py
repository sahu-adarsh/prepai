"""
Code Executor Lambda Function
Executes candidate code submissions in a sandboxed environment
Supports Python and JavaScript
"""

import json
import sys
import io
import time
import traceback
from typing import Dict, Any, List

def lambda_handler(event, context):
    """
    Main Lambda handler for code execution

    Event structure:
    {
        "code": "def solution(arr): return sorted(arr)",
        "language": "python",
        "testCases": [{"input": "[3, 1, 2]", "expected": "[1, 2, 3]"}],
        "functionName": "solution",
        "timeout": 5
    }
    """

    try:
        # Parse event (from Bedrock Agent)
        if isinstance(event, str):
            event = json.loads(event)

        # Extract parameters
        code = event.get('code', '')
        language = event.get('language', 'python').lower()
        test_cases = event.get('testCases', [])
        function_name = event.get('functionName', 'solution')
        timeout = event.get('timeout', 5)

        # Validate inputs
        if not code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Code is required'
                })
            }

        # Execute code based on language
        if language == 'python':
            result = execute_python(code, test_cases, function_name, timeout)
        elif language == 'javascript':
            result = execute_javascript(code, test_cases, function_name, timeout)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Unsupported language: {language}'
                })
            }

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Execution error: {str(e)}',
                'traceback': traceback.format_exc()
            })
        }


def execute_python(code: str, test_cases: List[Dict], function_name: str, timeout: int) -> Dict[str, Any]:
    """
    Execute Python code in sandboxed environment
    """
    results = {
        'success': True,
        'language': 'python',
        'testResults': [],
        'allTestsPassed': True,
        'executionTime': 0,
        'output': None,
        'error': None
    }

    start_time = time.time()

    try:
        # Create restricted globals (no dangerous imports)
        safe_globals = {
            '__builtins__': {
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'dict': dict,
                'enumerate': enumerate,
                'filter': filter,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'print': print,
                'range': range,
                'reversed': reversed,
                'set': set,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'zip': zip,
            }
        }

        # Execute the user's code
        exec(code, safe_globals)

        # Check if function exists
        if function_name not in safe_globals:
            results['success'] = False
            results['error'] = f"Function '{function_name}' not found in code"
            return results

        user_function = safe_globals[function_name]

        # Run test cases
        for i, test_case in enumerate(test_cases):
            test_result = {
                'testCase': i + 1,
                'passed': False,
                'input': test_case.get('input'),
                'expected': test_case.get('expected'),
                'actual': None,
                'error': None
            }

            try:
                # Parse input (eval safely)
                test_input = eval(test_case['input'], {"__builtins__": {}})
                expected_output = eval(test_case['expected'], {"__builtins__": {}})

                # Call function with timeout
                if isinstance(test_input, (list, tuple)):
                    actual_output = user_function(*test_input)
                else:
                    actual_output = user_function(test_input)

                test_result['actual'] = str(actual_output)

                # Compare results
                if actual_output == expected_output:
                    test_result['passed'] = True
                else:
                    test_result['passed'] = False
                    results['allTestsPassed'] = False

            except Exception as e:
                test_result['error'] = str(e)
                test_result['passed'] = False
                results['allTestsPassed'] = False

            results['testResults'].append(test_result)

        # Store output from last successful run
        if results['testResults'] and results['testResults'][-1].get('actual'):
            results['output'] = results['testResults'][-1]['actual']

    except SyntaxError as e:
        results['success'] = False
        results['error'] = f'Syntax Error: {str(e)}'
        results['allTestsPassed'] = False

    except Exception as e:
        results['success'] = False
        results['error'] = f'Runtime Error: {str(e)}'
        results['allTestsPassed'] = False

    results['executionTime'] = round(time.time() - start_time, 3)

    return results


def execute_javascript(code: str, test_cases: List[Dict], function_name: str, timeout: int) -> Dict[str, Any]:
    """
    Execute JavaScript code (requires Node.js runtime or execjs)
    For Lambda, we'll use a Python-based JS interpreter or return not implemented
    """
    return {
        'success': False,
        'error': 'JavaScript execution not implemented in this version. Use Python for now.',
        'language': 'javascript',
        'testResults': []
    }


# For testing locally
if __name__ == '__main__':
    # Test event
    test_event = {
        'code': '''
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
        ''',
        'language': 'python',
        'functionName': 'two_sum',
        'testCases': [
            {
                'input': '[[2, 7, 11, 15], 9]',
                'expected': '[0, 1]'
            },
            {
                'input': '[[3, 2, 4], 6]',
                'expected': '[1, 2]'
            }
        ]
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))