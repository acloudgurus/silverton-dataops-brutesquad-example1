f#!/usr/bin/env bash
set -ex

source commands/test_funcs.sh

pwd

export PATH=$HOME/.local/bin:$PATH

test_individual_module utilitiess/toml_utilities
