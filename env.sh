#!/bin/bash
apt update 
apt install -y gfortran

echo "export LD_LIBRARY_PATH=/usr/local/mpi/lib/:\$LD_LIBRARY_PATH" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=/usr/local/rccl/lib/:\$LD_LIBRARY_PATH"  >> ~/.bashrc

echo "export PATH=/usr/local/mpi/bin:\$PATH" >> ~/.bashrc

apt install -y openssh-server


sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#Port 22/Port 6379/' /etc/ssh/sshd_config

mkdir -p /run/sshd
pkill sshd
/usr/sbin/sshd

