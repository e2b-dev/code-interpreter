#!/bin/sh
set -eu

for certificate in /etc/ssl/certs/*; do
    for blocked in \
        /usr/share/ca-certificates/mozilla/emSign_ECC_Root_CA_-_G3.crt \
        /usr/share/ca-certificates/mozilla/Comodo_AAA_Services_root.crt; do
        if cmp -s "$certificate" "$blocked"; then
            rm -f "$certificate"
            break
        fi
    done
done
