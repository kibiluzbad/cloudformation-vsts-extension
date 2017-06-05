#! /usr/bin/env python
"""Cloudformation 
"""
import sys
import os
import errno
import optparse
import logging

from glob import glob
import xml.etree.ElementTree
import subprocess
import coloredlogs
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError

import boto3


class NoneText(object):
    """Default value node search in pom file.
    """

    def text(self):
        """Get text. Returns None.
        """
        return None

class CloudformationDeployer(object):
    """Cloudformation deployer.
    """

    def __init__(self, **kargs):
        """Class constructor.
        """
        self.stack_name = kargs['stackName']
        self.client = boto3.client('cloudformation')
        self.logger = logging.getLogger()
        self.changeset_name = self.stack_name + os.environ.get('BUILD_BUILDID')

    def execute(self):
        """Execute cloudformation deployer
        """
        if self.does_changeset_exist():
            self.logger.info('Executing  change set ' + self.changeset_name + '.')
            type = 'stack_create_complete' if self.is_creation_changeset() else 'stack_update_complete'
            self.client.execute_change_set(
                StackName=self.stack_name,
                ChangeSetName=self.changeset_name
            )
            self.wait(type=type)
        else:
            self.logger.info('No change set ' + self.changeset_name + ' was found.')

    def wait(self, **kargs):
        """Wait change set creation to complete
        """
        try:
            waiter = self.client.get_waiter(kargs['type'])
            waiter.wait(StackName=self.stack_name)
        except WaiterError as err:
            self.logger.warn(err)

    def does_changeset_exist(self):
        """Check if change set exists
        """
        try:
            response = self.client.describe_change_set(
                ChangeSetName=self.changeset_name,
                StackName=self.stack_name
            )
            return response['Status'] == 'CREATE_COMPLETE'
        except ClientError as err:
            self.logger.warn(err)
            return False

    def is_creation_changeset(self):
        """Check if this is a creation change set.
        """
        try:
            response = self.client.describe_stacks(
                StackName=self.stack_name
            )
            return response['Stacks'][0]['StackStatus'] == 'REVIEW_IN_PROGRESS'
        except ClientError as err:
            self.logger.warn(err)
            return False



def main():
    """Main entry point.
    """
    parser = optparse.OptionParser()

    parser.add_option('-e', '--execute',
                      action="store_true", dest="execute",
                      help="Run cloudformation script", default=False)
    parser.add_option('-n', '--name',
                      dest="name",
                      help="Cloudfomation stack name", metavar="NAME")
    parser.add_option('-v', '--verbose',
                      action="store_true", dest="verbose",
                      help="Show debug logs", default=False)

    options, args = parser.parse_args()

    logger = logging.getLogger()
    coloredlogs.install(level='DEBUG' if options.verbose else 'INFO')

    logger.info('Starting cloudformation deployer')

    logger.debug(options)
    logger.debug(args)

    if options.execute:
        CloudformationDeployer(stackName=options.name).execute()

if __name__ == "__main__":
    sys.exit(main())