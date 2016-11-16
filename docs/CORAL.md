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
./install_ocssw.py --install-dir=/data/ocssw --git-branch=v7.2 --aqua --seawifs --terra --viirsn
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

### Notes

The /data drive was initially mounted with noexec; so I remounted it by running `mount -o remount,exec /dev/mapper/data-Vol_001 /data`

Any jupyter notebook started by `loic` can be accessed remotely via browser. ([coral:9999](coral:9999)). Password is `notebook`. The notebook server running permanently (launched with `nohup jupyter notebook &`) is running from within the `satmo-dev` virtualenv.

