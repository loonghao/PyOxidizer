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
# Downgrade time inside the container only — do not commit this change.
~/.cargo/bin/cargo update -p time --precise 0.3.36 2>/dev/null || true

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
