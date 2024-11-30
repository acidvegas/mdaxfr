# Mass DNS AXFR (Zone Transfer)

![](./.screens/preview.gif)

## Information
MDAXFR allows you to perform a DNS [Zone Transfer](https://en.wikipedia.org/wiki/DNS_zone_transfer) against a target domain by resolving all of the domains nameservers to their respective A/AAAA records and making an AXFR attempt against each of the IP addresses. You can also use this tool against the [Root Nameservers](https://en.wikipedia.org/wiki/Root_name_server) and [Top-level Domains](https://en.wikipedia.org/wiki/Top-level_domain) *(TLD)*, including those in the [Public Suffix List](https://en.wikipedia.org/wiki/Public_Suffix_List) *(PSL)* aswell.

## Expectations & Legalities
It is expected to set *realistic* expectations when using this tool. In contemporary network configurations, AXFR requests are typically restricted, reflecting best practices in DNS security. While many nameservers now disallow AXFR requests, there may still be occasional instances where configurations permit them. Always exercise due diligence and ensure ethical use.

## Usage:
- AXFR a single domain
```shell
./mdaxfr ripe.net
```

- AXFR a list of domains
```shell
cat domain_list.txt | ./mdaxfr
```

.. or for parellel lookups you can use [GNU Parallel](https://www.gnu.org/software/parallel/):

```shell
parallel -a domain_list.txt -j 10 ./mdaxfr
```

- AXFR all domains in an AXFR output file
```shell
domain="ripe.net" cat axfr-ripe.log | grep -aE "\s+IN\s+NS\s+" | grep -avE "^${domain}\.\s+" | awk '{print $1}' | sort -u | sed 's/\.$//' | ./mdaxfr
```

- AXFR on all TLDs
```shell
curl -s 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt' | tail -n +2 | tr '[:upper:]' '[:lower:] | ./mdaxfr
```

- AXFR on all PSL TLDs
```shell
curl -s https://publicsuffix.org/list/public_suffix_list.dat | grep -vE '^(//|.*[*!])' | grep '\.' | awk '{print $1}' | ./mdaxfr
```

- A python version of this tool with better concurrency control is available [here](./extras/mdaxfr.py):
```shell
python ./extras/mdaxfr.py --tlds -c 30
```

## Statistics, laughs, & further thinking...
I only wrote this to shit on **[this bozo](https://github.com/flotwig/TLDR-2/)** who took a dead project & brought it back to life by making it even worse. Rather than making a pull request to give this bloke more credit in his "tenure" as a developer, I decided to just rewrite it all from scratch so people can fork off of *clean* code instead.

As of my last scan in 2023, I was only able to AXFR the zones for **8** *(.er, .fj, .gp, .mp, .mw, .ni, .sl, .xn--54b7fta0cc)* out of **1,456** root TLDs, & **114** out of **7,977** TLDs in the [Public suffix list](https://publicsuffix.org/). The [addition scripts](./extras/) in this repository provide an additional **37** zone files.

This repository also includes a GitHub Actions workflow that will automatically perform a daily scan of the root TLDs and push the results to the [axfrout/root](./axfrout/) directory.

For laughs, here is a one-liner mass zone axfr:
```bash
curl -s https://www.internic.net/domain/root.zone | awk '$4=="A" || $4=="AAAA" {print substr($1, 3) " " $5}' | sed 's/\.$//' | xargs -n2 sh -c 'dig AXFR "$0" "@$1"'
```
**Note:** Don't actually use this lol...

It is interesting to have seen this has worked on some "darknet" DNS servers...would maybe look into exploring collecting more zones for alterntive DNS routing. I am also intruiged at how much you can explore [ARPANET](https://en.wikipedia.org/wiki/ARPANET) with AXFRs...more ARPAgheddon coming soon...

___

###### Mirrors for this repository: [acid.vegas](https://git.acid.vegas/mdaxfr) • [SuperNETs](https://git.supernets.org/acidvegas/mdaxfr) • [GitHub](https://github.com/acidvegas/mdaxfr) • [GitLab](https://gitlab.com/acidvegas/mdaxfr) • [Codeberg](https://codeberg.org/acidvegas/mdaxfr)