#!/bin/bash
#SBATCH --job-name=RENDER
#SBATCH --output=RENDER_%j.out
#SBATCH --array=51-100

#SBATCH -p gpu --gres=gpu:2
#SBATCH --constraint=quadrortx
#SBATCH --mem=32G
#SBATCH -n 4
#SBATCH -t 12:00:00

module load blender/2.90.1
module load python/3.7.4
module load cuda
input=$((SLURM_ARRAY_TASK_ID))
blender -b --factory-startup -noaudio -P /path/to/your/scripts/generate_images.py -- -s 0 -e 3600 -o $input
