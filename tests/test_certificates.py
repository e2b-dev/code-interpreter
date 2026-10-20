import json
import shlex

import pytest
from e2b import Sandbox

from harness import CodeInterpreter

pytestmark = pytest.mark.skip_debug

CHECK_CERTIFICATES = """
import ssl
from importlib.metadata import version

import certifi
from pip._vendor import certifi as pip_certifi

assert tuple(map(int, version('certifi').split('.'))) >= (2026, 10, 19)
assert tuple(map(int, version('pip').split('.'))) >= (26, 2, 2)

blocked = {'emSign ECC Root CA - G3', 'AAA Certificate Services'}
for bundle in (None, certifi.where(), pip_certifi.where()):
    context = ssl.create_default_context(cafile=bundle)
    certificates = context.get_ca_certs()
    assert certificates, f'Empty trust store: {bundle}'
    names = {
        value
        for certificate in certificates
        for rdn in certificate['subject']
        for key, value in rdn
        if key == 'commonName'
    }
    assert not names & blocked, f'{bundle}: still trusts {names & blocked}'
print('Certificate stores verified')
"""


@pytest.mark.parametrize("python", ["python", "/root/.server/.venv/bin/python"])
def test_certificate_stores(sandbox: Sandbox, python: str):
    result = sandbox.commands.run(
        f"{python} -c {shlex.quote(CHECK_CERTIFICATES)}", user="root"
    )
    assert result.exit_code == 0
    assert "Certificate stores verified" in result.stdout


CHECK_NODE_HTTPS = """
(async () => {
const https = require('node:https');
const probe = (host) => new Promise((resolve, reject) => {
    const request = https.get(`https://${host}/`, (response) => {
        response.resume();
        resolve('connected');
    });
    request.setTimeout(15000, () => request.destroy(new Error('TLS probe timed out')));
    request.on('error', (error) => {
        if (error.code === 'UNABLE_TO_GET_ISSUER_CERT_LOCALLY' ||
            error.code === 'UNABLE_TO_VERIFY_LEAF_SIGNATURE' ||
            error.code === 'SELF_SIGNED_CERT_IN_CHAIN') {
            resolve('untrusted');
        } else {
            reject(error);
        }
    });
});
const results = await Promise.all([
    probe('dv-g3b-emudhra.we-have-a-problem.com'),
    probe('dv-g3b-aaa-emudhra.we-have-a-problem.com'),
    probe('nodejs.org'),
]);
console.log(JSON.stringify(results));
})()
"""


def test_node_certificate_stores(sandbox: Sandbox, client: CodeInterpreter):
    command = CHECK_NODE_HTTPS
    result = sandbox.commands.run(f"node -e {shlex.quote(command)}")
    assert json.loads(result.stdout) == ["untrusted", "untrusted", "connected"]

    execution = client.run_code("await " + command, language="js")
    assert execution.error is None
    assert json.loads("".join(execution.stdout)) == [
        "untrusted",
        "untrusted",
        "connected",
    ]
