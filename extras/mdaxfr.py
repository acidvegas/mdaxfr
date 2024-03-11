#!/usr/bin/env python
# Mass DNS AXFR - developed by acidvegas in python (https://git.acid.vegas/mdaxfr)

import logging
import os
import re
import urllib.request

try:
	import dns.rdatatype
	import dns.query
	import dns.zone
	import dns.resolver
except ImportError:
	raise SystemExit('missing required \'dnspython\' module (pip install dnspython)')


# Colours
BLUE   = '\033[1;34m'
CYAN   = '\033[1;36m'
GREEN  = '\033[1;32m'
GREY   = '\033[1;90m'
PINK   = '\033[1;95m'
PURPLE = '\033[0;35m'
RED    = '\033[1;31m'
YELLOW = '\033[1;33m'
RESET  = '\033[0m'


def attempt_axfr(domain: str, nameserver: str, nameserver_ip: str):
	'''
	Request a zone transfer from a nameserver on a domain.

	:param domain: The domain to perform the zone transfer on.
	:param nameserver: The nameserver to perform the zone transfer on.
	:param nameserver_ip: The IP address of the nameserver.
	'''

	print(f'                {YELLOW}Attempting AXFR for {CYAN}{domain}{RESET} on {PURPLE}{nameserver} {GREY}({nameserver_ip}){RESET}')

	zone = dns.zone.from_xfr(dns.query.xfr(nameserver_ip, domain))

	record_count = sum(len(node.rdatasets) for node in zone.nodes.values())

	print(f'                {GREEN}AXFR successful for {CYAN}{domain}{RESET} on {PURPLE}{nameserver} {GREY}({nameserver_ip}){RESET} - {record_count:,} records')

	with open(os.path.join('axfrout', f'{domain}_{nameserver}_{nameserver_ip}.log'), 'w') as file:
		file.write(zone.to_text())


def get_nameservers(domain: str) -> list:
	'''
	Generate a list of the root nameservers.

	:param target: The target domain to get the nameservers for.
	'''

	ns_records  = dns.resolver.resolve(domain, 'NS', lifetime=30)
	nameservers = [str(rr.target)[:-1] for rr in ns_records]

	return nameservers


def get_root_tlds(output_dir: str) -> list:
	'''
	Get the root TLDs from a root nameservers.

	:param output_dir: The output directory to use.
	'''
	rndroot = [root for root in os.listdir(output_dir) if root.endswith('.root-servers.net.txt')]
	if rndroot:
		rndroot_file = rndroot[0]  # Take the first file from the list
		tlds = sorted(set([item.split()[0][:-1] for item in open(os.path.join(root_dir, rndroot_file)).read().split('\n') if item and 'IN' in item and 'NS' in item]))
	else:
		logging.warning('Failed to find root nameserver list...fallback to using IANA list')
		tlds = urllib.request.urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt').read().decode('utf-8').lower().split('\n')[1:]
	return tlds


def get_psl_tlds() -> list:
	'''Download the Public Suffix List and return its contents.'''
	data = urllib.request.urlopen('https://publicsuffix.org/list/public_suffix_list.dat').read().decode()
	domains = []
	for line in data.split('\n'):
		if line.startswith('//') or not line:
			continue
		if '*' in line or '!' in line:
			continue
		if '.' not in line:
			continue
		domains.append(line)
	return domains


def resolve_nameserver(nameserver: str) -> list:
	'''
	Resolve a nameserver to its IP address.

	:param nameserver: The nameserver to resolve.
	'''

	data = []

	for version in ('A', 'AAAA'):
		data.extend([ip.address for ip in dns.resolver.resolve(nameserver, version, lifetime=30)])

	return data


def process_domain(domain: str):
	domain = re.sub(r'^https?://|^(www\.)|(/.*$)', '', domain)

	print(f'{PINK}Looking up nameservers for {CYAN}{domain}{RESET}')

	try:
		nameservers = get_nameservers(domain)
	except Exception as ex:
		print(f'    {RED}Error resolving nameservers for {CYAN}{domain} {GREY}({ex}){RESET}')
		return
	
	if not nameservers:
		print(f'    {GREY}No nameservers found for {CYAN}{domain}{RESET}')
		return
	
	print(f'    {BLUE}Found {len(nameservers):,} nameservers for {CYAN}{domain}{RESET}')

	for nameserver in nameservers:
		print(f'        {PINK}Looking up IP addresses for {PURPLE}{nameserver}{RESET}')

		try:
			nameserver_ips = resolve_nameserver(nameserver)
		except Exception as ex:
			print(f'            {RED}Error resolving IP addresses for {PURPLE}{nameserver} {GREY}({ex}){RESET}')
			continue

		if not nameserver_ips:
			print(f'            {GREY}No IP addresses found for {PURPLE}{nameserver}{RESET}')
			continue

		print(f'            {BLUE}Found {len(nameserver_ips):,} IP addresses for {PURPLE}{nameserver}{RESET}')

		for nameserver_ip in nameserver_ips:
			attempt_axfr(domain, nameserver, nameserver_ip)



if __name__ == '__main__':
	import argparse
	import concurrent.futures

	parser = argparse.ArgumentParser(description='Mass DNS AXFR')
	parser.add_argument('-d', '--domain', type=str,help='domain to perform AXFR on')
	parser.add_argument('-i', '--input', type=str, help='input directory')
	parser.add_argument('-t', '--tld', type=str, help='TLD to perform AXFR on')
	parser.add_argument('-p', '--psl', action='store_true', help='use the Public Suffix List')
	parser.add_argument('-c', '--concurrency', type=int, default=30, help='maximum concurrent tasks')
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

	root_dir = os.path.join(args.output, 'root')
	os.makedirs(root_dir, exist_ok=True)
	os.makedirs(args.output, exist_ok=True)
	dns.resolver._DEFAULT_TIMEOUT = args.timeout

	logging.info('Fetching root nameservers...')
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
		futures = [executor.submit(attempt_axfr, '', root, os.path.join(args.output, f'root/{root}.txt')) for root in get_nameservers('.')]
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				logging.error(f'Error in TLD task: {e}')

	logging.info('Fetching root TLDs...')
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
		futures = [executor.submit(attempt_axfr, tld, ns, os.path.join(args.output, tld + '.txt')) for tld in get_root_tlds(root_dir) for ns in get_nameservers(tld) if ns]
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				logging.error(f'Error in TLD task: {e}')

	logging.info('Fetching PSL TLDs...')
	os.makedirs(os.path.join(args.output, 'psl'), exist_ok=True)
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
		futures = [executor.submit(attempt_axfr, tld, ns, os.path.join(args.output, f'psl/{tld}.txt')) for tld in get_psl_tlds() for ns in get_nameservers(tld) if ns]
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				logging.error(f'Error in TLD task: {e}')