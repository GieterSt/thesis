#!/usr/bin/env python3
"""
CLAUDE 3.7 SONNET LED OPTIMIZATION TEST
Testing Anthropic's latest Claude 3.7 Sonnet with improved reasoning capabilities

Key Features:
- Uses v2 prompts (same as successful DeepSeek R1 Full)
- Proper rate limiting (respects OpenRouter limits)
- Enhanced JSON parsing with fallback extraction
- Auto-integration with monitoring system
- Cost tracking and optimization
"""

import json
import requests
import time
import os
from datetime import datetime
import re

# OpenRouter API key
OPENROUTER_API_KEY = ""

class Claude37SonnetTester:
    def __init__(self):
        self.model_name = "anthropic/claude-3.7-sonnet"
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Rate limiting - Conservative for OpenRouter
        self.request_delay = 6.0  # 6 seconds between requests
        self.max_retries = 5
        self.timeout = 300  # 5 minutes timeout
        
        # Cost tracking (from OpenRouter page)
        self.input_cost_per_million = 3.0  # $3/M input tokens
        self.output_cost_per_million = 15.0  # $15/M output tokens
        
        # Test configuration
        self.test_file = "data/test_sets/test_dataset_v2_prompts_clean.json"
        self.output_file = "results/model_outputs/anthropic_claude-3.7-sonnet_results_v2_prompt.json"
        
        # Statistics
        self.stats = {
            'total_tests': 0,
            'successful_calls': 0,
            'valid_json_responses': 0,
            'rate_limited_calls': 0,
            'total_time': 0,
            'total_cost': 0.0,
            'responses': []
        }
        
    def load_test_data(self):
        """Load test dataset"""
        print(f"📁 Loading test dataset: {self.test_file}")
        
        if not os.path.exists(self.test_file):
            raise FileNotFoundError(f"Test file not found: {self.test_file}")
            
        with open(self.test_file, 'r') as f:
            data = json.load(f)
            
        print(f"✅ Loaded {len(data)} test cases")
        return data
    
    def extract_json_from_response(self, response_text):
        """Extract JSON from Claude response with multiple fallback methods"""
        if not response_text or response_text.strip() == "":
            return None
        
        # Method 1: Direct JSON parsing
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Method 2: Look for allocation_PPFD_per_hour pattern
        allocation_pattern = r'"allocation_PPFD_per_hour"\s*:\s*\{[^}]+\}'
        match = re.search(allocation_pattern, response_text)
        if match:
            try:
                json_str = "{" + match.group() + "}"
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Method 3: Look for hour_X pattern
        hour_pattern = r'\{[^}]*"hour_\d+"[^}]*\}'
        matches = re.findall(hour_pattern, response_text)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Method 4: Extract any valid JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text)
        for match in matches:
            try:
                parsed = json.loads(match)
                # Check if it looks like an allocation (has hour keys)
                if any(key.startswith('hour_') for key in parsed.keys()):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        return None
    
    def call_claude_api(self, prompt, retry_count=0):
        """Call Claude 3.7 Sonnet API with comprehensive error handling"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://led-optimization-thesis.com',
            'X-Title': 'LED Optimization Research'
        }
        
        payload = {
            'model': self.model_name,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 4096,
            'temperature': 0.1,  # Low temperature for consistent JSON output
            'top_p': 0.9
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            
            # Handle rate limiting
            if response.status_code == 429:
                self.stats['rate_limited_calls'] += 1
                if retry_count < self.max_retries:
                    wait_time = min(60, (2 ** retry_count) * 10)  # Exponential backoff, max 60s
                    print(f"  ⚠️ Rate limited. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self.call_claude_api(prompt, retry_count + 1)
                else:
                    return None, elapsed_time, "Max retries exceeded for rate limiting"
            
            # Handle other HTTP errors
            if response.status_code != 200:
                if retry_count < self.max_retries:
                    wait_time = min(30, (2 ** retry_count) * 5)
                    print(f"  ⚠️ HTTP {response.status_code}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self.call_claude_api(prompt, retry_count + 1)
                else:
                    return None, elapsed_time, f"HTTP {response.status_code}: {response.text}"
            
            result = response.json()
            
            # Extract response content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # Track usage for cost calculation
                if 'usage' in result:
                    usage = result['usage']
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                    
                    cost = (input_tokens * self.input_cost_per_million / 1_000_000 + 
                           output_tokens * self.output_cost_per_million / 1_000_000)
                    self.stats['total_cost'] += cost
                
                return content, elapsed_time, None
            else:
                return None, elapsed_time, "No content in response"
                
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                wait_time = min(60, (2 ** retry_count) * 10)
                print(f"  ⏰ Request timeout. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                return self.call_claude_api(prompt, retry_count + 1)
            else:
                elapsed_time = time.time() - start_time
                return None, elapsed_time, "Request timeout after retries"
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            return None, elapsed_time, str(e)
    
    def process_test_case(self, test_case, index):
        """Process a single test case"""
        print(f"🔄 Processing item {index + 1}/{self.stats['total_tests']}...")
        
        # Find messages in the item structure (v2 dataset format)
        messages_key = None
        for key in test_case.keys():
            if key.startswith('messages'):
                messages_key = key
                break
        
        if not messages_key or not test_case.get(messages_key):
            print(f"  ⚠️ Skipping item {index + 1} - no messages found")
            return {
                'test_case': test_case,
                'response': None,
                'parsed_allocation': None,
                'success': False,
                'error': 'No messages found in test case',
                'response_time': 0,
                'timestamp': datetime.now().isoformat()
            }

        # Extract user prompt from the messages
        user_prompt = None
        for message in test_case[messages_key]:
            if message.get("role") == "user":
                user_prompt = message.get("content")
                break

        if not user_prompt:
            print(f"  ⚠️ Skipping item {index + 1} - no user prompt found")
            return {
                'test_case': test_case,
                'response': None,
                'parsed_allocation': None,
                'success': False,
                'error': 'No user prompt found in messages',
                'response_time': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"  📤 Sending prompt to Claude 3.7 Sonnet...")
        
        # Call the API
        response_content, elapsed_time, error = self.call_claude_api(user_prompt)
        
        self.stats['total_time'] += elapsed_time
        
        if error:
            print(f"  ❌ Error: {error} ({elapsed_time:.2f}s)")
            return {
                'test_case': test_case,
                'response': None,
                'parsed_allocation': None,
                'success': False,
                'error': error,
                'response_time': elapsed_time,
                'timestamp': datetime.now().isoformat()
            }
        
        # API call successful
        self.stats['successful_calls'] += 1
        print(f"  ✅ Response received ({elapsed_time:.2f}s)")
        
        # Try to parse JSON
        parsed_allocation = self.extract_json_from_response(response_content)
        
        if parsed_allocation:
            self.stats['valid_json_responses'] += 1
            print(f"  ✅ Valid JSON response parsed")
        else:
            print(f"  ⚠️ Response is not valid JSON")
        
        result = {
            'test_case': test_case,
            'response': response_content,
            'parsed_allocation': parsed_allocation,
            'success': True,
            'error': None,
            'response_time': elapsed_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Progress update every 10 items
        if (index + 1) % 10 == 0:
            success_rate = (self.stats['successful_calls'] / (index + 1)) * 100
            json_rate = (self.stats['valid_json_responses'] / max(1, self.stats['successful_calls'])) * 100
            avg_time = self.stats['total_time'] / max(1, self.stats['successful_calls'])
            
            print(f"  📈 Progress: {index + 1}/{self.stats['total_tests']} | " +
                  f"Success: {success_rate:.1f}% | JSON: {json_rate:.1f}% | " +
                  f"Avg: {avg_time:.1f}s | Cost: ${self.stats['total_cost']:.3f}")
        
        return result
    
    def run_test(self):
        """Run the complete test suite"""
        print("🚀 CLAUDE 3.7 SONNET LED OPTIMIZATION TEST")
        print("=" * 70)
        print(f"🤖 Model: {self.model_name}")
        print(f"📁 Input: {self.test_file}")
        print(f"📝 Output: {self.output_file}")
        print(f"⏱️ Request delay: {self.request_delay}s")
        print(f"🔄 Max retries: {self.max_retries}")
        print(f"💰 Cost: ${self.input_cost_per_million}/${self.output_cost_per_million} per million tokens")
        print(f"🎯 Target: High JSON compliance with reasoning capabilities")
        
        # Load test data
        test_data = self.load_test_data()
        self.stats['total_tests'] = len(test_data)
        
        print(f"📊 Processing {len(test_data)} test cases...")
        
        # Process each test case
        for i, test_case in enumerate(test_data):
            result = self.process_test_case(test_case, i)
            self.stats['responses'].append(result)
            
            # Rate limiting delay (except for last item)
            if i < len(test_data) - 1:
                print(f"  ⏱️ Waiting {self.request_delay}s before next request...")
                time.sleep(self.request_delay)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        print(f"💾 Saving results to {self.output_file}...")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        output_data = {
            'model_info': {
                'name': self.model_name,
                'test_file': self.test_file,
                'prompt_version': 'v2',
                'test_date': datetime.now().isoformat(),
                'rate_limiting': {
                    'request_delay': self.request_delay,
                    'max_retries': self.max_retries
                }
            },
            'statistics': self.stats,
            'results': self.stats['responses']
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Results saved to: {self.output_file}")
    
    def print_summary(self):
        """Print test summary"""
        success_rate = (self.stats['successful_calls'] / self.stats['total_tests']) * 100
        json_rate = (self.stats['valid_json_responses'] / max(1, self.stats['successful_calls'])) * 100
        avg_time = self.stats['total_time'] / max(1, self.stats['successful_calls'])
        rate_limit_rate = (self.stats['rate_limited_calls'] / self.stats['total_tests']) * 100
        
        print("\n🎯 CLAUDE 3.7 SONNET TEST SUMMARY")
        print("=" * 70)
        print(f"   Total test cases: {self.stats['total_tests']}")
        print(f"   Successful API calls: {self.stats['successful_calls']}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Rate limited calls: {self.stats['rate_limited_calls']}")
        print(f"   Rate limit percentage: {rate_limit_rate:.1f}%")
        print(f"   Valid JSON responses: {self.stats['valid_json_responses']}")
        print(f"   JSON success rate: {json_rate:.1f}%")
        print(f"   Total API time: {self.stats['total_time']:.1f}s")
        print(f"   Average per successful call: {avg_time:.1f}s")
        print(f"   Total cost: ${self.stats['total_cost']:.3f}")
        print(f"   Results saved to: {self.output_file}")
        print("=" * 70)
        
        # Quality assessment
        if self.stats['valid_json_responses'] >= 50:
            print("✅ EXCELLENT! High number of valid JSON responses")
        elif self.stats['valid_json_responses'] >= 30:
            print("✅ GOOD! Sufficient valid JSON responses for analysis")
        elif self.stats['valid_json_responses'] >= 15:
            print("⚠️ MODERATE! Some valid responses, may need post-processing")
        else:
            print("❌ LOW! Few valid responses, post-processing required")
        
        print("✅ Claude 3.7 Sonnet test completed!")

if __name__ == "__main__":
    # Run the test
    tester = Claude37SonnetTester()
    tester.run_test() 