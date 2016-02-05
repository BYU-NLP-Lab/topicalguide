FROM fedora:20
MAINTAINER Ethan Garofolo <ethan@suchsoftware.com>

RUN useradd web -d /home/web -s /bin/bash
RUN yum install -y \
  automake \
  blas-devel \
  blas \ 
  curl-devel \
  expat-devel \
  gcc \
  gcc-c++ \
  gettext-devel \
  git \
  ipython \
  java-1.7.0-openjdk \
  lapack-devel \
  make \
  numpy \
  openssl-devel \
  postgresql-devel \
  python-devel \
  python-matplotlib \
  python-nose \
  python-pandas \
  sympy \
  zlib-devel

ADD vendor/get-pip.py /
ADD requirements.txt /
RUN python get-pip.py
RUN pip install -r requirements.txt

ADD . /home/web/src/
RUN chown -R web:web /home/web/

USER web
WORKDIR /home/web/src/

ENV TOPICAL_GUIDE_WORKING_DIR /home/web/topical_guide_working_dir

ENTRYPOINT ["/bin/bash"]
