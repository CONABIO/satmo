Installation
------------

System setup
^^^^^^^^^^^^

You can also 

The commands with sudo have to be ran from a user account with ``sudo`` priviledges, or directly from ``root``, without sudo. Commands that **do not** start with sudo have to be ran from a normal user account. Example ``xtuser`` on CONABIO servers.

.. code-block:: bash

    # Install generic and spatial libraries
    sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
    sudo apt-get update
    sudo apt-get install libproj-dev libgeos-dev gdal-bin libgdal-dev
    sudo apt-get install python-pip git
    sudo pip install virtualenv
    sudo pip install virtualenvwrapper
    # As the user from which satmo will be operated (e.g. xtuser)
    echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc
    source ~/.bashrc

    # Install Version v7.4 of Seadas
    wget http://oceandata.sci.gsfc.nasa.gov/ocssw/install_ocssw.py
    chmod +x install_ocssw.py
    seadas_dir=/data/ocssw
    mkdir $seadas_dir
    ./install_ocssw.py --install-dir=$seadas_dir --git-branch=v7.4 --aqua --seawifs --terra --viirsn
    echo "export OCSSWROOT=$seadas_dir" >> ~/.profile
    source ~/.profile
    echo "source $OCSSWROOT/OCSSW_bash.env" >> ~/.profile

    # Create a virtualenv named satmo and install the satmo package in it
    mkvirtualenv satmo
    pip install -U pip
    pip install numpy==1.13.1
    pip install git+https://github.com/CONABIO/satmo.git

Further details on installing the satmo python library can be found in the project `travis file`_ 


Autostart
^^^^^^^^^

It's important to have the near real time command of the system start automatically (e.g.: after server maintenance and restart). For that, a @reboot cron task can be created. See the explanations below. 

.. code-block:: bash
    
    # As xtuser, enter crontab edit mode by running:
    crontab -e
    # And add the following line to the file
    @reboot . ~/.profile; /home/xtuser/.virtualenvs/satmo/bin/satmo_nrt.py --day_vars chlor_a nflh sst Kd_490 --night_vars sst --l1a_vars afai fai --north 33 --south 3 --west -122 --east -72 -d /export/isilon/datos2/satmo2_data/ -multi 3 > /home/xtuser/nrt_log.log &


.. _travis file: https://github.com/CONABIO/satmo/blob/master/.travis.yml