import shlex

import pytest
from e2b import Sandbox

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
