#!/bin/bash

python run.py --build_rccl_tests --build_tests_with_MPI --prefix /usr/local/rccl/ --amdgpu_targets="gfx1101"
