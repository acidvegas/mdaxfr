# Mass DNS AXFR (Zone Transfer)

# STILL FINISHING THIS - JUST UPLOADING PROGRESS

## Requirements
- [dnspython](https://pypi.org/project/dnspython/)

## Information
This script will attempt a [Zone Transfer](https://en.wikipedia.org/wiki/DNS_zone_transfer) on all of the [Root Nameservers](https://en.wikipedia.org/wiki/Root_name_server) and [Top-level Domains](https://en.wikipedia.org/wiki/Top-level_domain) *(TLDs)*.

Really, I only wrote this to shit on **[this idiot](https://github.com/flotwig/TLDR-2/tree/main)** who took a dead project & brought it back to life by making it even worse. Rather than making a pull request to give this bloke more credit in his "tenure" as a developer, I decided to just rewrite it all from scratch so people can fork off of *clean* code instead.

## Notice
Do not expect insane results. For the most part, AXFR's are not very commonly allowed on nameservers anymore, by you will always catch a few that are not configured to block AXFR requests...

___

###### Mirrors
[acid.vegas](https://git.acid.vegas/mdaxfr) • [GitHub](https://github.com/acidvegas/mdaxfr) • [GitLab](https://gitlab.com/acidvegas/mdaxfr) • [SuperNETs](https://git.supernets.org/acidvegas/mdaxfr)
