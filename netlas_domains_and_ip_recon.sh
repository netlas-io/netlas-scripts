#!/bin/bash

# Original variables
IP_RESULTS="ips_from_netlas.txt"
DOMAIN_RESULTS="domains_from_netlas.txt"
ip_or_cidr_regex="^[0-9]+.[0-9]+.[0-9]+.[0-9]+(/[0-9]+)?$"
domain_regex="^([a-zA-Z0-9-]*.)+([a-zA-Z]{2,}|xn--[[:alnum:]][a-zA-Z0-9-]*[[:alnum:]])$"

# Colors Variables
C_ERR="\x1b[31m" # Error
C_INF="\x1b[96m" # Info
C_END="\x1b[0m"  # Reset

[[ -z "$1" ]]&& echo -e "Usage:\n Create a file(s) with target domains and IPs.\n Then run this script with this file(s) as an argument(s)." && exit 2

# Checking if files exists
if [ -f "$IP_RESULTS" ] && [ -f "$DOMAIN_RESULTS" ]; then
  echo -e "${C_ERR}Error${C_END}: File \"$IP_RESULTS\" already exists in: $(pwd)" >&2
  echo -e "${C_ERR}Error${C_END}: File \"$DOMAIN_RESULTS\" already exists in: $(pwd)" >&2
  exit 2
fi

# Cheating files
> "$IP_RESULTS"
> "$DOMAIN_RESULTS"

for input_file in "$@"; do
#for target_ in $(cat "$input_file"); do # Original Loop using cat
  while IFS= read -r target_; do
  target_=$(echo $target_ | tr -d '\r')
    if [[ $target_ =~ $ip_or_cidr_regex ]]; then # IP or CIDR Section
      echo "$target_"
      temp_ips="$(echo "$(<$IP_RESULTS)")"; temp_domains="$(echo "$(<$DOMAIN_RESULTS)")"
      search_="$(netlas download -d domain -c 10000 -i domain,a "domain:* a:\"$target_\"")"
      new_ips="$(printf "%s\n" "$search_" | jq .data.a | tr -d "\" [],")"
      new_domains="$(printf "%s\n" "$search_" | jq -r .data.domain)"
      echo "$temp_ips" "$new_ips" | sort -uV | grep -v "^$"> $IP_RESULTS
      echo "$temp_domains" "$new_domains" | sort -u | grep -v "^$"> $DOMAIN_RESULTS
    elif [[ $target_ =~ $domain_regex ]]; then # Domain Section
      echo "$target_"
      temp_ips="$(echo "$(<$IP_RESULTS)")"; temp_domains="$(echo "$(<$DOMAIN_RESULTS)")"
      search_="$(netlas download -d domain -c 10000 -i domain,a "domain:/(.*\.)?$target_/ a:*")"
      new_ips="$(printf "%s\n" "$search_" | jq .data.a | tr -d "\" [],")"
      new_domains="$(printf "%s\n" "$search_" | jq -r .data.domain)"
      echo "$temp_ips" "$new_ips" | sort -uV | grep -v "^$"> $IP_RESULTS
      echo "$temp_domains" "$new_domains" | sort -u | grep -v "^$"> $DOMAIN_RESULTS
    else # Unrecognized target
      echo -e "${C_ERR}Error${C_END}: Unrecognized target \"$target_\" in file \"$input_file\"." >&2
    fi
  done < <(echo "$(<$input_file)") # File that "while" will read
done

echo -e "${C_INF}Found${C_END} \"$(wc -l $IP_RESULTS)\" ${C_INF}IP addresses and${C_END} \"$(wc -l $DOMAIN_RESULTS)\" ${C_INF}domains.${C_END}\n"
#rm $IP_RESULTS $DOMAIN_RESULTS

# Unsetting the variables assigned in the script
unset temp_ips temp_domains search_ new_ips new_domains IP_RESULTS DOMAIN_RESULTS ip_or_cidr_regex domain_regex C_ERR C_INF C_END
