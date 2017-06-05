var path = require('path');
var tl = require('vso-task-lib');

var stackname = tl.getInput('stackname', true);

var basePath = path.resolve(__dirname)

tl.debug('Stack name: ' + stackname);

const spawn = require('child_process').spawn;
const reqFile = path.join(basePath, 'requirements.txt');
const pythonFile = path.join(basePath, 'cloudformation.py');

tl.debug('Req file path: ' + reqFile);
tl.debug('Python script path: ' + pythonFile);

execPip();

function execPip() {
    const pip = spawn('pip', ['install', '-r', reqFile]);

    pip.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pip.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
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
        '-n',
        stackname
    ]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        tl.exit(code);
    });
}