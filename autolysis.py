import os
import sys
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai
from io import StringIO
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize OpenAI with API Token and Proxy
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable is not set or accessible.")
else:
    print(f"AIPROXY_TOKEN is successfully loaded: {AIPROXY_TOKEN[:5]}...")  # Debugging output (hides most of the token)

openai.api_key = AIPROXY_TOKEN
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

def load_data(filepath):
    """Load dataset from a CSV file."""
    encodings = ['utf-8', 'ISO-8859-1', 'latin1']
    for encoding in encodings:
        try:
            print(f"Trying to load file with {encoding} encoding...")
            data = pd.read_csv(filepath, encoding=encoding)
            print(f"File loaded successfully with {encoding} encoding.")
            return data
        except UnicodeDecodeError as e:
            print(f"Error loading file with {encoding} encoding: {e}")
        except Exception as e:
            print(f"General error: {e}")
            sys.exit(1)

    # If none of the encodings work, raise an error
    print("Failed to load file with available encodings.")
    sys.exit(1)

def analyze_data(data):
    """Perform generic analysis on the dataset."""
    analysis = {
        "info": StringIO(),
        "description": data.describe(include="all").to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
    }
    data.info(buf=analysis["info"])
    numeric_data = data.select_dtypes(include=['number'])
    if not numeric_data.empty:
        analysis["correlation"] = numeric_data.corr().to_dict()
    return analysis

def generate_visualizations(data, output_dir="."):
    """Generate and save visualizations."""
    numeric_data = data.select_dtypes(include=['number'])
    visualizations = []
    if not numeric_data.empty:
        # Correlation heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
        plt.title("Correlation Heatmap")
        heatmap_path = f"{output_dir}/correlation_heatmap.png"
        plt.savefig(heatmap_path)
        plt.close()
        visualizations.append(heatmap_path)

    # Histograms for numeric data
    for column in numeric_data.columns:
        plt.figure(figsize=(8, 6))
        sns.histplot(numeric_data[column], kde=True, bins=30)
        plt.title(f"Histogram of {column}")
        hist_path = f"{output_dir}/{column}_histogram.png"
        plt.savefig(hist_path)
        plt.close()
        visualizations.append(hist_path)

    return visualizations

def get_llm_narrative(data_analysis, visualizations):
    """Use LLM to generate a Markdown narrative."""
    prompt = (
        f"The dataset contains the following columns:\n"
        f"{list(data_analysis['description'].keys())}\n\n"
        f"Here is the summary of the dataset:\n"
        f"{data_analysis['info'].getvalue()}\n\n"
        f"Missing values:\n{data_analysis['missing_values']}\n\n"
        f"Correlation analysis (if applicable):\n{data_analysis.get('correlation', {})}\n\n"
        f"Generated visualizations:\n"
        f"{', '.join(visualizations)}\n\n"
        f"Generate a story analyzing this data, describing the insights found, and suggest implications."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error with LLM request: {e}")
        sys.exit(1)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Automated data analysis and visualization.")
    parser.add_argument("filepath", type=str, help="Path to the CSV file.")
    args = parser.parse_args()

    # Debug: Check AIPROXY_TOKEN value
    print(f"Using AIPROXY_TOKEN: {AIPROXY_TOKEN[:5]}... (hidden for security)")

    # Load and analyze data
    data = load_data(args.filepath)
    analysis = analyze_data(data)

    # Generate visualizations
    visualizations = generate_visualizations(data)

    # Get LLM narrative
    narrative = get_llm_narrative(analysis, visualizations)

    # Save README.md
    with open("README.md", "w") as f:
        f.write(narrative)
    print("README.md and visualizations generated successfully.")

if __name__ == "__main__":
    main()
