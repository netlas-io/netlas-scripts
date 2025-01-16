# Netlas Scripts <!-- omit in toc -->

Here you can find some scripts that use [Netlas.io](https://netlas.io) search engine. Some of them may be of interest to pen testers or bug bounty  hunters, and some to enthusiasts in the field of information security. Anyone can freely use these repository contents as examples when developing their own integrations or scripts. The code is available under Creative Commons License.

<span class="hidden">[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)</span>

Do not forget to install Netlas Python SDK:

```bash
pip install netlas
```
*Note*: more about Netlas Python SDK & CLI Tool on [Netlas Docs &rarr;](https://docs.netlas.io/automation/setup/).  

- [Passive Recon Script](#passive-recon-script)
- [HTTP Responses Download](#http-responses-download)
- [Amass and Netlas Recon](#amass-and-netlas-recon)
- [Vulnerabilities Search](#vulnerabilities-search)
- [Identifying C\&C Servers Using Abuse.ch SSL Blacklist and Netlas](#identifying-cc-servers-using-abusech-ssl-blacklist-and-netlas)
- [Passive Scanner](#passive-scanner)
- [Emails by Domain](#emails-by-domain)
- [Documents by Domain](#documents-by-domain)
- [Company Tech Profile](#company-tech-profile)
- [Google Dorking Automatization](#google-dorking-automatization)

## Passive Recon Script

Use this script to passively extend an atack surface of any target. It gets a files with domains, subdomains, IP addresses and CIDRs as an input info and returns a list of domains, subdomains and IP addresses that are also related to the target. Read more about how it works in this [article](https://osintteam.blog/fast-one-shot-passive-recon-script-with-netlas-io-53a75b018fcc).

**Usage:** 

```bash
bash netlas_domains_and_ip_recon.sh domains_IPs_CIDRs.txt
```

**Output files:**

- `domains_from_netlas.txt` - a list of domains and subdomains, having at least one A-record, which was found;
- `ips_from_netlas.txt` - a list of A-records.


## HTTP Responses Download

Use this script to download web pages available in Netlas.io Responses Search tool. It gets a files with domains, subdomains and IP addresses as an input and returns a set of html files associated with these targets.

This script takes as input the files obtained as a result of the work of the previous one and loads all the pages from all objects, which will later automatically check them for vulnerabilities. Read more about how it works in this [article](https://osintteam.blog/fast-one-shot-passive-recon-script-with-netlas-io-53a75b018fcc).

**Usage:**

```bash
bash netlas_download_http_responses.sh domains_from_netlas.txt ips_from_netlas.txt
```

**Output files:**

`./responses/domain-443_page_path_!200.html` - directory with .html files, where:

- `domain` – a target host from input file;
- `443` – a port number;
- `_page_path_` – a path on the server, where this page is located (slashes replased by "_");
  in this case page downloaded from https://domain:443/page/path/
- `!200`– an HTTP server response code.


## Amass and Netlas Recon

A script that starts searching for subdomains and visualizing the results using OWASP Amass.

*Note*: don't forget to edit config.ini if you want Amass to use Netlas searches as well.

You can read more about the script and utility settings for interacting with Netlas in this [article](https://netlas.medium.com/using-owasp-amass-with-netlas-io-module-cb7308669ecd).

**Usage:**

```bash
bash amass_netlas_recon.sh
```

**Output files:**

`results/` - directory with list of subdomains in .txt format and graph in .html.


## Vulnerabilities Search

Use this script to check objects from your attack surface for vulnerabilities. Searching by vulnerability pattern is supported (you need to manually add a request to the script) or by identifier (just enter CVE).
Read more how it works in this [article](https://systemweakness.com/how-to-find-probably-vulnerable-objects-in-your-own-surface-with-netlas-io-7f3448363892).

**Usage:**

```bash
python3 netlas_cve_surface_check.py
```

**If you are searching by vulnerability pattern:** fix the sQuery line in netlas_cve_surface_check.py. You need to replace the search available there (for example, the script contains CVE-2023-36434, search for Microsoft IIS servers) with another one compiled by you or taken from our [Twitter](https://twitter.com/Netlas_io)/[Telegram](https://t.me/netlas).
Then run the script and follow the instructions in the terminal: enter the path to the file that contains your surface, then select the "Pattern" mode.

**If you are searching by CVE:** you don't need to fix anything in the script. Instead, run it and follow the instructions in the terminal: enter the path to the file, select the "CVE" mode, and enter the identifier in the format "CVE-...-...".

**Output:**

Count of probably vulnerable objects, their names.

## Identifying C&C Servers Using Abuse.ch SSL Blacklist and Netlas

This script downloads the SSL Certificate Blacklist CSV file from Abuse.ch, processes it, and queries the Netlas API to search for the most relevant internet scan data, identifying hosts that are using blacklisted SSL certificates.

Key functionalities:
1. Downloads and processes the CSV file from Abuse.ch.
2. Extracts the SHA-1 fingerprint of each SSL certificate.
3. Uses the Netlas API to search for hosts with these blacklisted certificates.
4. Outputs IP addresses and ports associated with each blacklisted certificate.

**Important:** The script makes thousands of requests to the Netlas API. A **paid Netlas account** is required to ensure sufficient API usage limits.

**Usage:**

```bash
python3 sslbl_netlas_search.py
```

**Output sample:**

```text
195.201.141.106:443     Vidar C&C (bfe0b1a3b0178779bbd0cae86e7a7bcc34558463)
116.203.14.4:443        Vidar C&C (2cab90fc1044fa9ec7706e41a418b0c427002beb)
47.242.227.169:443      CobaltStrike C&C (984ef7eab73b77e5e8d24727022aac9f12c705d9)
66.63.187.205:443       LegionLoader C&C (a728f59bb6b73af97af852879e85789775dbca0b)
188.119.66.185:443      Socks5Systemz C&C (dabed6d3b133b078ba8ef95396954a5f7e1fca0b)
91.211.249.30:443       Socks5Systemz C&C (bb1c6fb9e3bfd4bf6f784a08040b7ceba1ad0ebf)
158.247.208.174:443     Sliver C&C (1bd1fee41dac6fda021becc6ed67c26e7e7315ed)
175.178.109.66:443      CobaltStrike C&C (16b297fe392a082c653ed159106253c76c2e6b66)
122.51.7.208:443	      CobaltStrike C&C (16b297fe392a082c653ed159106253c76c2e6b66)
81.71.103.11:443	      CobaltStrike C&C (16b297fe392a082c653ed159106253c76c2e6b66)
...
```

## Passive Scanner

The script is designed to quickly and passively scan your surface using data stored by Netlas. Data is obtained from all responses of a given host, and information such as a list of vulnerabilities with their criticality, used ports, protocols, and software (Netlas tags) is displayed.

**Usage:**

```bash
python3 netlas_passive_scan.py -i file_with_hosts
```

**Additional arguments:**

`-o / --output` - output format. The default is YAML, which can be changed to JSON (`json` argument).

`-k / --key` - your API key. The default is obtained from the corresponding variable in the script code, but you can change it (input like `--key nEwKEy`).

**Output:**

Data in YAML/JSON format in the console. Can be saved to a file using output redirection (`>` or `>>`).


## Emails by Domain

This script will allow you to quickly collect all email addresses associated with a specific domain. This can help both during OSINT investigations and during pen tests to collect targets for social engineering.

*Note*: To use this script you need a paid subscription with access to contacts.

**Usage:**

```bash
python3 netlas_emails_by_domain.py domain_name
```

**Additional arguments:**

`-k/--key` - your API key. The default is obtained from the OS-specific user config dir, but you can change it (input like `--key nEwKEy`).

`-e/--print-errors` - Displaying errors during the parsing process is disabled by default.

**Output:**

A sequence of email addresses in the console can be redirected to a file using output redirection (`>` or `>>`).


## Documents by Domain

This script will allow you to quickly collect all documents which store in responses associated with specific domain. This can help both during OSINT investigations and during pen tests to collect targets for social engineering.

**Usage:**

```bash
python3 netlas_docs_by_domain.py domain_name
```

**Additional arguments:**

`-k/--key` - Your API key. The default is obtained from the OS-specific user config dir, but you can change it (input like `--key nEwKEy`).

`-e/--print-errors` - Displaying errors during the parsing process is disabled by default.

**Output:**

Links to documents in the console, can be redirected to a file using output redirection (`>` or `>>`).


## Company Tech Profile

This script allows you to semi-automatically collect information about the technological profile of a company, including the services used, providers, registrars, and so on. You can read more [here](https://netlas.medium.com/building-tech-profile-of-a-company-f2145dedad31).

**Usage:**

```bash
python3 netlas_company_tech_profile.py -i file_with_scope
```

**Additional arguments:**

`-k/--key` - Your API key. The default is obtained from the OS-specific user config dir, but you can change it (input like `--key nEwKEy`).

`-s/--services` - Path to file with services list.

**Output:**

Summary containing all the information found.

## Google Dorking Automatization

This script makes a series of Google queries using [dorks from Mike Takashi](https://github.com/TakSec/google-dorks-bug-bounty/?tab=readme-ov-file). The results obtained are collected in the form of json/yaml and output to the terminal.

**Usage**:

```bash
python3 google_dorking_automatization.py -i file_with_scope
```

**Additional arguments:**

`-o/--output` - Output format: YAML or JSON (default - YAML).

`-c/--count` - Count of results from one query.

**Output**:

Links to webpages in the console, can be redirected to a file using output redirection (> or >>).

Read more about this script in [our article](https://netlas.io/blog/google_dorking_in_cybersecurity/).
