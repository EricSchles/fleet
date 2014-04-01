#!/usr/bin/env python

"""Fleet is a simple library/tool for performing remote actions via ssh."""

from subprocess import Popen, PIPE
import argparse
import datetime
import shlex
import os


class RemoteResponse(object):

    """Useful information about a single command which has already run."""

    cmd = None
    outut = None
    error = None

    def __init__(self, cmd, output, error):
        self.cmd = cmd
        self.output = output
        self.error = error
        self.create_time = datetime.datetime.now()

    def __str__(self):
        return str(self.output)

    def __call__(self):
        return (self.cmd, self.output, self.error, self.create_time)


class RemoteHost(object):

    """Represents potential ssh connections and commands to a remote host."""

    def __init__(self, username, address, port=22, **kwargs):
        self.username = str(username)
        self.address = str(address)
        self.port = str(port)

    def run_command(self, remote_cmd):
        """Single command run over a non-persistent connection."""
        ssh_cmd = 'ssh -p {port} {username}@{address} {0}'.format(
            remote_cmd, **self.__dict__)
        _result = Popen(shlex.split(ssh_cmd), shell=False, stdout=PIPE)
        return RemoteResponse(remote_cmd, *_result.communicate())

    @classmethod
    def _scp_command(cls, scp_cmd):
        _result = Popen(shlex.split(scp_cmd), shell=False, stdout=PIPE)
        return _result.communicate()

    def get_files(self, remote_path, local_path):
        _cmd = 'scp {0} -p {port} {username}@{address}:{1} {2}'.format(
            remote_path, local_path, **self.__dict__)
        return RemoteHost._scp_command(_cmd)

    def put_files(self, local_path, remote_path):
        _cmd = 'scp -r -p {port} {1} {username}@{address}:{2}'.format(
            remote_path, local_path, **self.__dict__)
        return RemoteHost._scp_command(_cmd)

    def __str__(self):
        return '{username}@{address}:{port}'.format(**self.__dict__)


def add_pub_key(remote_host_object, pub_key_file=None,
                authorized_keys_file=None, **kwargs):
    """Add a public key to some remote hosts authorized keys file."""

    add_pub_key_cmd = '"echo \'{0}\' >> {1}"'.format(
        str(open(pub_key_file, 'r').read()), authorized_keys_file)
    remote_host_object.run_command(add_pub_key_cmd)


def parse_args(arg_list):
    """Returns a dictionary of arguments."""
    parser = argparse.ArgumentParser(
        description="Perform remote actions on some host(s) via ssh and scp.")
    parser.add_argument('username', type=str,
                        help="Username to use for ssh login.")
    parser.add_argument('address', type=str, help="Address of remote host.")
    parser.add_argument('-p', '--port', type=int, required=False,
                        default=22, help="SSH port to connect to.")

    subparsers = parser.add_subparsers()

    addkey_parser = subparsers.add_parser(
        'addkey',
        help="Add the current machines public key to some remote host."
    )
    addkey_parser.add_argument(
        '-P',
        '--pub-key-file',
        ype=str,
        default='{HOME}/.ssh/id_rsa.pub'.format(**os.environ),
        help="Path to the public key file."
    )
    addkey_parser.add_argument(
        '-A',
        '--authorized-keys-file',
        type=str,
        default='~/.ssh/authorized_keys',
        help="Path to the authorized keys file."
    )

    cmd_parser = subparsers.add_parser(
        'cmd', help="Run a command on some remote host.")
    cmd_parser.add_argument('remote_cmd', type=str, help="Command to be run.")

    return parser.parse_args(arg_list)


if __name__ == '__main__':
    import sys

    args = vars(parse_args(sys.argv[1:]))
    remote_host = RemoteHost(**args)

    if 'pub_key_file' in args:
        add_pub_key(remote_host, **args)

    if 'remote_cmd' in args:
        print(remote_host.run_command(args['remote_cmd']))
