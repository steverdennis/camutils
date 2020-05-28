
Need to download and build voms-clients.
>wget https://github.com/italiangrid/voms-clients/archive/v3.0.7.tar.gz

Build with Maven:
> wget http://apache.mirror.anlx.net/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz
  
Put the `voms-clients` somewhere that's in `$PATH`

Make sure you have a FNAL kerberos token active (eg `kinit`)

Get FNAL trust/voms:

> mkdir ~/.voms
> rsync -P dune:/etc/vomses ~/.voms/vomses
> mkdir ~/.globus
> rsync -r -P -l dune:/etc/grid-security/certificates ~/.globus
> rsync -r -P -l dune:/etc/grid-security/vomsdir ~/.globus


Also need the FNAL UPS stuff set up:

> source /cvmfs/dune.opensciencegrid.org/products/dune/setup_dune.sh
> setup fife_utils  # includes setup kx509, setup ifdhc, setup sam_web_client

Then get a certifiace and then a proxy:
> kx509
> voms-proxy-init -noregen -rfc --certdir ~/.globus/certificates/ --vomsdir ~/.globus/vomsdir/ -voms dune:/dune/Role=Analysis

Should then be able to get any file from SAM, eg
> ifdh_fetch PDSPProd3_protoDUNE_sp_reco_p2GeV_35ms_sce_datadriven_31396519_15_20200426T005537_Pandora_Events.pndr
