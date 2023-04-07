#!/bin/bash

if [ -z $1 ]; then
   echo 'USAGE: Create a file(s) with target domains and IPs. Then run this script with this file(s) as an argument(s).'
   exit
fi 

if [ ! -d "./responses" ]; then 
   mkdir "./responses"
fi


for input_file in "$@"
do
	i=1
	sp="/-\|"
   for domain in $(cat $input_file) 
   do
    	search=$(netlas download -c 1000 -i host,port,path,http.status_code,http.body "host:$domain prot7:http http.body:*")
     	for response in $(echo "$search" | jq -r '(.data.port|tostring) +";"+ .data.path +";"+ (.data.http.status_code|tostring)')
     	do
         port=$(echo $response | awk -F";" '{print $1}')
        	rpath=$(echo $response | awk -F";" '{print $2}')
        	_rpath=${rpath//\//_}
        	scode=$(echo $response | awk -F";" '{print $3}')
        	fname=$domain'-'$port$_rpath'!'$scode'.html'
        	echo "$search" | jq "select(.data.port == $port) | select(.data.http.status_code == $scode)" | jq 'select(.data.path == "'$rpath'")' | jq ".data.http.body" > "./responses/"$fname
     	done
     	printf "\b${sp:i++%${#sp}:1}"
	done
done
