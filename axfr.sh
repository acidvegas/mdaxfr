#!/bin/sh

letters="abcdefghijklm"

for letter in $(echo -n "$letters" | grep -o .); do
    dig AXFR . @$letter.root-servers.net. +nocomments +nocmd +noquestion +nostats +time=15
done

tlds=$(curl -s https://data.iana.org/TLD/tlds-alpha-by-domain.txt | tail -n +2 | tr 'A-Z' 'a-z')

for tld in $tlds; do
    namesevers=$(dig +short ns ${tld}.)
    for nameserver in $namesevers; do
        dig AXFR ${tld}. @$nameserver +nocomments +nocmd +noquestion +nostats +time=15
    done
done