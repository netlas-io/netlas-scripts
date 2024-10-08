from googlesearch import search
import json
import time
import argparse
import copy
import yaml

outputDict = {}

def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Path to input file')
    parser.add_argument('-o', '--output', default='yaml', help='Output settings. Default: YAML in console. Custom: JSON in console ("json" argument).')
    parser.add_argument('-c', '--count', help='Count of results from one query')

    return parser

def oneRequest(query, count):
    responseDict = {}

    # -----------
    #if you want to use rotating proxy
    #proxy = 'http://yourProxy:8080/'

    #j = search(query, advanced=True, num_results=count, proxy=proxy, ssl_verify=False)
    # -----------

    j = search(query, advanced=True, num_results=count)

    for i in j:
        responseDict[i.url] = i.description

    return responseDict

def functionHub(site, resultsCount):
    domainDict = {}

    domainDict["API Endpoints"] = copy.deepcopy(oneRequest("site:" + site + " inurl:api | site:*/rest | site:*/v1 | site:*/v2 | site:*/v3", resultsCount))
    time.sleep(10)
    domainDict["Juicy Extensions"] = copy.deepcopy(oneRequest("site:" + site + " ext:log | ext:txt | ext:conf | ext:cnf | ext:ini | ext:env | ext:sh | ext:bak | ext:backup | ext:swp | ext:old | ext:~ | ext:git | ext:svn | ext:htpasswd | ext:htaccess | ext:json", resultsCount))
    time.sleep(10)
    domainDict["Server Errors"] = copy.deepcopy(oneRequest("inurl:""error"" | intitle:""exception"" | intitle:""failure"" | intitle:""server at"" | inurl:exception | ""database error"" | ""SQL syntax"" | ""undefined index"" | ""unhandled exception"" | ""stack trace"" site:" + site, resultsCount))
    time.sleep(10)
    domainDict["XSS Prone Parameters"] = copy.deepcopy(oneRequest("inurl:q= | inurl:s= | inurl:search= | inurl:query= | inurl:keyword= | inurl:lang= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Open Redirect Prone Parameters"] = copy.deepcopy(oneRequest("inurl:url= | inurl:return= | inurl:next= | inurl:redirect= | inurl:redir= | inurl:ret= | inurl:r2= | inurl:page= inurl:& inurl:http site:" + site, resultsCount))
    time.sleep(10)
    domainDict["SQLi Prone Parameteres"] = copy.deepcopy(oneRequest("inurl:id= | inurl:pid= | inurl:category= | inurl:cat= | inurl:action= | inurl:sid= | inurl:dir= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["SSRF Prone Parameters"] = copy.deepcopy(oneRequest("inurl:http | inurl:url= | inurl:path= | inurl:dest= | inurl:html= | inurl:data= | inurl:domain=  | inurl:page= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["LFI Prone Parameters"] = copy.deepcopy(oneRequest("inurl:include | inurl:dir | inurl:detail= | inurl:file= | inurl:folder= | inurl:inc= | inurl:locate= | inurl:doc= | inurl:conf= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["RCE Prone Parameters"] = copy.deepcopy(oneRequest("inurl:cmd | inurl:exec= | inurl:query= | inurl:code= | inurl:do= | inurl:run= | inurl:read=  | inurl:ping= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["File Upload Endpoints"] = copy.deepcopy(oneRequest("site:" + site + " ""choose file""", resultsCount))
    time.sleep(10)
    domainDict["API Docs"] = copy.deepcopy(oneRequest("inurl:apidocs | inurl:api-docs | inurl:swagger | inurl:api-explorer site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Login Pages"] = copy.deepcopy(oneRequest("inurl:login | inurl:signin | intitle:login | intitle:signin | inurl:secure site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Test Environments"] = copy.deepcopy(oneRequest("inurl:test | inurl:env | inurl:dev | inurl:staging | inurl:sandbox | inurl:debug | inurl:temp | inurl:internal | inurl:demo site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Sensitive Documents"] = copy.deepcopy(oneRequest("site:" + site + " ext:txt | ext:pdf | ext:xml | ext:xls | ext:xlsx | ext:ppt | ext:pptx | ext:doc | ext:docx intext:“confidential” | intext:“Not for Public Release” | intext:”internal use only” | intext:“do not distribute”", resultsCount))
    time.sleep(10)
    domainDict["Sensitive Parameters"] = copy.deepcopy(oneRequest("inurl:email= | inurl:phone= | inurl:password= | inurl:secret= inurl:& site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Adobe Experience Manager"] = copy.deepcopy(oneRequest("inurl:/content/usergenerated | inurl:/content/dam | inurl:/jcr:content | inurl:/libs/granite | inurl:/etc/clientlibs | inurl:/content/geometrixx | inurl:/bin/wcm | inurl:/crx/de site:" + site, resultsCount))
    time.sleep(10)
    domainDict["Disclosed XSS"] = copy.deepcopy(oneRequest("site:openbugbounty.org inurl:reports intext:""" + site + """""", resultsCount))
    time.sleep(10)
    domainDict["Google Groups"] = copy.deepcopy(oneRequest("site:groups.google.com """ + site + """""", resultsCount))

    return domainDict

if __name__ == '__main__':
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])

    inputFileName = namespace.input
    outputType = namespace.output
    resultsCount = namespace.count

    inputFile = open(inputFileName, "r")

    while True:
        line = inputFile.readline()

        if not line:
            break

        site = line.replace("\n", "")

        outputDict[site] = copy.deepcopy(functionHub(site, resultsCount))

    inputFile.close()

    if outputType == "yaml":
        print(yaml.dump(outputDict, sort_keys=False), flush=True)
    elif outputType == "json":
        print(json.dumps(outputDict), flush=True)
