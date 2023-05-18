#!/bin/bash
echo -e "\033[36m[Starting script]\033[0m"
#Making direstory for all results
mkdir -p results
touch results/domains_from_amass.txt
echo -e "\033[36m[Amass is searching subdomains]\033[0m"
amass enum -df target_root_domains.txt -o results/domains_from_amass.txt -config ~/.config/amass/config.ini
echo -e "\033[32m[End of operation]\033[0m"
#Making graph for vizualization
echo -e "\033[36m[Amass is building graph]\033[0m"
amass viz -d3 -df results/domains_from_amass.txt -o ./results/
echo -e "\033[32m[End of operation]\033[0m"
echo -e "\033[32m[End of script]\033[0m"
