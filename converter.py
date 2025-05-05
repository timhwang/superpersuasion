import os
import argparse
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def process_with_openai(input_file, output_file, prompt_name, model="gpt-4o"):
    """
    Process the content of a text file using OpenAI API and save the result to another file.

    Args:
        input_file (str): Path to the input text file
        output_file (str): Path to save the output
        prompt_name (str): Name of the prompt file in the Prompts folder
        model (str): The OpenAI model to use (default: gpt-4o)
    """
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Construct the path to the prompt file in the Prompts folder
        prompt_file = os.path.join("Prompts", prompt_name)

        # Check if the prompt file exists
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file '{prompt_name}' not found in the Prompts folder")

        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()

        # Read the prompt file
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()

        # Combine the prompt and input text
        full_prompt = f"{prompt}\n\n{input_text}"

        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        # Extract the response text
        result = response.choices[0].message.content

        # Write the result to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)

        print(f"Successfully processed {input_file} with prompt '{prompt_name}' from Prompts folder")
        print(f"Result saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process a text file using OpenAI API")
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument("output_file", help="Path to save the output")
    parser.add_argument("prompt_name", help="Name of the prompt file in the Prompts folder")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")

    args = parser.parse_args()

    # Process the file
    process_with_openai(args.input_file, args.output_file, args.prompt_name, args.model)
