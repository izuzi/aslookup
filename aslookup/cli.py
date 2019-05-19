'CLI module'

import sys
import logging
import argparse
from time import sleep

from .exceptions import AddressFormatError, LookupError


LOGLEVEL_CHOICES = ['debug', 'info', 'warning', 'error', 'critical']

def main():
    description = ('Client to return autonomous system information for '
                   'IPv4 addresses')
    epilog = ('One or more IP addresses may be passed as arguments on the '
              'command line. A list of IP addresses (newline-separated) may '
              'also be passed on standard input.')
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('-s', '--service', choices=['shadowserver', 'cymru'],
                        default='shadowserver',
                        help='service to query (default: %(default)s)')
    parser.add_argument('-H', '--header', action='store_true',
                        help='print descriptive header before output')
    parser.add_argument('-p', '--pause', action='store_true',
                        help='pause for one second between each query on address list input')
    parser.add_argument('-r', '--raw', action='store_true',
                        help='display internal ASData object showing the value '
                             'of each known field in the AS data')
    parser.add_argument('-l', '--loglevel', choices=LOGLEVEL_CHOICES,
                        default='warning',
                        help='set output verbosity level '
                             '(default: %(default)s)')
    parser.add_argument('-V', '--version', action='store_true',
                        help='display software version')
    parser.add_argument('address', nargs='*', help='IPv4 address(es) on which to perform AS lookup')
    args = parser.parse_args()

    logging.getLogger().setLevel(args.loglevel.upper())

    if args.version:
        from . import get_version
        from os import linesep
        parser.exit(0, get_version() + linesep)

    # Loaded from here so that root logger configured with level first
    from .lookup import get_as_data

    # Print header lines if specified
    if args.header:
        print('-' * 50)
        print('%-15s  %s' % ('IP Address', 'AS Information'))
        print('-' * 50)

    # Process addresses given as parameters or fed on stdin.
    # - Input as parameters: In this mode, invalid IP addresses result in
    #   script exiting with an error. Non-routable addresses result in
    #   message to stderr.
    # - Input on stdin: In this mode, invalid IP addresses result in script
    #   proceeding without exiting, in order to make it so that address lists
    #   process without interruption. All issues are output on stderr.
    in_src = args.address if args.address else sys.stdin
    for addr in in_src:
        addr = addr.strip()
        try:
            data = get_as_data(addr, service=args.service)
        except AddressFormatError as e:
            if args.address:
                parser.error('[{}] {}'.format(addr, e))
            else:
                stream = sys.stderr
                out_str = e
        except LookupError as e:
            stream = sys.stderr
            out_str = e
        else:
            stream = sys.stdout
            if not args.raw:
                out_str = '{0} | {1} | {2}'.format(data.handle, data.cc, data.as_name)
            else:
                print(data)
                continue

        print('%-15s  %s' % (addr, out_str), file=stream)
        if args.pause:
            sleep(1)
