#!/bin/bash

python run.py --build_rccl_tests --build_tests_with_MPI --prefix /opt/rocm --amdgpu_targets="gfx1201"
