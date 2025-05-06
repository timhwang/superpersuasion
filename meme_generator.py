import os
import re
import openai
from dotenv import load_dotenv
import json
import glob

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_persuasive_points(file_content):
    """Extract persuasive talking points from the document content."""
    # Look for persuasive talking points section
    persuasive_section = re.search(r'## Part 3: Persuasive Talking Points(.*?)##', file_content, re.DOTALL)
    
    if not persuasive_section:
        # Try alternative pattern if the standard one fails
        persuasive_section = re.search(r'### Persuasive Talking Points(.*?)##', file_content, re.DOTALL)
    
    if persuasive_section:
        talking_points = persuasive_section.group(1).strip()
    else:
        # If no section found, use the whole document
        talking_points = file_content
    
    # Extract key points (bullet points)
    points = re.findall(r'- \*\*(.*?)\*\*:(.*?)(?=- \*\*|\Z)', talking_points, re.DOTALL)
    
    # If no bullet points found, try to get paragraph chunks
    if not points:
        # Just get first few paragraphs for context
        points = [p.strip() for p in talking_points.split('\n\n')[:3] if p.strip()]
    
    return points

def extract_audience_from_filename(filename):
    """Attempt to determine the target audience from the filename."""
    # Remove path and extension
    base_name = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Try to extract audience from common patterns
    audience = name_without_ext.replace("input_", "").replace("output_", "").replace("-", " ")
    
    # If audience couldn't be determined clearly, look inside the file
    if audience == name_without_ext:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
                # Look for audience indicators in the content
                audience_match = re.search(r'### Target Audience: (.*?)(\n|$)', content)
                if audience_match:
                    audience = audience_match.group(1).strip()
                else:
                    audience = "general political"  # Default if nothing found
        except Exception:
            audience = "general political"  # Default if reading fails
    
    return audience

def create_meme_description(points, audience):
    """Use GPT-4o to create a meme description based on persuasive points and audience."""
    if isinstance(points[0], tuple):
        # If we have structured points with titles and descriptions
        formatted_points = []
        for title, desc in points[:3]:  # Take up to 3 main points
            clean_title = title.strip()
            clean_desc = desc.strip()
            formatted_points.append(f"- {clean_title}: {clean_desc}")
        point_text = "\n".join(formatted_points)
    else:
        # If we just have paragraphs
        point_text = "\n".join([f"- {p}" for p in points[:3]])
    
    prompt = f"""
    You are an expert political meme creator. Create a detailed description for a persuasive political meme 
    that would appeal to a {audience} audience. The meme should visually represent these key talking points:
    
    {point_text}
    
    Your response should include:
    1. A title for the meme
    2. A detailed description of the visual elements and layout
    3. Any text that should be included in the meme
    4. An explanation of why this would resonate with the {audience} audience
    
    Format your response as a structured JSON with these fields:
    - title: The meme title
    - visual_description: Detailed description of imagery
    - meme_text: Any text that would appear in the meme
    - rationale: Why this meme would be effective for the target audience
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in political messaging and meme creation. Provide detailed, creative meme concepts based on political talking points."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        meme_description = json.loads(response.choices[0].message.content)
        return meme_description
    
    except Exception as e:
        print(f"Error generating meme description: {e}")
        return None

def process_documents(input_dir=".", output_dir="Memes"):
    """Process each text file in the input directory and generate a meme description."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all .txt files in the input directory
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))
    
    if not txt_files:
        print(f"No text files found in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} text files to process")
    
    for file_path in txt_files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...")
        
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Determine the target audience from the filename or content
            audience = extract_audience_from_filename(file_path)
            print(f"Identified target audience: {audience}")
            
            # Extract persuasive points
            points = extract_persuasive_points(content)
            
            # Create meme description using GPT-4o
            meme_description = create_meme_description(points, audience)
            
            if meme_description:
                # Create safe filename from audience name
                safe_audience = audience.replace(' ', '_').lower()
                
                # Save the description to a JSON file
                output_path = os.path.join(output_dir, f"meme_{safe_audience}.json")
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    json.dump(meme_description, outfile, indent=2)
                
                # Also create a human-readable text version
                text_output_path = os.path.join(output_dir, f"meme_{safe_audience}.txt")
                with open(text_output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(f"MEME FOR {audience.upper()} AUDIENCE\n\n")
                    outfile.write(f"TITLE: {meme_description.get('title', 'N/A')}\n\n")
                    outfile.write(f"VISUAL DESCRIPTION:\n{meme_description.get('visual_description', 'N/A')}\n\n")
                    outfile.write(f"MEME TEXT:\n{meme_description.get('meme_text', 'N/A')}\n\n")
                    outfile.write(f"RATIONALE:\n{meme_description.get('rationale', 'N/A')}\n")
                
                print(f"Saved meme description to {output_path} and {text_output_path}")
            else:
                print(f"Failed to generate meme description for {file_name}")
        
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables or .env file")
        print("Please set your OpenAI API key before running this script")
        exit(1)
    
    # Get input directory from user or use default
    input_dir = input("Enter the input directory path (press Enter to use current directory): ").strip()
    if not input_dir:
        input_dir = "."
    
    # Use "Memes" as the default output directory
    output_dir = "Memes"
    
    process_documents(input_dir, output_dir)
    print(f"All documents processed! Meme descriptions saved to the '{output_dir}' folder.")