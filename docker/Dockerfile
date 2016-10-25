FROM ubuntu:16.04

MAINTAINER Loic Dutrieux "loic.dutrieux@gmail.com"

RUN apt-get update && apt-get install -y \
		wget \
		python \
        # python3 \
     && rm -rf /var/lib/apt/lists/*

# Install Seadas (requires curl, git and bash)
RUN wget http://oceandata.sci.gsfc.nasa.gov/ocssw/install_ocssw.py
RUN chmod +x install_ocssw.py
RUN ./install_ocssw.py --terra
# RUN echo "export OCSSWROOT=[SeaDAS_install_dir]/ocssw" >> .bashrc
# RUN echo "source $OCSSWROOT/OCSSW_bash.env" >> .bashrc