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
	if not (nameserver := resolve_nameserver(nameserver)):
		logging.error(f'Failed to resolve nameserver {nameserver}: {ex}')
	else:
		for ns in nameserver: # Let's try all the IP addresses for the nameserver
			try:
				xfr = dns.query.xfr(ns, tld+'.', lifetime=300)
				if xfr:
					with open(temp_file, 'w') as file:
						for msg in xfr:
							for rrset in msg.answer:
								for rdata in rrset:
									file.write(f'{rrset.name}.{tld} {rrset.ttl} {rdata}\n')
					os.rename(temp_file, filename)
					break
			except Exception as ex:
				# Most zone transfers are blocked, so we don't want to log them
				#logging.error(f'Failed to perform zone transfer from {nameserver} ({ns}) for {tld}: {ex}')
				if os.path.exists(temp_file):
					os.remove(temp_file)


def get_nameservers(target: str) -> list:
	'''
	Generate a list of the root nameservers.
	
	:param target: The target domain to get the nameservers for.
	'''
	try:
		ns_records = dns.resolver.resolve(target+'.', 'NS', lifetime=60)
		nameservers = [str(rr.target)[:-1] for rr in ns_records]
		return nameservers
	except dns.exception.Timeout:
		logging.warning(f'Timeout fetching nameservers for {target}')
	except dns.resolver.NoNameservers:
		logging.warning(f'No nameservers found for {target}')
	return []


def get_root_tlds() -> list:
	'''Get the root TLDs from a root nameservers.'''
	rndroot = [root for root in os.listdir('root') if root.endswith('.root-servers.net.txt')][0]
	if rndroot:
		tlds = sorted(set([item.split()[0][:-1] for item in open(rndroot).read().split('\n') if item and 'IN' in item and 'NS' in item]))
	else:
		logging.warning('Failed to find root nameserver list...fallback to using IANA list')
		tlds = urllib.request.urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt').read().decode('utf-8').lower().split('\n')[1:]
	random.shuffle(tlds)
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
		try:
			data += [ip.address for ip in dns.resolver.resolve(nameserver, version, lifetime=60)]
		except:
			pass
	return data



if __name__ == '__main__':
	import argparse
	import concurrent.futures

	parser = argparse.ArgumentParser(description='Mass DNS AXFR')
	parser.add_argument('-c', '--concurrency', type=int, default=30, help='maximum concurrent tasks')
	parser.add_argument('-o', '--output', default='axfrout', help='output directory')
	parser.add_argument('-t', '--timeout', type=int, default=15, help='DNS timeout (default: 15)')
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

	os.makedirs(args.output, exist_ok=True)
	dns.resolver._DEFAULT_TIMEOUT = args.timeout

	logging.info('Fetching root nameservers...')
	os.makedirs(os.path.join(args.output, 'root'), exist_ok=True)
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
		futures = [executor.submit(attempt_axfr, '', root, os.path.join(args.output, f'root/{root}.txt')) for root in get_nameservers('')]
		for future in concurrent.futures.as_completed(futures):
			try:
				future.result()
			except Exception as e:
				logging.error(f'Error in root server task: {e}')

	logging.info('Fetching root TLDs...')
	with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
		futures = [executor.submit(attempt_axfr, tld, ns, os.path.join(args.output, tld + '.txt')) for tld in get_root_tlds() for ns in get_nameservers(tld) if ns]
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
