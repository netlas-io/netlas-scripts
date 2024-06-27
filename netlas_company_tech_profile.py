import netlas
import json
import time
import re
import ipaddress
import argparse
import sys

servicesList = []
registriesList = []
registrarsList = []

geoDict = {}
tagsDict = {}
providersDict = {}

api_key = 'yourKey'
servicesFileName = ''

def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to input file')
    parser.add_argument('-k', '--key', default='None', help='Your Netlas.io API key')
    parser.add_argument('-s', '--services', default='None', help='Path to file with service names')

    return parser

def getProvider(host, netlas_connection):
    result = netlas_connection.host(host, fields=None, exclude_fields=False)
    provider = result['organization']
    cidr = result['whois']['asn']['cidr']

    if provider in providersDict:
        if cidr in providersDict[provider]:
            pass
        else:
            providersDict[provider].append(cidr)
    else:
        providersDict[provider] = []
        providersDict[provider].append(cidr)

def getResponseInfo(host, netlas_connection):
    sQuery = "host:" + host
    cnt_of_res = netlas_connection.count(query=sQuery, datatype='response')
    time.sleep(1)

    if cnt_of_res['count'] > 0:
        downloaded_query = netlas_connection.download(query=sQuery, datatype='response', size=cnt_of_res['count'])
        for query_res in downloaded_query:
            data = json.loads(query_res)['data']

            try:
                tags = data['tag']
                for tag in tags:
                    tagName = tag['fullname']
                    tagCategory = tag['category'][0]

                    if tagCategory in tagsDict:

                        if tagName in tagsDict[tagCategory]:
                            pass
                        else:
                            tagsDict[tagCategory].append(tagName)

                    else:
                        tagsDict[tagCategory] = []
                        tagsDict[tagCategory].append(tagName)
            except:
                pass

            try:
                city = data['geo']['city']
                country = data['geo']['country']

                if country in geoDict:

                    if city in geoDict[country]:
                        pass
                    else:
                        geoDict[country].append(city)

                else:
                    geoDict[country] = []
                    geoDict[country].append(city)
            except:
                pass

def whoisRegistryIP(host, netlas_connection):
    sQuery = "ip:" + host

    downloaded_query = netlas_connection.download(query=sQuery, datatype='whois-ip', size=1)

    for query_res in downloaded_query:
        data = json.loads(query_res)['data']
        registry = data['asn']['registry'].upper()

        if registry in registriesList:
            pass
        else:
            registriesList.append(registry)

def whoisRegistrarDomain(host, netlas_connection):
    sQuery = "domain:" + host

    cnt_of_res = netlas_connection.count(query=sQuery, datatype='whois-domain')
    time.sleep(1)

    if cnt_of_res['count'] > 0:
        downloaded_query = netlas_connection.download(query=sQuery, datatype='whois-domain', size=cnt_of_res['count'])
    else:
        return

    for query_res in downloaded_query:
        data = json.loads(query_res)['data']

        try:
            registrar = data['registrar']['name']

            if registrar in registrarsList:
                pass
            else:
                registrarsList.append(registrar)
        except:
            pass

def getServices(netlas_connection):
    if servicesFileName != 'None':
        servicesFile = open(servicesFileName, "r")
    else:
        return

    print("Print brand name (like an apple, microsoft etc.): ")
    name = input()

    while True:
        line = servicesFile.readline()

        if not line:
            break

        line = line.replace("\n", "")

        sQuery = "domain:" + name + ".*" + line + ".*"

        cnt_of_res = netlas_connection.count(query=sQuery, datatype='domain')
        time.sleep(1)

        if cnt_of_res['count'] > 0:
            servicesList.append(line)

def cidrPreparing(string, netlas_connection):
    lastIP = ""

    ips = ipaddress.ip_network(string)

    sQuery = "ip:["+ips[0].compressed + " TO " + ips.broadcast_address.compressed + "]"

    cnt_of_res = netlas_connection.count(query=sQuery, datatype='whois-ip')
    time.sleep(1)

    if cnt_of_res['count'] > 0:
        downloaded_query = netlas_connection.download(query=sQuery, datatype='whois-ip', size=cnt_of_res['count'])
    else:
        return

    for query_res in downloaded_query:
        data = json.loads(query_res)['data']

        ip = data['net']['start_ip']

        if ip == lastIP:
            continue
        else:
            functionHub(ip, netlas_connection)
            lastIP = ip

def functionHub(string, netlas_connection):
    reg = re.match(r'([0-9]{1,3}[\.]){3}[0-9]{1,3}', string, 0)

    if reg:
        whoisRegistryIP(string, netlas_connection)
        time.sleep(1)
        getProvider(string, netlas_connection)
    else:
        whoisRegistrarDomain(string, netlas_connection)

    time.sleep(1)
    getResponseInfo(string, netlas_connection)

def printResults():
    print("== Summary ==")

    if not tagsDict:
        pass
    else:
        print("-- Using applications --")
        for category in tagsDict.keys():
            print(category + ": ")
            print(*tagsDict[category], sep="\n")
            print("")
        print("\n")

    if not geoDict:
        pass
    else:
        print("-- Geo information --")
        for country in geoDict.keys():
            print(country)
            print(*geoDict[country], sep="\n")
            print("")
        print("\n")

    if not servicesList:
        pass
    else:
        print("-- Using services --")
        print(*servicesList, sep="\n")
        print("\n")

    if not providersDict:
        pass
    else:
        print("-- Providers and CIDRs --")
        for provider in providersDict.keys():
            print(provider)
            print(*providersDict[provider], sep=", ")
            print("")
        print("\n")

    if not registrarsList:
        pass
    else:
        print("-- Registrars --")
        print(*registrarsList, sep="\n")
        print("\n")

    if not registriesList:
        pass
    else:
        print("-- Registries --")
        print(*registriesList, sep="\n")
        print("\n")

if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    if namespace.key != 'None':
        api_key = namespace.key

    inputFileName = namespace.input
    servicesFileName = namespace.services

    netlas_connection = netlas.Netlas(api_key=api_key)

    inputFile = open(inputFileName, "r")

    while True:
        line = inputFile.readline()

        if not line:
            break

        line = line.replace("\n", "")

        if line.find("/") != -1:
            cidrPreparing(line, netlas_connection)
        else:
            functionHub(line, netlas_connection)

    inputFile.close()

    getServices(netlas_connection)

    printResults()

    wait = input()
