# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import datetime
import time
import socket
import json


class HealthChecker(object):
    """
    HealthChecker provides a uniform way to run checks that provides output to
    different monitoring and logging systems sush as nagios, sensu, etc
    """

    # standard return codes
    OK = 0
    WARNING = 1
    CRITICAL = 2

    def __init__(self, name):
        self.name = name
        self.status = {'status': self.OK,
                       'message': 'Not set',
                       'timestamp': 'Not set',
                       'kv': {}
                       }

    def check(self):
        """ the child inheriting from HealthChecker should implement the checks specific to the use case
        this method doesn't return any value, just fill in the internal dictionary `self.status`
        a check must fill the `status`, `message` and `timestamp` fields of `self.status`
        any check-specific values should go into the generic key/value store `self.status.kv`
        """
        raise Exception('Not implemented')

    @staticmethod
    def get_format_options():
        """ provide the user with a way to query the supported formats"""
        return ['nagios', 'sensu', 'generic', 'sensu-metric']

    def get_output(self, output_format):
        """ Returns  ret code and a message that reflects the health status according to `output_format`"""

        ret_code = self.status.get('status')
        message = ''
        try:
            if output_format == 'nagios':
                if ret_code == self.OK:
                    message = 'OK - {}'.format(self.status.get('message'))
                elif ret_code == self.CRITICAL:
                    message = 'CRITICAL - {}'.format(self.status.get('message'))
                else:
                    message = 'WARNING - {}'.format(self.status.get('message'))

            elif output_format == 'sensu':
                # this is the minimum required attributes for sensu, we can add more if required
                # https://sensuapp.org/docs/latest/reference/checks.html#check-result-check-attributes
                # TODO: check what `output` makes sense in case of error
                sensu_output_format = {'status': ret_code,
                                       'name': self.name,
                                       'output': json.dumps(self.status)}
                message = json.dumps(sensu_output_format, indent=4)

            elif output_format == 'sensu-metric':
                # generate 'net.cartodb.<cloud>.<hostname>.<metric)name>'
                sensu_metric_server_prefix = '.'.join(socket.gethostname().split('.')[::-1])
                sensu_metric_prefix = '{}.{}'.format(sensu_metric_server_prefix, self.name)
                output = []
                for k, v in self.status.get('kv').items():
                    output.append('{}.{} {} {}'.format(sensu_metric_prefix, k, v, self.status['timestamp']))

                message = '\n'.join(output)
            else:  # output_format == generic
                message = json.dumps(self.status, indent=4)
        except Exception as ex:
            print('[Exception]: error while formatting output: {}'.format(ex), file=sys.stderr)

        return ret_code, message

    def dump_log(self, dest_log_file):  # TODO should the script take care of log rotation?
        """ logs internal data structure into `dest_log_file` in json format"""
        try:
            with open(dest_log_file, 'a') as f:
                f.write(json.dumps(self.status, indent=4) + '\n')
        except IOError as e:
            print('[Exception]: error writing to {} file [{}]'.format(dest_log_file, e), file=sys.stderr)

