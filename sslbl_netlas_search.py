"""
This script downloads the SSL Certificate Blacklist CSV file from Abuse.ch, processes it,
and queries the Netlas API to search for the most relevant internet scan data, identifying
hosts that are using blacklisted SSL certificates.

Key functionalities:
1. Downloads and processes the CSV file from Abuse.ch.
2. Extracts the SHA-1 fingerprint of each SSL certificate.
3. Uses the Netlas API to search for hosts with these blacklisted certificates.
4. Outputs IP addresses and ports associated with each blacklisted certificate.

Important:
- The script makes thousands of requests to the Netlas API. A **paid Netlas account** is required
  to ensure sufficient API usage limits.

Requirements:
- A valid Netlas API key.
- The `requests`, `csv`, and `netlas` Python libraries installed.

Usage:
1. Replace the placeholder API key (`YOUR_API_KEY`) with your valid Netlas API key.
2. Run the script to download the CSV, process the data, and output results.

"""

import json
import netlas
import time
import csv
import requests

# Define your Netlas API key and initialize the Netlas client
api_key = "YOUR_API_KEY" 

# URL of the SSL Certificate Blacklist CSV file
url = "https://sslbl.abuse.ch/blacklist/sslblacklist.csv"

# List to store used hashes and avoid redundant queries
used_hashes = []
line_no = 0

# Configuration for retry delays
max_retries = 100  # Define number of retries in case of errors
initial_delay = 1  # Initial delay in seconds between retries
max_delay = 60     # Maximum delay in seconds

# Ensure the API key is defined
if api_key == "YOUR_API_KEY":
    print("Error: Netlas API Key undefined!")
    exit(code=-1)

# Initialize Netlas connection
netlas_connection = netlas.Netlas(api_key)

# Download the CSV file
response = requests.get(url)
response.raise_for_status()  # Raise an error for HTTP issues

# Process the CSV content
blacklist_csv = response.text
csv_lines = blacklist_csv.splitlines()  # Split content into lines
reader = csv.reader(csv_lines)

# Iterate through each row and extract relevant data
for row in reader:
    # Update progress
    progress = (line_no / len(csv_lines)) * 100
    print(f"\rProgress: {progress:.2f}%", end='', flush=True)
    line_no += 1

    # Skip comments or malformed rows
    if row[0][0] == '#':
        continue

    # Ensure the row has at least 3 columns
    if len(row) >= 3:
        # Skip already processed hashes
        if row[1] in used_hashes:
            continue

        # Define the query for the Netlas API
        query = "certificate.fingerprint_sha1:" + row[1]

        # Query the Netlas API with retries
        for attempt in range(1, max_retries + 1):
            try:
                cnt_of_res = netlas_connection.count(query=query, datatype="response")
                break
            except Exception:
                if attempt == max_retries:
                    print(f" - All {max_retries} retries failed. Exiting.")
                    raise
                time.sleep(min(initial_delay * (2 ** (attempt - 1)), max_delay))

        # Process responses if results are found
        if cnt_of_res["count"] > 0:
            print(f"\rFetching responses...", end='', flush=True)
            ips = []
            for attempt in range(1, max_retries + 1):
                try:
                    for resp in netlas_connection.download_all(query):
                        # Decode response from binary
                        response = json.loads(resp.decode("utf-8"))
                        ip = response.get("data", {}).get("ip")
                        port = response.get("data", {}).get("port")
                        if ip is not None and port is not None:
                            ip_port = f"{ip}:{port}"
                            if ip_port not in ips:
                                ips.append(ip_port)
                    break
                except Exception:
                    if attempt == max_retries:
                        print(f" - All {max_retries} retries failed. Exiting.")
                        raise
                    time.sleep(min(initial_delay * (2 ** (attempt - 1)), max_delay))

            # Output collected IP:port pairs
            print(f"\r{' ' * 40}\r", end='', flush=True)
            for n in ips:
                print(f"{n}\t{row[2]} ({row[1]})")

        # Mark the hash as used
        used_hashes.append(row[1])

print(f"\r{' ' * 40}")
