#!/usr/bin/env python
# Mass DNS AXFR - developed by acidvegas in python (https://git.acid.vegas/mdaxfr)

import urllib.request

try:
    import dns.rdatatype
    import dns.query
    import dns.zone
    import dns.resolver
except ImportError:
    raise SystemExit('missing required \'dnspython\' module (pip install dnspython)')

def tld_axfr(tld: str, nameserver: str):
    '''
    Perform a DNS zone transfer on a target domain.
    
    :param target: The target domain to perform the zone transfer on.
    :param nameserver: The nameserver to perform the zone transfer on.
    '''
    xfr = dns.query.xfr(nameserver, tld+'.', timeout=15)
    for msg in xfr:
        for rrset in msg.answer:
            for rdata in rrset:
                print(f'{rrset.name}.{tld} {rrset.ttl} {rdata}')

def get_root_nameservers() -> list: # https://www.internic.net/domain/named.root
    '''Generate a list of the root nameservers.'''
    return [f'{root}.rootservers.net' for root in ('abcdefghijklm')]

def get_root_tlds() -> list:
    '''Get the root TLDs from IANA.'''
    return urllib.request.urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt').read().decode('utf-8').lower().split('\n')[1:]

def get_tld_nameservers(tld: str) -> list: # https://www.internic.net/domain/root.zone
    '''Get the nameservers for a TLD.'''    
    return [nameserver for nameserver in dns.resolver.query(tld+'.', 'NS' )]

def resolve_nameserver(nameserver: str):
    '''
    Resolve a nameserver to its IP address.
    
    :param nameserver: The nameserver to resolve.
    '''
    try:
        ip_addresses = dns.resolver.resolve(nameserver, 'A', lifetime=15)
    except:
        ip_addresses = dns.resolver.resolve(nameserver, 'AAAA', lifetime=15)

    return ip_addresses[0].address
    

if __name__ == '__main__':

    for root in get_root_nameservers():
        try:
            xfr = tld_axfr('', root+'.root-servers.net')
        except Exception as e:
            print(f"Failed to perform zone transfer from the {root} root server: {e}")

    for tld in get_root_tlds():
        try:
            for ns in get_tld_nameservers(tld):
                xfr = tld_axfr(tld, resolve_nameserver(str(ns)))
        except Exception as e:
            print(f"Failed to resolve {tld}: {e}")