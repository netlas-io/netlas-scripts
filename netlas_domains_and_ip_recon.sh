#!/bin/bash

IP_RESULTS="ips_from_netlas.txt"
DOMAIN_RESULTS="domains_from_netlas.txt"
ip_or_cidr_regex="^[0-9]+.[0-9]+.[0-9]+.[0-9]+(/[0-9]+)?$"
domain_regex="^([a-zA-Z0-9-]*.)+([a-zA-Z]{2,}|xn--[[:alnum:]][a-zA-Z0-9-]*[[:alnum:]])$"

if [ -z $1 ]; then
   echo "USAGE: Create a file(s) with target domains and IPs. Then run this script with this file(s) as an argument(s)."
   exit
fi 

if [ -f $IP_RESULTS ]; then
    echo "Error: File "$IP_RESULTS" is already exists in "$(pwd) >&2
    exit -1
fi

if [ -f $DOMAIN_RESULTS ]; then
    echo "Error: File "$DOMAIN_RESULTS" is already exists in "$(pwd) >&2
    exit -1
fi

touch $IP_RESULTS
touch $DOMAIN_RESULTS

for input_file in "$@"
do
	for target in $(cat $input_file) 
	do
        if [[ $target =~ $ip_or_cidr_regex ]]; then   #IP or CIDR section
            echo $target
            temp_ips=$(cat $IP_RESULTS); temp_domains=$(cat $DOMAIN_RESULTS)
            search=$(netlas download -d domain -c 10000 -i domain,a "domain:* a:\"$target\"")
            new_ips=$(printf "%s\n" $search | jq .data.a | tr -d "\" [],")
            new_domains=$(printf "%s\n" $search | jq -r .data.domain)
            echo "$temp_ips" "$new_ips" | sort -uV | grep -v "^$"> $IP_RESULTS
            echo "$temp_domains" "$new_domains" | sort -u | grep -v "^$"> $DOMAIN_RESULTS
        elif [[ $target =~ $domain_regex ]]; then   #Domain section
            echo $target
            temp_ips=$(cat $IP_RESULTS); temp_domains=$(cat $DOMAIN_RESULTS)
            search=$(netlas download -d domain -c 10000 -i domain,a "domain:/(.*\.)?$target/ a:*")
            new_ips=$(printf "%s\n" $search | jq .data.a | tr -d "\" [],")
            new_domains=$(printf "%s\n" $search | jq -r .data.domain)
            echo "$temp_ips" "$new_ips" | sort -uV | grep -v "^$"> $IP_RESULTS
            echo "$temp_domains" "$new_domains" | sort -u | grep -v "^$"> $DOMAIN_RESULTS
        else    #Unrecognized target
            echo 'Error: Unrecognized target '$target' in file '$input_file >&2
        fi
    done
done

echo "Found "$(cat $IP_RESULTS | wc -l)" IP addresses and "$(cat $DOMAIN_RESULTS | wc -l)" domains"
#rm $IP_RESULTS $DOMAIN_RESULTS
