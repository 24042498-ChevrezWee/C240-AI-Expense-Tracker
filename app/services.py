import os
import json
import google.generativeai as genai
from PIL import Image

def extract_receipt_data(image_path):
    """
    Sends a receipt image to Gemini 1.5 Flash and extracts structured data.
    """
    # Load API key from environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")
    
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Open the image using Pillow
    img = Image.open(image_path)
    
    # Strict prompt instructing exactly what keys we need
    prompt = """
    Analyze this receipt image and extract the following information.
    Return ONLY a valid JSON object with these exact keys. Do not include markdown formatting:
    - "merchant_name" (string)
    - "receipt_date" (string, format YYYY-MM-DD)
    - "total_amount" (float)
    - "currency_code" (string, 3-letter ISO code like USD, EUR, CAD)
    - "category_name" (string, a short general category like 'Food', 'Transport', 'Electronics')
    
    If you cannot find a value for a specific key, use null.
    """
    
    try:
        # Enforce JSON output at the API level
        response = model.generate_content(
            [prompt, img],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the guaranteed JSON string into a Python dictionary
        data = json.loads(response.text)
        return data
        
    except json.JSONDecodeError:
        raise Exception("Failed to parse AI response into JSON.")
    except Exception as e:
        raise Exception(f"AI Processing Error: {str(e)}")