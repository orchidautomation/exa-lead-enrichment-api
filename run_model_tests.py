#!/usr/bin/env python3
"""
Run all model tests and capture outputs
"""
import subprocess
import json
import time
import os
from datetime import datetime
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Define models to test
MODELS = [
    ("claude_sonnet_4", "exa_local_claude_sonnet_4.py"),
    ("kimi_k2", "exa_local_kimi_k2.py"),
    ("gemini_flash", "exa_local_gemini_flash.py"),
    ("gemini_pro", "exa_local_gemini_pro.py"),
    ("deepseek_r1", "exa_local_deepseek_r1.py"),
    ("qwen3", "exa_local_qwen3.py"),
    ("glm_4_5", "exa_local_glm_4_5.py"),
]

# Create output directory
output_dir = Path("model_outputs")
output_dir.mkdir(exist_ok=True)

# Results storage
results = {
    "test_date": datetime.now().isoformat(),
    "query": "leadership/superintendent/manager of deadhorselake.com in knoxville",
    "models": {}
}

print(f"🚀 Starting model tests at {datetime.now()}")
print(f"📁 Output directory: {output_dir}")
print(f"🔍 Query: {results['query']}\n")

for model_name, script_name in MODELS:
    print(f"\n{'='*60}")
    print(f"Testing {model_name} ({script_name})")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the script and capture output
        # Load environment variables for subprocess
        env = os.environ.copy()
        result = subprocess.run(
            ["python3", script_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=".",
            env=env
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extract JSON output from stdout
        output_lines = result.stdout.strip().split('\n')
        json_output = None
        
        # Look for JSON in the output
        for i, line in enumerate(output_lines):
            if line.strip().startswith('{'):
                # Found potential JSON start
                json_str = '\n'.join(output_lines[i:])
                try:
                    json_output = json.loads(json_str)
                    break
                except:
                    # Try to find valid JSON portion
                    for j in range(len(output_lines) - 1, i - 1, -1):
                        if output_lines[j].strip().endswith('}'):
                            json_str = '\n'.join(output_lines[i:j+1])
                            try:
                                json_output = json.loads(json_str)
                                break
                            except:
                                continue
        
        # Save raw output
        output_file = output_dir / f"{model_name}_output.txt"
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        
        # Save JSON output if found
        if json_output:
            json_file = output_dir / f"{model_name}_output.json"
            with open(json_file, 'w') as f:
                json.dump(json_output, f, indent=2)
            print(f"✅ JSON output saved to {json_file}")
        else:
            print(f"⚠️  No valid JSON found in output")
        
        # Store results
        results["models"][model_name] = {
            "status": "success" if result.returncode == 0 else "error",
            "duration_seconds": duration,
            "output_file": str(output_file),
            "json_file": str(json_file) if json_output else None,
            "error": result.stderr if result.returncode != 0 else None,
            "json_found": json_output is not None
        }
        
        print(f"✅ Completed in {duration:.2f} seconds")
        
    except subprocess.TimeoutExpired:
        results["models"][model_name] = {
            "status": "timeout",
            "duration_seconds": 300,
            "error": "Process timed out after 5 minutes"
        }
        print(f"❌ Timeout after 5 minutes")
        
    except Exception as e:
        results["models"][model_name] = {
            "status": "error",
            "error": str(e)
        }
        print(f"❌ Error: {e}")
    
    # Brief pause between models
    time.sleep(2)

# Save results summary
summary_file = output_dir / "test_summary.json"
with open(summary_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n\n{'='*60}")
print(f"✅ All tests completed!")
print(f"📊 Summary saved to {summary_file}")
print(f"{'='*60}")

# Print quick summary
print("\n📊 Quick Summary:")
for model_name in results["models"]:
    model_result = results["models"][model_name]
    status = model_result["status"]
    json_found = model_result.get("json_found", False)
    duration = model_result.get("duration_seconds", 0)
    
    status_emoji = "✅" if status == "success" else "❌"
    json_emoji = "📄" if json_found else "⚠️"
    
    print(f"{status_emoji} {model_name}: {status} {json_emoji} (JSON: {json_found}) - {duration:.2f}s")