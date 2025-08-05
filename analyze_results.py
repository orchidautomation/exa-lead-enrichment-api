#!/usr/bin/env python3
import re
import json
import os

# Expected contacts from benchmark
BENCHMARK_CONTACTS = {
    "Travis Hopkins": "President/Owner",
    "Forrest Salts": "Assistant Superintendent", 
    "Joe Parker": "Superintendent",
    "Pete Parker": "Superintendent",
    "Katie Brinker": "Head Golf Professional",
    "Bo Harris": "General Manager"
}

def extract_contacts_manually(filepath, model_name):
    """Manually extract contacts from each model output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    contacts = []
    
    # Model-specific extraction patterns
    if model_name == "claude_sonnet_4":
        # Claude typically has structured output
        # Extract: "1. Trey Parker - Current Vice President"
        pattern1 = r'(?:^\d+\.\s+)?([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[-–]\s*(?:Current\s+)?([^(\n]+)'
        matches = re.findall(pattern1, content, re.MULTILINE)
        
        # Also try: "- Name: Trey Parker"
        pattern2 = r'(?:-\s+)?Name:\s+([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        matches2 = re.findall(pattern2, content)
        
        # Combine results
        for name, title in matches:
            if name and "Dead Horse" not in name:
                contacts.append({"name": name.strip(), "title": title.strip()})
        
        for name in matches2:
            if name and "Dead Horse" not in name and not any(c['name'] == name for c in contacts):
                # Find associated title
                title_match = re.search(rf'{re.escape(name)}.*?Title:\s+([^\n]+)', content, re.DOTALL)
                if title_match:
                    contacts.append({"name": name, "title": title_match.group(1).strip()})
    
    elif model_name in ["deepseek_r1", "kimi_k2", "qwen3"]:
        # These models might have different formats
        # Try multiple patterns
        patterns = [
            r'(?:Contact\s+)?Name:\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:^\d+\.\s+)?([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:,|:|-)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:Manager|Superintendent|Professional|President|Director):\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0]
                    title = match[1] if len(match) > 1 else "Unknown"
                else:
                    name = match
                    title = "Unknown"
                
                if name and "Dead Horse" not in name and not any(c['name'] == name for c in contacts):
                    contacts.append({"name": name.strip(), "title": title.strip()})
    
    elif model_name in ["gemini_flash", "gemini_pro", "glm_4_5"]:
        # Google models might format differently
        # Look for contact-like patterns
        patterns = [
            r'(?:Contact|Name|Person):\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*-\s*([A-Z][a-z]+ ?[A-Z]?[a-z]*(?:\s+[A-Z][a-z]+)*)',
            r'•\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:\(|,|-)\s*([^)\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    name = match[0]
                    title = match[1] if len(match) > 1 else "Unknown"
                else:
                    name = match
                    title = "Unknown"
                
                if name and "Dead Horse" not in name and not any(c['name'] == name for c in contacts):
                    contacts.append({"name": name.strip(), "title": title.strip()})
    
    # Also check for any benchmark names mentioned
    for benchmark_name, benchmark_title in BENCHMARK_CONTACTS.items():
        if benchmark_name in content and not any(c['name'] == benchmark_name for c in contacts):
            contacts.append({"name": benchmark_name, "title": benchmark_title})
    
    # Remove duplicates and clean up
    unique_contacts = []
    seen_names = set()
    for contact in contacts:
        if contact['name'] not in seen_names:
            seen_names.add(contact['name'])
            unique_contacts.append(contact)
    
    return unique_contacts

def analyze_all_models():
    """Analyze all model outputs and compare to benchmark."""
    output_dir = "model_outputs"
    results = {}
    
    # Process each model
    for filename in os.listdir(output_dir):
        if filename.endswith('_output.txt'):
            model_name = filename.replace('_output.txt', '')
            filepath = os.path.join(output_dir, filename)
            
            print(f"\n=== {model_name.upper()} ===")
            contacts = extract_contacts_manually(filepath, model_name)
            
            # Check against benchmark
            found_benchmark = []
            missed_benchmark = []
            extra_contacts = []
            
            for contact in contacts:
                if contact['name'] in BENCHMARK_CONTACTS:
                    found_benchmark.append(contact['name'])
                else:
                    # Check for variations (e.g., "Trey Parker" might be "Travis Parker")
                    found_match = False
                    for bench_name in BENCHMARK_CONTACTS:
                        if (contact['name'].split()[-1] == bench_name.split()[-1] or 
                            contact['name'].split()[0] == bench_name.split()[0]):
                            found_benchmark.append(bench_name)
                            found_match = True
                            break
                    if not found_match:
                        extra_contacts.append(contact)
            
            for bench_name in BENCHMARK_CONTACTS:
                if bench_name not in found_benchmark:
                    missed_benchmark.append(bench_name)
            
            results[model_name] = {
                "contacts_found": len(contacts),
                "contacts": contacts,
                "benchmark_matches": found_benchmark,
                "benchmark_missed": missed_benchmark,
                "extra_contacts": extra_contacts,
                "accuracy": len(found_benchmark) / len(BENCHMARK_CONTACTS) if BENCHMARK_CONTACTS else 0
            }
            
            print(f"Found {len(contacts)} contacts:")
            for contact in contacts:
                print(f"  - {contact['name']} ({contact['title']})")
            print(f"Benchmark matches: {len(found_benchmark)}/6")
            if missed_benchmark:
                print(f"Missed: {', '.join(missed_benchmark)}")
    
    # Save results
    with open(os.path.join(output_dir, "analysis_results.json"), 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def rank_models(results):
    """Rank models based on performance."""
    rankings = []
    
    for model, data in results.items():
        score = (
            data['accuracy'] * 100 +  # Weight accuracy heavily
            len(data['contacts']) * 5 +  # Bonus for finding more contacts
            len(data['extra_contacts']) * 2  # Small bonus for extra contacts
        )
        
        rankings.append({
            "model": model,
            "score": score,
            "accuracy": data['accuracy'],
            "total_contacts": len(data['contacts']),
            "benchmark_matches": len(data['benchmark_matches'])
        })
    
    rankings.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n\n=== MODEL RANKINGS ===")
    for i, rank in enumerate(rankings, 1):
        print(f"{i}. {rank['model']}: Score={rank['score']:.1f}, Accuracy={rank['accuracy']*100:.0f}%, Contacts={rank['total_contacts']}")
    
    return rankings

if __name__ == "__main__":
    print("Analyzing model outputs against Claude-4-Sonnet benchmark...")
    print(f"Benchmark expects 6 contacts: {', '.join(BENCHMARK_CONTACTS.keys())}")
    
    results = analyze_all_models()
    rankings = rank_models(results)
    
    # Save rankings
    with open("model_outputs/model_rankings.json", 'w') as f:
        json.dump(rankings, f, indent=2)