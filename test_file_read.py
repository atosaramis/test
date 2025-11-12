"""
Test reading files from container
"""

import anthropic
import json
import os

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ Set ANTHROPIC_API_KEY environment variable")
    exit(1)

container_id = input("Enter Container ID from failed attempt: ").strip()
file_path = input("Enter File Path (e.g., /tmp/geo_blog_post.md): ").strip()

client = anthropic.Anthropic(api_key=api_key)

print(f"\n{'='*80}")
print(f"READING FILE: {file_path}")
print(f"FROM CONTAINER: {container_id}")
print(f"{'='*80}\n")

# Try to read the file
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": container_id
    },
    messages=[
        {
            "role": "user",
            "content": f"cat {file_path}"
        }
    ],
    tools=[
        {
            "type": "code_execution_20250825",
            "name": "code_execution"
        }
    ]
)

print(f"Response Stop Reason: {response.stop_reason}")
print(f"Content Blocks: {len(response.content)}\n")

for i, block in enumerate(response.content):
    print(f"\n--- BLOCK {i+1} ---")
    print(f"Type: {block.type}")

    if hasattr(block, 'text'):
        print(f"Text: {block.text[:200]}...")

    if block.type == 'bash_code_execution_tool_result':
        print("\nBASH RESULT FOUND!")
        print(f"Has content attr: {hasattr(block, 'content')}")

        if hasattr(block, 'content'):
            content = block.content
            print(f"Content type: {type(content)}")
            print(f"Content: {content}")

            # Try different ways to extract
            if isinstance(content, dict):
                print("\nContent is dict:")
                for key, value in content.items():
                    print(f"  {key}: {type(value)} = {value if not isinstance(value, (list, dict)) else '...'}")

                if 'content' in content:
                    inner = content['content']
                    print(f"\nInner content type: {type(inner)}")
                    if isinstance(inner, list):
                        for j, item in enumerate(inner):
                            print(f"  Item {j}: {type(item)}")
                            if isinstance(item, dict):
                                print(f"    Keys: {item.keys()}")
                                if item.get('type') == 'text':
                                    print(f"    TEXT FOUND: {item.get('text', '')[:200]}...")

            elif isinstance(content, str):
                print(f"\nContent is string: {content[:500]}...")

print("\n" + "="*80)
print("RAW RESPONSE")
print("="*80)
print(json.dumps(response.model_dump(), indent=2, default=str)[:3000])
