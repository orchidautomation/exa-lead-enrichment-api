#!/usr/bin/env python3
import json
import re
import os
import sys

def extract_json_from_file(filepath):
    """Extract JSON object from a model output file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strategy 1: Look for specific patterns that indicate JSON response
    patterns = [
        r'```json\n([\s\S]*?)\n```',  # JSON in code blocks
        r'```\n(\{[\s\S]*?\})\n```',  # JSON in generic code blocks
        r'(\{[^{}]*"business"[^{}]*:[\s\S]*?\n\})',  # Simple JSON with business key
        r'(\{\s*"business"\s*:[\s\S]*?"metadata"\s*:[\s\S]*?\})',  # Full LocalLeadResults structure
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        if matches:
            for match in matches:
                try:
                    # Try to parse as JSON
                    json_obj = json.loads(match)
                    # Verify it has expected structure
                    if 'business' in json_obj and 'contacts' in json_obj:
                        return json_obj
                except:
                    continue
    
    # Strategy 2: Look for structured output after "LocalLeadResults:"
    results_pattern = r'LocalLeadResults:\s*\n([\s\S]*?)(?:\n\n|\Z)'
    match = re.search(results_pattern, content)
    if match:
        results_text = match.group(1)
        
        # Try to parse the structured text into JSON
        try:
            # This is a simplistic parser for the structured output
            json_obj = parse_structured_output(results_text)
            if json_obj:
                return json_obj
        except:
            pass
    
    # Strategy 3: Find the largest valid JSON object in the file
    # Look for all potential JSON objects
    potential_jsons = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
    
    valid_jsons = []
    for potential in potential_jsons:
        try:
            obj = json.loads(potential)
            if isinstance(obj, dict) and len(obj) > 2:  # At least some complexity
                valid_jsons.append((len(potential), obj))
        except:
            continue
    
    # Return the largest valid JSON
    if valid_jsons:
        valid_jsons.sort(key=lambda x: x[0], reverse=True)
        return valid_jsons[0][1]
    
    return None

def parse_structured_output(text):
    """Parse the structured text output into JSON format."""
    # This is a placeholder - would need more sophisticated parsing
    # For now, return None to try other strategies
    return None

def process_model_outputs(output_dir):
    """Process all model output files and extract JSON."""
    results = {}
    
    for filename in os.listdir(output_dir):
        if filename.endswith('_output.txt'):
            model_name = filename.replace('_output.txt', '')
            filepath = os.path.join(output_dir, filename)
            
            print(f"Processing {model_name}...")
            json_data = extract_json_from_file(filepath)
            
            if json_data:
                results[model_name] = json_data
                # Save individual JSON file
                json_filepath = os.path.join(output_dir, f"{model_name}.json")
                with open(json_filepath, 'w') as f:
                    json.dump(json_data, f, indent=2)
                print(f"  ✓ Extracted JSON for {model_name}")
            else:
                print(f"  ✗ Could not extract JSON for {model_name}")
                # Let's examine what's in the file
                with open(filepath, 'r') as f:
                    content = f.read()
                    # Look for contact names to verify we have results
                    contacts = re.findall(r'(?:Name|Contact):\s*([A-Z][a-z]+ [A-Z][a-z]+)', content)
                    if contacts:
                        print(f"    Found contacts: {', '.join(set(contacts[:5]))}")
    
    return results

if __name__ == "__main__":
    output_dir = "model_outputs"
    results = process_model_outputs(output_dir)
    
    # Save combined results
    if results:
        with open(os.path.join(output_dir, "all_models_extracted.json"), 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nExtracted JSON from {len(results)} models")
    else:
        print("\nNo JSON could be extracted from any model outputs")