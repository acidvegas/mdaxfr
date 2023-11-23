# Mass DNS AXFR (Zone Transfer)

###### [Zone Transfer](https://en.wikipedia.org/wiki/DNS_zone_transfer) on all of the [Root Nameservers](https://en.wikipedia.org/wiki/Root_name_server) and [Top-level Domains](https://en.wikipedia.org/wiki/Top-level_domain) *(TLDs)*.

## Expectations & Legalities
It is expected to set *realistic* expectations when using this tool. In contemporary network configurations, AXFR requests are typically restricted, reflecting best practices in DNS security. While many nameservers now disallow AXFR requests, there may still be occasional instances where configurations permit them. Always exercise due diligence and ensure ethical use.

## Requirements
- [dnspython](https://pypi.org/project/dnspython/) *(`pip install dnspython`)*

## Usage
| Argument              | Description                                          |
| --------------------- | ---------------------------------------------------- |
| `-c`, `--concurrency` | Maximum concurrent tasks.                            |
| `-o`, `--output`      | Specify the output directory *(default is axfrout)*. |
| `-t`, `--timeout`     | DNS timeout *(default: 30)*                          |

## Information
I only wrote this to shit on **[this bozo](https://github.com/flotwig/TLDR-2/)** who took a dead project & brought it back to life by making it even worse. Rather than making a pull request to give this bloke more credit in his "tenure" as a developer, I decided to just rewrite it all from scratch so people can fork off of *clean* code instead.

This repostiory also contains a [pure POSIX version](./mdaxfr) for portability, aswell as a [script](./opennic) to do zone transfers on [OpenNIC TLDs](https://wiki.opennic.org/opennic/dot). Included also is a special [ozones](./ozones) script for fetching a few obscure zones in a non-convential manner.

## One Liner (YEAH THATS RIGHT)
Just flexing nuts here...little one-liner MASS zone AXFR, ok?

```bash
curl -s https://www.internic.net/domain/root.zone | awk '$4=="A" || $4=="AAAA" {print substr($1, 3) " " $5}' | sed 's/\.$//' | xargs -n2 sh -c 'dig AXFR "$0" "@$1"'
```

___

###### Mirrors
[acid.vegas](https://git.acid.vegas/mdaxfr) • [GitHub](https://github.com/acidvegas/mdaxfr) • [GitLab](https://gitlab.com/acidvegas/mdaxfr) • [SuperNETs](https://git.supernets.org/acidvegas/mdaxfr)
