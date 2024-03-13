import argparse
import json
import re
import sys
import time
import netlas


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
MAX_TRIES = 10

parser = argparse.ArgumentParser(
                    prog='python3 ntls_emails_by_domain',
                    description='Fetch email addresses from all Netlas.io data collections (default indices only)',
                    epilog='See https://github.com/netlas-io/ to lear more')

parser.add_argument('domain', help="Domain of interest. E.g. for foo.com you will get email1@foo.com, email2@subdomain.foo.com and so on")
parser.add_argument('-k', '--key', help="Netlas.io API key")      
parser.add_argument('-e', '--print-errors', action='store_true', help="Show parser errors. Diabled by default.")
args = parser.parse_args()

# Setting up API KEY and Netlas connection
apikey = None
if args.key != None:
    apikey = args.key                      # read from args
else:
    apikey = netlas.helpers.get_api_key()  # or from storage

# Create new connection to Netlas
netlas_connection = netlas.Netlas(api_key=apikey)

# Quering RESPONSES data collection
##   Responses collection stores emails in PROTO.contacts.email field, where PROTO could be any supported protocol.
##   "\*" is a wildcard symbol, that means "any field".
##   So Netlas will return responses of any protocol contain email ends with domain of interest.
responses_query = f"\*.contacts.email.keyword:*@{args.domain}" 

try_number = 0
while True:
    try:
        d_count = netlas_connection.count(responses_query)  # Request documents with emails count
        time.sleep(try_number)  # Waiting to avoid request throttling
        if d_count.get('count', None) and d_count['count'] > 0:
            for resp in netlas_connection.download(responses_query, size=d_count['count']):
                response = json.loads(resp.decode('utf-8')) # decode from binary stream
                prot7 = response['data']['prot7'] # Prot7 field contains protocol name: http, ftp, snmp and so on
                                                  # we need this field as a key to address email field in the response
                for email in response['data'][prot7]['contacts']['email']:
                    prep_email = email.strip().lower()
                    if EMAIL_REGEX.fullmatch(prep_email):       # This removes Netlas email parser errors
                        if prep_email.endswith(args.domain): 
                            print(prep_email)                   # Select only emails on domain of interest
                    else:
                        if (args.print_errors):                 # You can print parser errors by adding -r key
                            print('_PARSERROR: '+prep_email, file=sys.stderr)
        break
    except netlas.exception.APIError:
        try_number += 1
        if try_number >= MAX_TRIES:
            raise Exception(f"Failed to fetch data from the Responses collection after {try_number} tries")
        time.sleep(try_number*try_number)


# Quering IP WHOIS data collection

# print("#IP WHOIS:")
ip_whois_net_query = f"net.contacts.emails:*@{args.domain}"
ip_whois_related_nets_query = f"related_nets.contacts.emails:*@{args.domain}"  

try_number = 0
while True:
    try:
        d_count = netlas_connection.count(ip_whois_net_query, datatype='whois-ip') # Request documents with emails count
        time.sleep(try_number)    # Waiting to avoid request throttling
        if d_count.get('count', None) and d_count['count'] > 0:
            for resp in netlas_connection.download(ip_whois_net_query, datatype='whois-ip', size=d_count['count']):
                response = json.loads(resp.decode('utf-8')) # decode from binary stream
                for email in response['data']['net']['contacts']['emails']:
                    if email.endswith(args.domain): print(email)      # Select only emails on domain of interest
        time.sleep(try_number)    # Waiting to avoid request throttling

        d_count = netlas_connection.count(ip_whois_related_nets_query, datatype='whois-ip') # Request documents with emails count
        time.sleep(try_number)    # Waiting to avoid request throttling
        if d_count.get('count', None) and d_count['count'] > 0:
            for resp in netlas_connection.download(ip_whois_related_nets_query, datatype='whois-ip', size=d_count['count']):
                response = json.loads(resp.decode('utf-8')) # decode from binary stream
                for net in response['data']['related_nets']:
                    for email in net['contacts']['emails']:
                        if email.endswith(args.domain): 
                            print(email)    # Select only emails on domain of interest
        break
    except netlas.exception.APIError:
        try_number += 1
        if try_number >= MAX_TRIES:
            raise Exception(f"Failed to fetch data from the IP WHOIS collection after {try_number} tries")
        time.sleep(try_number*try_number)


# Quering DOMAIN WHOIS data collection
##  This query addresses to registrant, registrar, administrative and other sections of document.

# print("#DOMAIN WHOIS:")
domain_whois_query = f"\*.email.keyword:*@{args.domain}"
            
try_number = 0
while True:
    try:
        d_count = netlas_connection.count(domain_whois_query, datatype='whois-domain') # Request documents with emails count
        time.sleep(try_number)    # Waiting to avoid request throttling
        if d_count.get('count', None) and d_count['count'] > 0:
            for resp in netlas_connection.download(domain_whois_query, datatype='whois-domain', size=d_count['count']):
                response = json.loads(resp.decode('utf-8')) # decode from binary stream
                keys_of_interest = ['registrant', 'registrar', 'administrative', 'billing', 'technical']
                for key in keys_of_interest:
                    try: 
                        prep_email = response['data'][key]['email'].strip().lower()
                        if EMAIL_REGEX.fullmatch(prep_email):   # This removes Netlas email parser errors
                            if prep_email.endswith(args.domain):
                                print(prep_email)   # Select only emails on domain of interest
                        else:
                            if (args.print_errors): # You can print parser errors by adding -r key
                                print('_PARSERROR: ' + prep_email, file=sys.stderr)
                    except KeyError:
                        pass
        break
    except netlas.exception.APIError:
        try_number += 1
        if try_number >= MAX_TRIES:
            raise Exception(f"Failed to fetch data from the Domain WHOIS collection after {try_number} tries")
        time.sleep(try_number*try_number)


# Quering CERTIFICATES data collection
# print("#CERTIFICATES:")
certs_subj_query = f"certificate.subject.email_address.keyword:*@{args.domain}"
certs_issuer_query = f"certificate.issuer.email_address.keyword:*@{args.domain}"

try_number = 0
while True:
    try:
        for key, q in {'subject': certs_subj_query, 'issuer': certs_issuer_query}.items(): #iterate for make query by subject and issuer
            d_count = netlas_connection.count(q, datatype='cert') # Request documents with emails count
            time.sleep(try_number)    # Waiting to avoid request throttling
            if d_count.get('count', None) and d_count['count'] > 0:
                for resp in netlas_connection.download(q, datatype='cert', size=d_count['count']):
                    response = json.loads(resp.decode('utf-8')) # decode from binary stream
                    for email in response['data']['certificate'][key]['email_address']:
                        if email.endswith(args.domain): 
                            print(email)    # Select only emails on domain of interest
        break
    except netlas.exception.APIError:
        try_number += 1
        if try_number >= MAX_TRIES:
            raise Exception(f"Failed to fetch data from the Certificate collection after {try_number} tries")
        time.sleep(try_number*try_number)
