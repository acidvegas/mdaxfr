#!/usr/bin/env python
# Mass DNS AXFR - developed by acidvegas in python (https://git.acid.vegas/mdaxfr)

import logging
import os
import random
import urllib.request

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
        nameserver = resolve_nameserver(nameserver)[0].address # Not sure why, but we need to do this...
    except Exception as ex:
        logging.error(f'Failed to resolve nameserver {nameserver}: {ex}')
    else:
        try:
            with open(temp_file, 'w') as file:
                xfr = dns.query.xfr(nameserver, tld+'.', lifetime=300)
                for msg in xfr:
                    for rrset in msg.answer:
                        for rdata in rrset:
                            file.write(f'{rrset.name}.{tld} {rrset.ttl} {rdata}\n')
            os.rename(temp_file, filename)
        except Exception as ex:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            logging.error(f'Failed to perform zone transfer from {nameserver} for {tld}: {ex}')

def get_root_nameservers() -> list:
    '''Generate a list of the root nameservers.'''
    root_ns_records = dns.resolver.resolve('.', 'NS', lifetime=15)
    root_servers = [str(rr.target)[:-1] for rr in root_ns_records]
    return root_servers

def get_root_tlds() -> list:
    '''Get the root TLDs from IANA.'''
    tlds = urllib.request.urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt').read().decode('utf-8').lower().split('\n')[1:]
    random.shuffle(tlds)
    return tlds

def get_tld_nameservers(tld: str) -> list:
    '''Get the nameservers for a TLD.'''    
    try:
        return [str(nameserver) for nameserver in dns.resolver.resolve(tld+'.', 'NS', lifetime=60)]  # Increase lifetime
    except dns.exception.Timeout:
        logging.warning(f"Timeout fetching nameservers for TLD: {tld}")
    except dns.resolver.NoNameservers:
        logging.warning(f"No nameservers found for TLD: {tld}")
    return []

def resolve_nameserver(nameserver: str) -> str:
    '''
    Resolve a nameserver to its IP address.
    
    :param nameserver: The nameserver to resolve.
    '''
    try:
        return dns.resolver.resolve(nameserver, 'A', lifetime=60)
    except:
        return dns.resolver.resolve(nameserver, 'AAAA', lifetime=60)


if __name__ == '__main__':
    import argparse
    import concurrent.futures

    parser = argparse.ArgumentParser(description='Mass DNS AXFR')
    parser.add_argument('-c', '--concurrency', type=int, default=30, help='maximum concurrent tasks')
    parser.add_argument('-o', '--output', default='axfrout', help='output directory')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='DNS timeout (default: 30)')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    dns.resolver._DEFAULT_TIMEOUT = args.timeout

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(attempt_axfr, '', root + '.root-servers.net', os.path.join(args.output, root + '-root.txt')) for root in get_root_nameservers()]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f'Error in root server task: {e}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(attempt_axfr, tld, ns, os.path.join(args.output, tld + '.txt')) for tld in get_root_tlds() for ns in get_tld_nameservers(tld) if ns]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f'Error in TLD task: {e}')