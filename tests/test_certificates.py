import shlex

import pytest
from e2b import Sandbox

pytestmark = pytest.mark.skip_debug

CHECK_CERTIFICATES = """
import ssl
from importlib.metadata import version
from pathlib import Path

import certifi
from pip._vendor import certifi as pip_certifi

assert tuple(map(int, version('certifi').split('.'))) >= (2026, 10, 19)
assert tuple(map(int, version('pip').split('.'))) >= (26, 2, 2)

blocked = {'emSign ECC Root CA - G3', 'AAA Certificate Services'}
for bundle in (None, certifi.where(), pip_certifi.where()):
    context = ssl.create_default_context(cafile=bundle)
    if bundle is None:
        for path in Path('/etc/ssl/certs').iterdir():
            if path.is_file():
                try:
                    context.load_verify_locations(cafile=str(path))
                except ssl.SSLError:
                    pass
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


def test_java_certificate_store(sandbox: Sandbox):
    result = sandbox.commands.run(
        "/usr/lib/jvm/jdk-11/bin/keytool -J-Duser.language=en -list -v -cacerts -storepass changeit",
        user="root",
    )
    assert result.exit_code == 0
    assert "trustedCertEntry" in result.stdout
    assert "CN=AAA Certificate Services," not in result.stdout
    assert "CN=emSign ECC Root CA - G3," not in result.stdout
