#!/bin/bash -eu

LCOV_VERSION=2.4

pushd /tmp
sudo rm -rf lcov-${LCOV_VERSION}

curl -SL https://github.com/linux-test-project/lcov/releases/download/v${LCOV_VERSION}/lcov-${LCOV_VERSION}.tar.gz | \
  tar -xz

pushd lcov-${LCOV_VERSION}
sudo make install
popd  # back to /tmp

rm -rf lcov-${LCOV_VERSION}
popd  # back to original directory
