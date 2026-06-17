// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

//! Build script for python-oxidized-importer.
//!
//! This script uses pyo3-build-config to emit the correct cfg flags
//! for the Python version being compiled against. These flags enable
//! conditional compilation for version-specific features.

fn main() {
    // Use PyO3's build configuration to emit cfg flags like Py_3_11, Py_3_12, etc.
    // This is required for conditional compilation based on Python version.
    pyo3_build_config::use_pyo3_cfgs();
}

