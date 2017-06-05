var path = require('path');
var tl = require('vso-task-lib');

var templatePath = tl.getPathInput('template', true);
var array = tl.getDelimitedInput('parameters', '\n');
tl.debug(array);
var parameters = array.join('|');
var stackname = tl.getInput('stackname', true);

var basePath = path.resolve(__dirname)

tl.debug('Template path: ' + templatePath);
tl.debug('Parameters: ' + parameters);
tl.debug('Stack name: ' + stackname);

tl.checkPath(templatePath, 'template');

const spawn = require('child_process').spawn;
const reqFile = path.join(basePath, 'requirements.txt');
const pythonFile = path.join(basePath, 'cloudformation.py');

const buildPath = tl.getVariable('BUILD_REPOSITORY_LOCALPATH');
const buildId = tl.getVariable('BUILD_BUILDID');
const changesetName = stackname + buildId + '.html';

const summaryFile = path.join(buildPath, changesetName);

tl.debug('Req file path: ' + reqFile);
tl.debug('Python script path: ' + pythonFile);

execPip();

function execPip() {
    const pip = spawn('pip', ['install', '-r', reqFile]);

    pip.stdout.on('data', (data) => {
        console.log(`${data}`);
    });

    pip.stderr.on('data', (data) => {
        console.log(`${data}`);
    });

    pip.on('close', (code) => {
        if (code > 0) {
            tl.exit(code);
            return;
        }
        execPython();
    });
}

function execPython() {
    const pythonProcess = spawn('python', [pythonFile,
        '-ev',
        templatePath,
        '-n',
        stackname,
        '-p',
        parameters
    ]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.log(`${data}`);
    });

    pythonProcess.on('close', (code) => {
        uploadBuildSummary()
        tl.exit(code);
    });
}

function uploadBuildSummary() {
    tl.debug('Uploading ' + summaryFile);
    tl.command('task.addattachment', {
        'type': 'Distributedtask.Core.Summary',
        'name': 'Cloudformation change set'
    }, summaryFile);
}