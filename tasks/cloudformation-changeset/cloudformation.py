#! /usr/bin/env python
"""Cloudformation
"""
import sys
import os
import json
import optparse
import logging

import coloredlogs
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError
from jinja2 import Template

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
        self.template_path = kargs['templatePath']
        self.stack_name = kargs['stackName']
        self.parameters = kargs['parameters']
        self.client = boto3.client('cloudformation')
        self.logger = logging.getLogger()
        self.changeset_name = self.stack_name + os.environ.get('BUILD_BUILDID')
        self.json_path = os.path.join(os.environ.get('BUILD_REPOSITORY_LOCALPATH'),
                                      self.changeset_name + '.html')

    def execute(self):
        """Execute cloudformation deployer
        """
        if self.does_stack_exists():
            self.update_changeset()
        else:
            self.create_changeset()
        self.wait()
        self.write_changes(changes=self.get_changes())

    def does_stack_exists(self):
        """Check if stack is already created
        """
        self.logger.info('Check if stack ' + self.stack_name + ' exists.')
        completed_status = ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
        try:
            response = self.client.describe_stacks(StackName=self.stack_name)
            if 'Stacks' in response:
                return response['Stacks'][0]['StackStatus'] in completed_status
            return False
        except ClientError as err:
            self.logger.warn(err)
            return False

    def create_changeset(self):
        """Updates cloudformation stack
        """
        self.logger.info('Updating stack ' + self.stack_name + '.')
        self.client.create_change_set(
            StackName=self.stack_name,
            ChangeSetName=self.changeset_name,
            TemplateBody=self.get_body(),
            Parameters=self.parameters,
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            ChangeSetType='CREATE'
        )

    def update_changeset(self):
        """Updates cloudformation stack
        """
        self.logger.info('Updating stack ' + self.stack_name + '.')
        self.client.create_change_set(
            StackName=self.stack_name,
            ChangeSetName=self.changeset_name,
            TemplateBody=self.get_body(),
            Parameters=self.parameters,
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            ChangeSetType='UPDATE'
        )


    def wait(self):
        """Wait change set creation to complete
        """
        try:
            waiter = self.client.get_waiter('change_set_create_complete')
            waiter.wait(ChangeSetName=self.changeset_name,
                        StackName=self.stack_name)
        except WaiterError as err:
            self.logger.warn(err)


    def get_body(self):
        """Get body of template file
        """
        with open(self.template_path, 'r') as template_body:
            return template_body.read()

    def get_changes(self):
        """Get changes from current change set
        """
        response = self.client.describe_change_set(
            ChangeSetName=self.changeset_name,
            StackName=self.stack_name
        )
        return response['Changes']

    def write_changes(self, **kargs):
        """Save changes to json file
        """
        self.logger.debug('Write changes to json file')
        self.logger.debug(kargs)
        if 'changes' not in kargs:
            self.logger.warn('No changes were found')
            return
        with open(self.json_path, "w") as text_file:
            text_file.write(self.parse_summary(**kargs))


    def parse_summary(self, **kargs):
        """Parse summary json data to html
        """

        template_data = """<table>
<thead>
<tr>
    <th style="cellpading:5px">Action</th>
    <th style="cellpading:5px">Logical ID</th>
    <th style="cellpading:5px">Physical ID</th>
    <th style="cellpading:5px">Resource type</th>
    <th style="cellpading:5px">Replacement</th>
</tr>
</thead>
<tbody>
{% for change in changes %}<tr>
    <td style="cellpading:5px">{{change.ResourceChange.Action}}</td>
    <td style="cellpading:5px">{{change.ResourceChange.LogicalResourceId}}</td>
    <td style="cellpading:5px">{{change.ResourceChange.PhysicalResourceId}}</td>
    <td style="cellpading:5px">{{change.ResourceChange.ResourceType}}</td>
    <td style="cellpading:5px">{{change.ResourceChange.Replacement}}</td>
</tr>{% endfor %}
</tbody>
</table>"""
        template = Template(template_data)
        rendered = template.render(changes=kargs['changes'])
        self.logger.debug(rendered)
        return rendered


def parse_param_list(option, opt_str, value, parser):
    result = []
    if value:
        for item in value.split('|'):
            parameter = item.split('=')

            if len(parameter) != 2:
                raise Exception('Wrong parameters')

            result.append({
                'ParameterKey': parameter[0],
                'ParameterValue': parameter[1],
                'UsePreviousValue': False
            })
    setattr(parser.values, 'parameters', result)

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
    parser.add_option('-p', '--params',
                      type='string',
                      action='callback',
                      callback=parse_param_list,
                      help="Parameters comma separed list. Ex: param_name1:value1,param_name2:value2",
                      metavar="PARAM_LIST")
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
        CloudformationDeployer(templatePath=args[0],
                               stackName=options.name,
                               parameters=options.parameters if hasattr(options, 'parameters') else []).execute()

if __name__ == "__main__":
    sys.exit(main())