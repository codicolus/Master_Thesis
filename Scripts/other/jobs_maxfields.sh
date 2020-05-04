#!/bin/bash
#
#SBATCH --mail-user=example_mail@mailto.ch
#SBATCH --job-name="Maxfield_calculation"
#SBATCH --mail-type=FAIL
#SBATCH --time=00:20:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=10G
#SBATCH --partition=partition_name
#SBATCH --account=account_name
#SBATCH --output="outfile.log"
#SBATCH --error="errorfile.log"

# activating conda environment in job submission
export PATH="path_to_conda_environment":$PATH
export CONDA_DEFAULT_ENV=env_name
export CONDA_PREFIX="path_to_conda_environment"

source "path_to_conda_env_activation_file" env_name

# MAXFIELDS
srun python ../MAXFIELDS.py $1 $2 &
