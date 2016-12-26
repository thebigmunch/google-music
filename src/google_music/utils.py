__all__ = ['create_mac_string', 'is_valid_mac']

import re

mac_re = re.compile(r'^([\dA-F]{2}[:]){5}([\dA-F]{2})$')


def create_mac_string(mac_int):
	mac = hex(mac_int)[2:].upper()
	pad = max(12 - len(mac), 0)

	return mac + '0' * pad


def is_valid_mac(mac_string):
	return bool(mac_re.match(mac_string))
