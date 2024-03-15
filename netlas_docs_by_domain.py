import argparse
import json
import re
import time
import netlas
import warnings
from bs4 import BeautifulSoup

MAX_TRIES = 3
EXTENSIONS = 'txt|pdf|rtf|doc|docx|xls|xlsx|zip|rar|tar|gz|tgz|bz|7z|.bac|.old'

parser = argparse.ArgumentParser(
                    prog='python3 netlas_docs_by_domain',
                    description='Fetch responses for a domain and subdomains from Netlas.io responses collection and search for documents links.',
                    epilog='See https://github.com/netlas-io/ to lear more')

parser.add_argument('domain', help="Domain of interest. E.g. for foo.com you will get https://foo.com/doc1.pdf, https://subdomain.foo.com/arch.zip and so on")
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
responses_query = f"host:*.{args.domain} prot7:http"
warnings.filterwarnings('ignore')

try_number = 0
while True:
    try:
        d_count = netlas_connection.count(responses_query)  # Request documents with emails count
        time.sleep(try_number)  # Waiting to avoid request throttling
        if d_count.get('count', None) and d_count['count'] > 0:
            for resp in netlas_connection.download(responses_query, size=d_count['count']):
                response = json.loads(resp.decode('utf-8')) # decode from binary stream
                if response['data']['http'].get('body', None):
                    soup = BeautifulSoup(response['data']['http']['body'], 'html.parser')
                    ext_regex = r'.*\.('+EXTENSIONS+')$'
                    for link in soup.findAll('a'):
                        try:
                            href = str(link.get('href')).replace(" ", "%20")
                            if re.match(ext_regex, href):
                                # Abosolute link
                                if (href.startswith('http://') or href.startswith('https://')):
                                    print(href)
                                # Relative link with /
                                elif href.startswith('/'):    
                                    print(f"{response['data']['protocol']}://{response['data']['host']}:{response['data']['port']}{href}") 
                                # Relative link with ./
                                elif link.get('href').startswith('./'):
                                    href = href[2:]
                                    print(f"{response['data']['uri']}{href}")
                                # Relative link starts with file / directory name
                                elif re.match(r'^[\w,.-]', href):
                                    print(f"{response['data']['uri']}{href}")
                                # Wrong link
                                else:
                                    raise Exception(f"Parse error on: {href}")
                        except (NameError, AttributeError, Exception) as error:
                            if (args.print_errors): print(error)

        break
    except netlas.exception.APIError:
        try_number += 1
        if try_number >= MAX_TRIES:
            raise Exception(f"Failed to fetch data from the Responses collection after {try_number} tries")
        time.sleep(try_number*try_number)
