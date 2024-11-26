#!/usr/bin/env bash

set -euo pipefail

# This script generates the python SDK reference markdown files
# Run it in the `python-sdk/` directory

PKG_VERSION="v$(node -p "require('./package.json').version")"
ROUTES_DIR="../sdk-reference/code-interpreter-python-sdk/${PKG_VERSION}"
mkdir -p "${ROUTES_DIR}"

packages=("e2b_code_interpreter")

mkdir -p sdk_ref

for package in "${packages[@]}"; do
    # generate raw SDK reference markdown file
    poetry run pydoc-markdown -p "${package}" >sdk_ref/"${package}".mdx
    # remove package path display
    sed -i'' -e '/<a[^>]*>.*<\/a>/d' "sdk_ref/${package}.mdx"
    # remove empty hyperlinks
    sed -i'' -e '/^# /d' "sdk_ref/${package}.mdx"
    # remove " Objects" from lines starting with "##"
    sed -i'' -e '/^## / s/ Objects$//' "sdk_ref/${package}.mdx"
    # replace lines starting with "####" with "###"
    sed -i'' -e 's/^####/###/' "sdk_ref/${package}.mdx"
    # move to docs
    mkdir -p "${ROUTES_DIR}/${package}"
    mv "sdk_ref/${package}.mdx" "${ROUTES_DIR}/${package}/page.mdx"
done

rm -rf sdk_ref
