import netlas
import time
import re

if __name__ == '__main__':
    api_key='yourAPIKey'
    netlas_connection = netlas.Netlas(api_key=api_key)

    res = 0

    print("File with your surface: ")
    fileName = input()
    inputFile = open(fileName, "r")

    print("Do you want to search by pattern or CVE?\n1 - Pattern;\n2 - CVE.")
    choose = input()

    if (int(choose) == 2):
        print("Vulnerability: ")
        vuln = input()
    else:
        print("\nI hope you have added the required request to the script\n")

    while True:
        line = inputFile.readline()

        if not line:
            break

        reg = re.match(r'([0-9]{1,3}[\.]){3}[0-9]{1,3}', line, 0)
        if reg:
            if (int(choose) == 1):
                sQuery = "http.headers.server:""Microsoft-IIS"" AND host:" + line.replace("\n", "")
            else:
                sQuery = "cve.name:" + vuln + " AND host:" + line.replace("\n", "")
        else:
            if (int(choose) == 1):
                sQuery="http.headers.server:""Microsoft-IIS"" AND host:*." + line.replace("\n","")
            else:
                sQuery="cve.name:" + vuln + " AND host:*." + line.replace("\n","")

        cnt_of_res = netlas_connection.count(query=sQuery, datatype='response')
        if cnt_of_res['count'] != 0:
            res += 1
            print(line.replace("\n","") + " is probably vulnerable")
        time.sleep(1)

        print("Now: " + str(res))

    print("\nThere are " + str(res) + " probably vulnerable objects from your surface")
