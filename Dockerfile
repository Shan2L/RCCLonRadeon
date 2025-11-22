FROM rocm/pytorch:rocm6.4.4_ubuntu24.04_py3.12_pytorch_release_2.7.1


RUN apt install openssh-server -y

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
RUN sed -i 's/#Port 22/Port 6379/' /etc/ssh/sshd_config

WORKDIR /root

# install mpi
RUN wget https://www.mpich.org/static/downloads/4.3.1/mpich-4.3.1.tar.gz
RUN tar -xzvf mpich-4.3.1.tar.gz
WORKDIR mpich-4.3.1
RUN ./configure --prefix=/usr/local/mpi
RUN make -j 128
RUN make install

RUN echo "export LD_LIBRARY_PATH=/usr/local/mpi/lib:\$LD_LIBRARY_PATH"
RUN echo "export PATH=/usr/local/mpi/bin:\$PATH"

WORKDIR /root

ENTRYPOINT  ["/usr/sbin/sshd", "-D"]
