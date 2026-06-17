#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Builds PyOxy executables.

set -ex

TARGET_TRIPLE=$1
PYTHON_VERSION=$2
TARGET_DIR=$3

source ~/.cargo/env

cd /pyoxidizer

# The workspace Cargo.lock has time 0.3.47 which requires rustc >= 1.88.0,
# but this Docker image pins Rust 1.85.0 to avoid LLVM bitcode incompatibility
# (Python build artifacts use LLVM 22, Rust 1.85.0 uses LLVM 20).
# Downgrade time inside the container only. Copy to /tmp first because
# the workspace mount may be read-only.
cp Cargo.lock /tmp/Cargo.lock
sed -i 's/^version = "0\.3\.47"$/version = "0.3.36"/' /tmp/Cargo.lock
sed -i 's/^checksum = "743bd48c283afc0388f9b8827b976905fb217ad9e647fae3a379a9283c4def2c"$/checksum = "5dfd88e563464686c916c7e46e623e520ddc6d79fa6641390f2e3fa86e83e885"/' /tmp/Cargo.lock
sed -i 's/^version = "0\.1\.8"$/version = "0.1.2"/' /tmp/Cargo.lock
sed -i 's/^checksum = "7694e1cfe791f8d31026952abf09c69ca6f6fa4e1a1229e18988f06a04a12dca"$/checksum = "ef927ca75afb808a4d64dd374f00a2adf8d0fcff8e7b184af886c3c87ec4a3f3"/' /tmp/Cargo.lock
sed -i 's/^version = "0\.2\.27"$/version = "0.2.18"/' /tmp/Cargo.lock
sed -i 's/^checksum = "2e70e4c5a0e0a8a4823ad65dfe1a6930e4f4d756dcd9dd7939022b5e8c501215"$/checksum = "3f252a68540fde3a3877aeea552b832b40ab9a69e318efd078774a01ddee1ccf"/' /tmp/Cargo.lock
cp /tmp/Cargo.lock .

# Use PyOxidizer to generate embeddable files.
pyoxidizer build \
  --system-rust \
  --release \
  --path pyoxy \
  --target-triple ${TARGET_TRIPLE} \
  --var BUILD_PATH ${TARGET_DIR} \
  --var PYTHON_VERSION ${PYTHON_VERSION}

# Use PyOxidizer's embeddable files to build the pyoxy binary. Its
# build script will hook things up to the pyembed crate.
export PYO3_CONFIG_FILE=$(pwd)/pyoxy/${TARGET_DIR}/${TARGET_TRIPLE}/release/resources/pyo3-build-config-file.txt
~/.cargo/bin/cargo build \
  --target-dir pyoxy/${TARGET_DIR} \
  --bin pyoxy \
  --release \
  --target ${TARGET_TRIPLE}
