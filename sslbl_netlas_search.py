"""
This script downloads the SSL Certificate Blacklist CSV file from Abuse.ch, processes it,
and queries the Netlas API to search for the most relevant internet scan data, identifying
hosts that are using blacklisted SSL certificates.

Key functionalities:
1. Downloads the SSLBL CSV file from Abuse.ch.
2. Processes the CSV to extract SHA-1 fingerprints of blacklisted SSL certificates.
3. Queries the Netlas API to find URIs (not just IPs) associated with these blacklisted certificates.
4. Outputs the results, including URIs and associated ports, to a CSV file.
5. Supports command-line options -a / --apikey for providing an API key and -s/--silent to supress the output.

Important:
- The script makes thousands of requests to the Netlas API. A **paid Netlas account** is required
  to ensure sufficient API usage limits.
"""

import json
import sys
import requests
import time
import csv
import netlas
from netlas.helpers import get_api_key
from itertools import islice
from datetime import datetime
import shutil
import argparse


# URL of the SSL Certificate Blacklist CSV file
url = "https://sslbl.abuse.ch/blacklist/sslblacklist.csv"

# Configuration for retry delays
max_retries = 5  # Define number of retries in case of errors
initial_delay = 1  # Initial delay in seconds between retries
max_delay = 60     # Maximum delay in seconds

csv_chunk_size = 80 # Number of lines per request MAX=90
flush_to_file_every = 1000 # Maximum amount of lines stored in memmory, when exeeded will be flushed to the output file

# Parse command-line arguments
parser = argparse.ArgumentParser(description="A script with progress bar, silent mode, and Netlas API Key support.")
parser.add_argument("-s", "--silent", action="store_true", help="Run the script without any output.")
parser.add_argument("-a", "--apikey", type=str, help="Netlas API Key for accessing the service (optional).")
args = parser.parse_args()


# Ensure the API key is defined and Initialize Netlas connection
api_key = args.apikey
if not api_key:
    api_key = get_api_key()
    if not api_key:
        print("Error: Netlas API Key undefined!")
        exit(code=-1)
netlas_connection = netlas.Netlas(api_key)

# Define a NullWriter class for silent mode
class NullWriter:
    def write(self, _):
        pass
    def flush(self):
        pass

# Redirect stdout if silent mode is enabled
if args.silent:
    sys.stdout = NullWriter()


# Preloader function
def show_progress_bar(processed, total, start_time):
    terminal_width = shutil.get_terminal_size().columns
    reserved_space = len("Processing ") + 42 # Reserve space for percentage and numbers (e.g., " 100.00% (123/456)")
    bar_length = max(terminal_width - reserved_space, 10)  # Length of the progress bar
    progress = processed / total
    blocks = int(bar_length * progress)
    bar = "[" + "#" * blocks + "-" * (bar_length - blocks) + "]"
    percentage = progress * 100

    # Calculate elapsed time and ETC
    elapsed_time = (datetime.now() - start_time).total_seconds()
    if processed > 0:  # Avoid division by zero
        etc = elapsed_time / processed * (total - processed)
    else:
        etc = 0

    # Format ETC as mm:ss
    etc_minutes, etc_seconds = divmod(int(etc), 60)

    # Display progress bar
    print(f" \rProcessing {bar} {percentage:.2f}% ({processed}/{total}) | ETC: {etc_minutes:02}:{etc_seconds:02}", end="")



# Download the CSV file
print("Downloading and processing SSL Certificate Blacklist CSV from Abuse.ch.")
response = requests.get(url)
response.raise_for_status()  # Raise an error for HTTP issues

# Process the CSV content
blacklist_csv = response.text
csv_lines = blacklist_csv.splitlines()  # Split content into lines
reader = csv.reader(csv_lines)

processed_rows = 0
queries_to_download = {}
total_targets = 0
processed_targets = 0
used_hashes = [] # List to store used hashes and avoid redundant queries


# Iterate through each row and count how many results are there for each query
start_time = datetime.now()
while True:

    # Using chunk of N lines to make less queries
    chunk_raw = list(islice(reader, csv_chunk_size))  # Read N lines at a time
    if not chunk_raw:  # Break if no more lines
        break

    # Update the progress bar
    show_progress_bar(processed_rows, len(csv_lines), start_time)
    processed_rows += len(chunk_raw)
    
    # Process each row in the current chunk
    chunk = []
    for row in chunk_raw:
        if row[0][0] != '#' and len(row)>=3 and row[1] not in used_hashes:
            chunk.append(row)
    
    if len(chunk)==0:
        continue

    query = "certificate.fingerprint_sha1:("
    for row in chunk:
        query = query + row[1] + " OR "
        used_hashes.append(row[1])
    query = query[:-4] + ")"

    # Query the Netlas API with retries to get count for current chunk
    for attempt in range(1, max_retries + 1):
        try:
            cnt_of_res = netlas_connection.count(query=query, datatype="response")
            break
        except Exception:
            if attempt == max_retries:
                print(f"\nAll {max_retries} retries failed. Exiting.")
                raise
            time.sleep(min(initial_delay * (2 ** (attempt - 1)), max_delay))
    
    if cnt_of_res["count"] > 0:
        queries_to_download[query] = chunk # Using queries, that have results as keys, and chunks of data as values
        total_targets += cnt_of_res["count"]

# Update progress bar and output total number of targets to download
show_progress_bar(len(csv_lines), len(csv_lines), start_time)
print(f"\nFound {format(total_targets, ",")} targets to download.")


# Output CSV file
output_file_path = f"sslbl_netlas_output_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv"
output_file = open(output_file_path, mode='w', newline='', encoding='utf-8')
writer = csv.writer(output_file)
print(f"Writing output to '{output_file_path}'.")

targets = []
start_time = datetime.now()
for key, value in queries_to_download.items():      # Iterate through queries
    for attempt in range(1, max_retries + 1):       # And  make some retries for each query
        try:
            for resp in netlas_connection.download_all(key):    # Iterate through responses returned for current query
                response = json.loads(resp.decode("utf-8"))     # Decode response from binary
                target = []                                     # Each returned response is a target
                
                # Building a target from URI, threat name, sha1 and timestamp
                target.append(response.get("data", {}).get("uri"))  #  Adding URI
                sha1 = response.get("data", {}).get("certificate", {}).get("fingerprint_sha1")
                for row in value:
                    if row[1] == sha1: # Search for threat name by SHA1 in SSL Certificate Blacklist CSV part associated with this query
                        target.append(row[2]) # Adding a threat neame
                        target.append(sha1) # Adding SHA1
                target.append(response.get("data", {}).get("last_updated")) # Adding timestamp from the document
                targets.append(target)
                processed_targets += 1
                show_progress_bar(processed_targets, total_targets, start_time)
                
                # Flushing data to the file each N records
                if len(targets) >= flush_to_file_every:
                    for target in targets:
                        writer.writerow(target)
                    output_file.flush()
                    targets.clear()
            break
        except Exception:
            if attempt == max_retries:
                print(f"\nAll {max_retries} retries failed. Exiting.")
                raise
            time.sleep(min(initial_delay * (2 ** (attempt - 1)), max_delay))

# writing the last portion of lines
for target in targets:
    writer.writerow(target)
output_file.flush() 
output_file.close()

show_progress_bar(processed_targets, total_targets, start_time)
print("\nCompleted successefuly")