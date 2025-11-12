"""
Test Claude Skills directly to see raw API responses
"""

import anthropic
import json
import os

# Get API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ Set ANTHROPIC_API_KEY environment variable")
    exit(1)

# Get skill IDs
blog_skill_id = input("Enter Blog Skill ID: ").strip()
linkedin_skill_id = input("Enter LinkedIn Skill ID: ").strip()

# Test content
test_content = """
This is a test about AI search and GEO (Generative Engine Optimization).
Traditional SEO is dying. Only 8% of users click through from AI search results.
Focus on these 4 areas: shortlist battle, apiable brands, earned media, lifecycle content.
"""

client = anthropic.Anthropic(api_key=api_key)

print("\n" + "="*80)
print("TESTING BLOG SKILL")
print("="*80)

# Test blog skill
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
    container={
        "skills": [
            {"type": "custom", "skill_id": blog_skill_id, "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": f"Process this content:\n\n{test_content}"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

print(f"\nContainer ID: {response.container.id if hasattr(response, 'container') else 'None'}")
print(f"Stop Reason: {response.stop_reason}")
print(f"Content Blocks: {len(response.content)}")

print("\n--- CONTENT BLOCKS ---")
for i, block in enumerate(response.content):
    print(f"\nBlock {i+1}:")
    print(f"  Type: {block.type}")

    if hasattr(block, 'text'):
        print(f"  Text: {block.text[:200]}...")

    if block.type == 'tool_use':
        print(f"  Tool Name: {block.name if hasattr(block, 'name') else 'N/A'}")
        if hasattr(block, 'content'):
            print(f"  Tool Content Type: {type(block.content)}")
            if isinstance(block.content, list):
                for j, item in enumerate(block.content):
                    print(f"    Item {j}: {type(item)} - {item if not hasattr(item, '__dict__') else item.__dict__}")
            else:
                print(f"  Tool Content: {block.content}")

# Check for files in response
print("\n--- SEARCHING FOR FILES ---")
files_found = []

for block in response.content:
    # Check tool_use blocks
    if block.type == 'tool_use':
        if hasattr(block, 'content'):
            content = block.content
            if isinstance(content, list):
                for item in content:
                    if hasattr(item, 'type') and getattr(item, 'type', None) == 'file':
                        files_found.append({
                            'file_id': getattr(item, 'file_id', None),
                            'filename': getattr(item, 'filename', None)
                        })
                        print(f"  ✓ Found file in tool_use content: {files_found[-1]}")

    # Check for any attribute that might contain files
    if hasattr(block, '__dict__'):
        for key, value in block.__dict__.items():
            if 'file' in key.lower():
                print(f"  Found file-related attribute: {key} = {value}")

if files_found:
    print(f"\n✓ Total files found: {len(files_found)}")
    for f in files_found:
        print(f"  - {f}")

        # Try to download
        try:
            file_content = client.beta.files.download(
                file_id=f['file_id'],
                betas=["files-api-2025-04-14"]
            )
            content_text = file_content.read().decode('utf-8')
            print(f"\n  FILE CONTENT ({len(content_text)} chars):")
            print("  " + "-"*76)
            print(content_text[:500])
            print("  " + "-"*76)
        except Exception as e:
            print(f"  ❌ Error downloading file: {e}")
else:
    print("❌ No files found in response")

print("\n" + "="*80)
print("RAW RESPONSE STRUCTURE")
print("="*80)
print(json.dumps(response.model_dump(), indent=2, default=str)[:2000])
print("...")
