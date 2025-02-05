import requests

# Algolia endpoint
url = "https://vfeb8tk7gw-dsn.algolia.net/1/indexes/*/queries"

# Headers for authentication
headers = {
    "x-algolia-application-id": "VFEB8TK7GW",
    "x-algolia-api-key": "7eb409217eabcd7e10083bcbeee0974a",
    "Content-Type": "application/json"
}

# Example search query (replace with relevant index and query)
payload = {
    "requests": [
        {
            "indexName": "songs",  # Replace with actual index name
            "params": "query=bohemian"
        }
    ]
}

# Making the request
response = requests.post(url, json=payload, headers=headers)

# Checking the response
if response.status_code == 200:
    data = response.json()
    for hit in data['results'][0]['hits']:
        print(f"Artist: {hit['artistITSO']}, Song: {hit['title']}, Length: {hit['length']}")

else:
    print(f"Request failed: {response.status_code}, {response.text}")
