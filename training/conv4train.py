import json
from pathlib import Path

def process_data(input_file, output_file):
    # Load the input data from a file
    with open(input_file, 'r') as file:
        input_data = json.load(file)

    output_data = []

    # Process each item in the input data list
    for item in input_data:
        history = item['history']
        history = list(history.values())[0]
        response = item['response']
        action_id = item['action_id']
        
        # Properly split the history into individual messages using the ending tags before splitting by the start tag
        history = history.replace("</Opponent>", "<").replace("</You>", "<")
        messages = history.split("<")
        formatted_messages = []

        # Process each message to format according to new schema
        for msg in messages:
            if msg:
                if 'Opponent>' in msg:
                    role = "user"
                    content = msg.replace("Opponent>", "").strip()
                elif 'You>' in msg:
                    role = "assistant"
                    content = msg.replace("You>", "").strip()
                else:
                    continue  # Skip any message that does not fit the expected patterns

                if content:  # Only add if content is not empty
                    formatted_messages.append({
                        "role": role,
                        "content": content
                    })

        # Append the final response from the assistant, including the action_id
        formatted_messages.append({
            "role": "assistant",
            "content": f"[<{action_id}>]{response}"
        })

        # Add to the final output
        output_data.append({"messages": formatted_messages})

    # Write one JSON object per line (JSONL)
    with open(output_file, 'w') as file:
        for item in output_data:
            file.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    process_data(root / "backend" / "debate_results.json", root / "training" / "ft_dataset.jsonl")

