"""
Test script to verify API is working correctly with the updated database
"""

import requests
import json
from pathlib import Path

# Constants
API_URL = "http://localhost:8000"
SEARCH_ENDPOINT = f"{API_URL}/api/v1/search"

def test_search_api():
    """Test the search API endpoint"""
    # Parameters
    query = "samsung"
    limit = 5
    
    # Make request
    try:
        print(f"Testing search API with query: '{query}'")
        response = requests.get(
            SEARCH_ENDPOINT,
            params={"q": query, "limit": limit}
        )
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search API returned {len(data['results'])} results")
            
            # Print first result
            if data["results"]:
                first_result = data["results"][0]
                print("\nFirst result:")
                print(f"- Title: {first_result['title']}")
                print(f"- Brand: {first_result['brand']}")
                print(f"- Price: ₹{first_result['price']}")
                print(f"- Rating: {first_result['rating']}")
            
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error testing search API: {e}")
        return False

if __name__ == "__main__":
    test_search_api()
