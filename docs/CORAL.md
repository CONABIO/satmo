## Coral Setup

*This page documents the setup of the coral server at conabio*

### Seadas

```sh
wget http://oceandata.sci.gsfc.nasa.gov/ocssw/install_ocssw.py
chmod +x install_ocssw.py
groupadd seadas
usermod -aG seadas loic
usermod -aG seadas xtuser
mkdir /data/ocssw
chown root:seadas /data/ocssw
chmod 775 /data/ocssw/
./install_ocssw.py --install-dir=/data/ocssw --git-branch=v7.3 --aqua --seawifs --terra --viirsn
# When running as loic
echo "export OCSSWROOT=/data/ocssw" >> ~/.zshrc
source ~/.zshrc
echo "source $OCSSWROOT/OCSSW_bash.env" >> ~/.zshrc
```

I also updated the pre-processors by running
```sh
update_luts.py terra
update_luts.py aqua
update_luts.py seawifs
update_luts.py viirsn
```

### GDAL

```sh
add-apt-repository ppa:ubuntugis/ubuntugis-unstable
apt-get update
apt-get install libgdal-dev gdal-bin
```

### Other stuff

```sh
apt-get install python-pip python-scipy python-numpy
# Some stuff for matplotlib
apt-get install python-tk
```

- virtualenv
- virtualenvwrapper

```sh
mkvirtualenv --system-site-packages satmo-dev
```

### Data root

I initiated a dataroot at `/export/isilon/datos2/satmo2_data/`

Permissions and ownership cannot be changed on this drive therefore for now seadas has to be operated as `xtuser`.


### Notes

The /data drive was initially mounted with noexec; so I remounted it by running `mount -o remount,exec /dev/mapper/data-Vol_001 /data`

Any jupyter notebook started by `loic` can be accessed remotely via browser. ([coral:9999](coral:9999)). Password is `notebook`. The notebook server running permanently (launched with `nohup jupyter notebook &`) is running from within the `satmo-dev` virtualenv.

