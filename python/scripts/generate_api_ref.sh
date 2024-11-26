#!/usr/bin/env bash

set -euo pipefail

# This script generates the python sdk api reference markdown files
# Run it in the `python-sdk/` directory

PKG_VERSION="v$(node -p "require('./package.json').version")"
ROUTES_DIR="../api-reference/code-interpreter-python-sdk/${PKG_VERSION}"
mkdir -p "${ROUTES_DIR}"

packages=("e2b_code_interpreter")

mkdir -p api_ref

for package in "${packages[@]}"; do
    # generate raw api reference markdown file
    poetry run pydoc-markdown -p "${package}" >api_ref/"${package}".mdx
    # remove package path display
    sed -i'' -e '/<a[^>]*>.*<\/a>/d' "api_ref/${package}.mdx"
    # remove empty hyperlinks
    sed -i'' -e '/^# /d' "api_ref/${package}.mdx"
    # remove " Objects" from lines starting with "##"
    sed -i'' -e '/^## / s/ Objects$//' "api_ref/${package}.mdx"
    # replace lines starting with "####" with "###"
    sed -i'' -e 's/^####/###/' "api_ref/${package}.mdx"
    # move to docs
    mkdir -p "${ROUTES_DIR}/${package}"
    mv "api_ref/${package}.mdx" "${ROUTES_DIR}/${package}/page.mdx"
done

rm -rf api_ref
