#!/bin/bash
#SBATCH --job-name=PREPROCESS
#SBATCH --output=PREPROCESS_%j.out
#SBATCH --array=1-100

# Request 1 CPU core
#SBATCH -n 1
#SBATCH -t 60:00:00

	#Uncomment if running locally
START=0
STEP=1
END=12000
blender=/Applications/Blender.app/Contents/MacOS/Blender

for ((i=$START;i<$END;i=i+$STEP))
do
	echo $i
    $blender -b -P dataset-synthesis/scripts/preprocessing.py -- -o $i
done

# # SLURM batch script
# module load blender/2.90.1
# input=$((SLURM_ARRAY_TASK_ID)) - 1
# blender -b -P /users/dmasotti/data/dmasotti/dataset-synthesis/ -- -o $input