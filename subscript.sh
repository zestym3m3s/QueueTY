#!/bin/bash
#
#$ -q speedy
#$ -cwd
#$ -j y
#$ -S /bin/bash
#$ -N {mol_name}
#$ -pe orte 10
#$ -R y

######## ENTER YOUR TURBOMOLE INSTALLATION PATH HERE ##########
export TURBODIR=/state/partition1/TURBOMOLE/TURBOMOLE
###############################################################
export PATH=$TURBODIR/scripts:$PATH
export PARA_ARCH=MPI
export PATH=$TURBODIR/bin/`sysname`:$PATH
export PARNODES=10
ulimit -s unlimited
module load openmpi-x86_64
pwd
jobex -c 400 -ri > job.out