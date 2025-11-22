#!/bin/bash

echo "export LD_LIBRARY_PATH=/usr/local/mpi/lib/:\$LD_LIBRARY_PATH" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=/usr/local/rccl/lib/:\$LD_LIBRARY_PATH"  >> ~/.bashrc

echo "export PATH=/usr/local/mpi/bin:\$PATH" >> ~/.bashrc
