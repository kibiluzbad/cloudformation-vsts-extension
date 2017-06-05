var path = require('path');
var tl = require('vso-task-lib');

var templatePath =  tl.getPathInput('template', false);
tl.debug('Template path: ' + templatePath);
tl.checkPath(templatePath, 'template');

const spawn = require('child_process').spawn;

const awsCliProcess = spawn('aws', ['cloudformation',
    'validate-template',
    '--template-body',
    'file://' + templatePath
]);

awsCliProcess.stdout.on('data', (data) => {
    console.log(`stdout: ${data}`);
});

awsCliProcess.stderr.on('data', (data) => {
    console.log(`stderr: ${data}`);
});

awsCliProcess.on('close', (code) => {
    tl.exit(code);
});