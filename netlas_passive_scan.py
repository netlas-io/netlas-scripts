import netlas
import time
import re
import json
import copy
import yaml
import sys
import argparse

outputDict = {}
api_key = 'YourAPIKey'
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to input file')
    parser.add_argument('-o', '--output', default='yaml', help='Output settings. Default: YAML in console. Custom: JSON in console ("json" argument).')
    parser.add_argument('-k', '--key', default='None', help='Your Netlas.io API key')

    return parser
def portToKey(data):
    return str(data['port']) + '/' + str(data['prot4']) + ', '
def oneResponse(data):
    tagList = []
    cveList = []

    responseDict = {}

    try:
        tags = data['tag']
        for tag in tags:
            tagName = tag['name']
            tagList.append(tagName)
    except:
        pass

    try:
        cves = data['cve']
        for cve in cves:
            cveName = cve['name']
            cveScore = cve['base_score']
            cveSeverity = cve['severity']
            cveList.append(cveName + ", Score: " + cveScore + ", Severity: " + cveSeverity)
    except:
        pass

    if len(tagList) != 0:
        responseDict["Tags"] = tagList
    if len(cveList) != 0:
        responseDict["CVEs"] = cveList

    return responseDict

if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    if namespace.key != 'None':
        api_key = namespace.key

    netlas_connection = netlas.Netlas(api_key=api_key)

    res = 0

    inputFileName = namespace.input
    inputFile = open(inputFileName, "r")
    outputType = namespace.output

    while True:
        line = inputFile.readline()

        if not line:
            break

        sQuery = "host:" + line.replace("\n", "")

        cnt_of_res = netlas_connection.count(query=sQuery, datatype='response')

        if cnt_of_res['count'] != 0:
            downloaded_query = netlas_connection.download(query=sQuery, datatype='response', size=cnt_of_res['count'])

            domainDict = {}
            localOutputDict = {}

            for query_res in downloaded_query:
                items = json.loads(query_res)
                data = items['data']
                uri = data['uri']
                domainDict[portToKey(data) + uri] = oneResponse(data)

            outputDict[line.replace("\n", "")] = copy.deepcopy(domainDict)

            if outputType == "yaml":
                localOutputDict[line.replace("\n", "")] = copy.deepcopy(domainDict)
                print(yaml.dump(localOutputDict, sort_keys=False), flush=True)
            elif outputType == "json":
                localOutputDict[line.replace("\n", "")] = copy.deepcopy(domainDict)
                print(json.dumps(localOutputDict), flush=True)

        time.sleep(1)

    inputFile.close()
