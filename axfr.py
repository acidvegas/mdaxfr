#!/usr/bin/env python
# Mass DNS AXFR - developed by acidvegas in python (https://git.acid.vegas/mdaxfr)

import os
import urllib.request
import logging

try:
    import dns.rdatatype
    import dns.query
    import dns.zone
    import dns.resolver
except ImportError:
    raise SystemExit('missing required \'dnspython\' module (pip install dnspython)')

def attempt_axfr(tld: str, nameserver: str, filename: str):
    '''
    Perform a DNS zone transfer on a target domain.
    
    :param target: The target domain to perform the zone transfer on.
    :param nameserver: The nameserver to perform the zone transfer on.
    :param filename: The filename to store the zone transfer results in.
    '''
    temp_file = filename + '.temp'
    try:
        nameserver = resolve_nameserver(nameserver)
    except Exception as ex:
        logging.error(f'Failed to resolve nameserver {nameserver}: {ex}')
    else:
        try:
            with open(temp_file, 'w') as file:
                xfr = dns.query.xfr(nameserver, tld+'.', timeout=15)
                for msg in xfr:
                    for rrset in msg.answer:
                        for rdata in rrset:
                            file.write(f'{rrset.name}.{tld} {rrset.ttl} {rdata}')
            os.rename(temp_file, filename)
        except Exception as ex:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            logging.error(f'Failed to perform zone transfer from {nameserver} for {tld}: {ex}')

def get_root_nameservers() -> list:
    '''Generate a list of the root nameservers.'''
    root_ns_records = dns.resolver.resolve('.', 'NS')
    root_servers = [str(rr.target)[:-1] for rr in root_ns_records]
    return root_servers

def get_root_tlds() -> list:
    '''Get the root TLDs from IANA.'''
    return urllib.request.urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt').read().decode('utf-8').lower().split('\n')[1:]

def get_tld_nameservers(tld: str) -> list:
    '''Get the nameservers for a TLD.'''    
    return [nameserver for nameserver in dns.resolver.query(tld+'.', 'NS' )]

def resolve_nameserver(nameserver: str) -> str:
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
    import argparse

    parser = argparse.ArgumentParser(description='Mass DNS AXFR')
    parser.add_argument('-r', '--root', action='store_true', help='perform zone transfer on root nameservers')
    parser.add_argument('-t', '--tld', help='perform zone transfer on a specific TLD')
    parser.add_argument('-ts', '--tlds', help='perform zone transfer on all TLDs')
    parser.add_argument('-o', '--output', default='axfrout', help='output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True) # Create output directory if it doesn't exist

    if args.root:
        try:
            for root in get_root_nameservers():
                try:
                    attempt_axfr('', root+'.root-servers.net', os.path.join(args.output, root+'-root.txt'))
                except Exception as e:
                    logging.error(f'Failed to perform zone transfer from the {root} root server: {e}')
        except Exception as e:
            logging.error(f'Failed to get root nameservers: {e}')

    if args.tlds:
        try:
            for tld in get_root_tlds():
                try:
                    for ns in get_tld_nameservers(tld):
                        try:
                            attempt_axfr(tld, ns, os.path.join(args.output, tld+'.txt'))
                        except Exception as e:
                            logging.error(f'Failed to perform zone transfer from {ns} for {tld}: {e}')
                except Exception as e:
                    logging.error(f'Failed to get nameservers for {tld}: {e}')
        except Exception as e:
            logging.error(f'Failed to get root TLDs: {e}')

    elif args.tld:
        try:
            for ns in get_tld_nameservers(args.tld):
                try:
                    attempt_axfr(args.tld, ns, os.path.join(args.output, args.tld+'.txt'))
                except Exception as e:
                    logging.error(f'Failed to perform zone transfer from {ns} for {args.tld}: {e}')
        except Exception as e:
            logging.error(f'Failed to get nameservers for {args.tld}: {e}')