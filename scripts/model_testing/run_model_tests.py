#!/usr/bin/env python3
"""
LLM Model Testing Script for LED Optimization Evaluation

This script tests various LLM models on greenhouse LED scheduling optimization tasks
via the OpenRouter API with advanced retry logic and rate limiting for improved success rates.

Usage:
    python run_model_tests.py --model anthropic/claude-opus-4 --test-set data/test_sets/test_set_v3.json
    python run_model_tests.py --model openai/o1 --test-set data/test_sets/test_set_v2.json --start-index 20
"""

import json
import requests
import time
import argparse
import sys
import random
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

class ModelTester:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "LLM_LED_Optimization_Research",
        }
        
        # Model-specific configurations
        self.model_config = self._get_model_config()
        
        # Rate limiting configuration
        self.base_delay = self._get_base_delay()
        self.max_retries = 5
        self.backoff_factor = 2.0
        self.timeout = 180  # Default 3 minute timeout
        
    def _get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration parameters"""
        config = {}
        
        # OpenAI O1 models have specific requirements
        if "openai/o1" in self.model_name.lower():
            # O1 models don't support temperature and have lower max_tokens limits
            config["max_tokens"] = 4000  # Lower limit for O1
            # Don't set temperature for O1 models
        else:
            # Standard configuration for other models
            config["max_tokens"] = 8000
            config["temperature"] = 0.1
            
        return config
        
    def _get_base_delay(self) -> float:
        """Get base delay between requests based on model type"""
        if "openai/o1" in self.model_name.lower():
            return 60.0  # 60 seconds for O1 models (strict rate limits)
        elif "claude" in self.model_name.lower():
            return 2.0   # 2 seconds for Claude models
        else:
            return 5.0   # 5 seconds for other models
    
    def _wait_with_backoff(self, attempt: int, base_delay: Optional[float] = None) -> None:
        """Implement exponential backoff with jitter"""
        if base_delay is None:
            base_delay = self.base_delay
            
        # Exponential backoff with jitter
        delay = base_delay * (self.backoff_factor ** attempt)
        jitter = random.uniform(0.8, 1.2)  # ±20% jitter
        final_delay = delay * jitter
        
        print(f"    Waiting {final_delay:.1f} seconds before retry (attempt {attempt + 1})...")
        time.sleep(final_delay)
    
    def _check_rate_limit_error(self, response_text: str) -> bool:
        """Check if error indicates rate limiting"""
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "quota exceeded",
            "rate_limit_exceeded",
            "429",
            "throttled"
        ]
        return any(indicator in response_text.lower() for indicator in rate_limit_indicators)
    
    def _check_availability_error(self, response_text: str) -> bool:
        """Check if error indicates model unavailability"""
        availability_indicators = [
            "model unavailable",
            "service unavailable",
            "temporarily unavailable",
            "overloaded",
            "capacity",
            "503",
            "502",
            "500"
        ]
        return any(indicator in response_text.lower() for indicator in availability_indicators)
        
    def call_api(self, prompt: str) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Call the OpenRouter API with retry logic and exponential backoff
        
        Returns:
            tuple: (response_content, total_duration_seconds, error_message)
        """
        total_start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            if attempt > 0:
                self._wait_with_backoff(attempt - 1)
                
            start_time = time.time()
            
            try:
                # Prepare request payload with model-specific config
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                payload.update(self.model_config)
                
                print(f"    Attempt {attempt + 1}/{self.max_retries}: Calling API...")
                
                response = requests.post(
                    url=self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout  # Use configurable timeout
                )
                
                duration = time.time() - start_time
                
                # Handle HTTP errors
                if response.status_code != 200:
                    error_text = response.text
                    print(f"    HTTP {response.status_code}: {error_text}")
                    
                    # Check for specific error types
                    if response.status_code == 429 or self._check_rate_limit_error(error_text):
                        last_error = f"Rate limit error (HTTP {response.status_code})"
                        print(f"    Rate limit detected, will retry...")
                        continue
                        
                    elif response.status_code >= 500 or self._check_availability_error(error_text):
                        last_error = f"Server/availability error (HTTP {response.status_code})"
                        print(f"    Server error detected, will retry...")
                        continue
                        
                    else:
                        # Client error that won't be fixed by retrying
                        total_duration = time.time() - total_start_time
                        return None, total_duration, f"HTTP {response.status_code}: {error_text}"
                
                # Parse successful response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    last_error = f"Invalid JSON response: {str(e)}"
                    print(f"    JSON decode error: {e}")
                    continue
                
                # Extract content from response
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content")
                    if content:
                        total_duration = time.time() - total_start_time
                        print(f"    Success! (attempt {attempt + 1}, {duration:.2f}s)")
                        return content, total_duration, None
                    else:
                        last_error = "No response content from model"
                        print(f"    No content in response: {data}")
                        continue
                else:
                    last_error = f"Unexpected API response format: {data}"
                    print(f"    Unexpected response format: {data}")
                    continue
                    
            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                print(f"    Request timeout (attempt {attempt + 1})")
                continue
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                print(f"    Connection error: {e}")
                continue
                
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {str(e)}"
                print(f"    Request error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"    Response: {e.response.text}")
                continue
        
        # All retries exhausted
        total_duration = time.time() - total_start_time
        print(f"    All {self.max_retries} attempts failed. Last error: {last_error}")
        return None, total_duration, last_error or "Unknown error after all retries"
    
    def clean_json_response(self, response_text: str) -> str:
        """Clean markdown code fences and whitespace from response"""
        if not response_text:
            return response_text
            
        cleaned = response_text.strip()
        
        # Remove markdown code fences
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        return cleaned.strip()
    
    def parse_json_response(self, response_text: str) -> tuple[dict, str]:
        """
        Parse JSON response, returning parsed data and any error message
        
        Returns:
            tuple: (parsed_json_or_raw_text, error_message)
        """
        if not response_text:
            return None, "No response content from model"
            
        cleaned = self.clean_json_response(response_text)
        
        try:
            return json.loads(cleaned), None
        except json.JSONDecodeError as e:
            return response_text, f"Invalid JSON: {str(e)}"

def load_test_set(file_path: str) -> list:
    """Load test set from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Test set file '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in test set file '{file_path}'.")
        sys.exit(1)

def extract_prompts_and_ground_truth(test_data: list) -> list:
    """Extract user prompts and original assistant responses from test data"""
    processed_items = []
    
    for i, item in enumerate(test_data):
        if not item.get("messages") or len(item["messages"]) < 2:
            print(f"Warning: Skipping item {i+1} due to unexpected format")
            continue
            
        user_prompt = None
        original_response = None
        
        for message in item["messages"]:
            if message.get("role") == "user":
                user_prompt = message.get("content")
            elif message.get("role") == "assistant":
                original_response = message.get("content")
        
        if not user_prompt:
            print(f"Warning: No user prompt found in item {i+1}")
            continue
            
        # Parse original assistant response if it's JSON
        original_json = None
        try:
            if original_response:
                original_json = json.loads(original_response)
        except json.JSONDecodeError:
            original_json = original_response
            
        processed_items.append({
            "index": i + 1,
            "user_prompt": user_prompt,
            "original_response": original_json
        })
    
    return processed_items

def generate_output_filename(model_name: str, test_set_path: str) -> str:
    """Generate output filename based on model name and test set version"""
    sanitized_model = model_name.replace("/", "_").replace(":", "_")
    
    # Detect test set version
    version_suffix = ""
    if "_v2.json" in test_set_path:
        version_suffix = "_v2_prompt"
    elif "_v3.json" in test_set_path:
        version_suffix = "_v3_prompt"
    elif "_v1.json" in test_set_path:
        version_suffix = "_v1_prompt"
    
    return f"results/model_outputs/{sanitized_model}_results{version_suffix}.json"

def main():
    parser = argparse.ArgumentParser(description='Test LLM models on LED optimization tasks with advanced retry logic')
    parser.add_argument('--model', required=True, help='Model name (e.g., anthropic/claude-opus-4, openai/o1)')
    parser.add_argument('--test-set', required=True, help='Path to test set JSON file')
    parser.add_argument('--api-key', help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--start-index', type=int, default=1, help='Start processing from this item index')
    parser.add_argument('--output', help='Output file path (auto-generated if not specified)')
    
    # Retry and rate limiting options
    parser.add_argument('--max-retries', type=int, default=5, help='Maximum retry attempts per API call (default: 5)')
    parser.add_argument('--base-delay', type=float, help='Base delay between requests in seconds (auto-detected if not specified)')
    parser.add_argument('--backoff-factor', type=float, default=2.0, help='Exponential backoff multiplier (default: 2.0)')
    parser.add_argument('--timeout', type=int, default=180, help='API request timeout in seconds (default: 180)')
    
    # Model configuration options
    parser.add_argument('--max-tokens', type=int, help='Override max_tokens parameter (auto-detected if not specified)')
    parser.add_argument('--temperature', type=float, help='Override temperature parameter (auto-detected if not specified)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key
    if not api_key:
        import os
        api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("Error: OpenRouter API key required. Use --api-key or set OPENROUTER_API_KEY environment variable.")
        sys.exit(1)
    
    # Load test data
    print(f"Loading test set from: {args.test_set}")
    test_data = load_test_set(args.test_set)
    processed_items = extract_prompts_and_ground_truth(test_data)
    
    print(f"Found {len(processed_items)} valid test items")
    
    # Determine output file
    output_file = args.output or generate_output_filename(args.model, args.test_set)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize model tester with custom parameters
    tester = ModelTester(api_key, args.model)
    
    # Override configuration if specified
    if args.max_retries:
        tester.max_retries = args.max_retries
    if args.base_delay is not None:
        tester.base_delay = args.base_delay
    if args.backoff_factor:
        tester.backoff_factor = args.backoff_factor
    if args.timeout:
        tester.timeout = args.timeout
    if args.max_tokens:
        tester.model_config["max_tokens"] = args.max_tokens
    if args.temperature is not None:
        tester.model_config["temperature"] = args.temperature
    
    print(f"Configuration:")
    print(f"  Model: {args.model}")
    print(f"  Max retries: {tester.max_retries}")
    print(f"  Base delay: {tester.base_delay} seconds")
    print(f"  Backoff factor: {tester.backoff_factor}")
    print(f"  Timeout: {getattr(tester, 'timeout', 180)} seconds")
    print(f"  Model config: {tester.model_config}")
    
    # Process items
    results = []
    start_index = args.start_index - 1  # Convert to 0-based indexing
    items_to_process = processed_items[start_index:]
    
    print(f"Starting evaluation of model '{args.model}' on {len(items_to_process)} items...")
    print(f"Results will be saved to: {output_file}")
    print(f"Base delay between requests: {tester.base_delay} seconds")
    print(f"Max retries per request: {tester.max_retries}")
    
    total_api_time = 0
    successful_calls = 0
    failed_calls = 0
    script_start = time.time()
    
    for i, item in enumerate(items_to_process):
        current_index = start_index + i + 1
        print(f"\nProcessing item {current_index}/{len(processed_items)} ({i+1}/{len(items_to_process)})...")
        
        # Add base delay between requests (not for first request)
        if i > 0:
            print(f"  Waiting {tester.base_delay} seconds between requests...")
            time.sleep(tester.base_delay)
        
        # Call model API with retry logic
        response_text, duration, api_error = tester.call_api(item["user_prompt"])
        total_api_time += duration
        
        if response_text is not None:
            successful_calls += 1
            print(f"  ✓ API call successful (total time: {duration:.2f} seconds)")
        else:
            failed_calls += 1
            print(f"  ✗ API call failed after all retries: {api_error}")
        
        # Parse response
        parsed_response, parse_error = tester.parse_json_response(response_text)
        
        if parse_error and response_text is not None:
            print(f"  WARNING: {parse_error}")
            if "Invalid JSON" in parse_error:
                print(f"  Raw response preview: {response_text[:200]}...")
        
        # Store result with comprehensive information
        result = {
            "item_index": current_index,
            "original_user_prompt": item["user_prompt"],
            "original_assistant_response": item["original_response"],
            "openrouter_model_response": parsed_response,
            "api_call_duration_seconds": duration,
            "api_success": response_text is not None
        }
        
        # Add error information if present
        if api_error:
            result["error_message"] = api_error
        if parse_error:
            result["parse_error"] = parse_error
            
        results.append(result)
        
        # Save progress periodically (every 10 items or on failures)
        if (i + 1) % 10 == 0 or response_text is None:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"  Progress saved ({len(results)} items)")
            except IOError as e:
                print(f"  Warning: Could not save progress: {e}")
        
        # Progress summary
        success_rate = (successful_calls / (i + 1)) * 100
        print(f"  Progress: {successful_calls} successes, {failed_calls} failures ({success_rate:.1f}% success rate)")
    
    # Save final results
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_file}")
    except IOError as e:
        print(f"Error saving final results: {e}")
        sys.exit(1)
    
    # Print comprehensive summary
    script_duration = time.time() - script_start
    avg_api_time = total_api_time / len(results) if results else 0
    avg_successful_api_time = total_api_time / successful_calls if successful_calls > 0 else 0
    success_rate = (successful_calls / len(results)) * 100 if results else 0
    
    print(f"\n=== Evaluation Summary ===")
    print(f"Model: {args.model}")
    print(f"Test set: {args.test_set}")
    print(f"Items processed: {len(results)}/{len(processed_items)}")
    print(f"API Success Rate: {successful_calls}/{len(results)} ({success_rate:.1f}%)")
    print(f"API Failures: {failed_calls}")
    print(f"Total execution time: {script_duration:.2f} seconds")
    print(f"Total API time: {total_api_time:.2f} seconds")
    print(f"Average time per item: {avg_api_time:.2f} seconds")
    print(f"Average time per successful API call: {avg_successful_api_time:.2f} seconds")
    
    if failed_calls > 0:
        print(f"\n⚠ Warning: {failed_calls} API calls failed despite retry logic.")
        print("Consider:")
        print("- Checking API key and model availability")
        print("- Running during off-peak hours")
        print("- Using --start-index to resume from failed items")

if __name__ == "__main__":
    main() 