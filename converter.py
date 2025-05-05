import os
import argparse
import time
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def process_prompt_file(prompt_file_path):
    """
    Process a prompt file, replacing any file references with their contents.

    Args:
        prompt_file_path (str): Path to the prompt file

    Returns:
        str: The processed prompt with file references replaced
    """
    with open(prompt_file_path, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # Look for file references in the format <<FILE:filename.txt>>
    file_references = re.findall(r'<<FILE:(.*?)>>', prompt_content)

    # Replace each file reference with its contents
    for file_ref in file_references:
        file_path = file_ref.strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as ref_file:
                file_content = ref_file.read()

            # Replace the reference with the file content
            prompt_content = prompt_content.replace(f'<<FILE:{file_ref}>>', file_content)
        except Exception as e:
            print(f"Warning: Could not read referenced file '{file_path}': {e}")
            # Leave the reference tag in place if the file couldn't be read

    return prompt_content

def process_with_openai(input_file, prompt_name, model="gpt-4o"):
    """
    Process the content of a text file using OpenAI API with a specific prompt.

    Args:
        input_file (str): Path to the input text file
        prompt_name (str): Name of the prompt file in the Prompts folder
        model (str): The OpenAI model to use (default: gpt-4o)

    Returns:
        str: The result from the OpenAI API
    """
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Construct the path to the prompt file in the Prompts folder
    prompt_file = os.path.join("Prompts", prompt_name)

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        input_text = f.read()

    # Process the prompt file (resolving any file references)
    prompt = process_prompt_file(prompt_file)

    # Combine the prompt and input text
    full_prompt = f"{prompt}\n\n{input_text}"

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    # Extract and return the response text
    return response.choices[0].message.content

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process a text file with multiple prompts using OpenAI API")
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--specific_prompts", nargs="*", help="Specific prompt files to use (optional, defaults to all prompts)")

    args = parser.parse_args()

    # Ensure the Prompts folder exists
    if not os.path.exists("Prompts"):
        print("Error: 'Prompts' folder not found")
        return

    # Create the Outputs folder if it doesn't exist
    os.makedirs("Outputs", exist_ok=True)

    # Get the list of prompt files to process
    if args.specific_prompts:
        prompt_files = args.specific_prompts
        # Verify all specified prompts exist
        for prompt in prompt_files:
            if not os.path.exists(os.path.join("Prompts", prompt)):
                print(f"Error: Prompt file '{prompt}' not found in 'Prompts' folder")
                return
    else:
        # Use all prompt files in the Prompts folder
        prompt_files = [f for f in os.listdir("Prompts") if os.path.isfile(os.path.join("Prompts", f))]

    if not prompt_files:
        print("No prompt files found to process")
        return

    # Get the base name of the input file (without extension)
    input_base = os.path.splitext(os.path.basename(args.input_file))[0]

    # Process the input file with each prompt
    for prompt_file in prompt_files:
        try:
            print(f"Processing with prompt: {prompt_file}")

            # Get the result from the API
            result = process_with_openai(args.input_file, prompt_file, args.model)

            # Create the output file name
            prompt_base = os.path.splitext(prompt_file)[0]
            output_file = os.path.join("Outputs", f"{input_base}_{prompt_base}.txt")

            # Write the result to the output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"Result saved to {output_file}")

            # Add a small delay to avoid hitting API rate limits
            time.sleep(1)

        except Exception as e:
            print(f"Error processing with prompt '{prompt_file}': {e}")

    print("All processing complete!")

if __name__ == "__main__":
    main()
