import numpy as np
import json
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

path = os.getenv('DATAPATH') #TODO: change to your own :) Path to your data folder
print("PATH", path)
path = path.replace("\\", "/")

with open("../params.json") as f:
  params = json.load(f)


np.random.seed(seed = params["random_seed"]) # Knowing the seed in advance is good


'''
 Given the number of samples on the unit sphere, returns that many uniformly chosen points
'''
def sample_maxwell(num_samples): # Thank you thermodynamics
	Xs = np.random.normal(0, 1, (num_samples, 1))
	Ys = np.random.normal(0, 1, (num_samples, 1))
	Zs = np.random.normal(0, 1, (num_samples, 1))

	norms = np.sqrt(np.square(Xs) + np.square(Ys) + np.square(Zs))

	Xs = Xs/norms
	Ys = Ys/norms
	Zs = Zs/norms

	radius_squared = params["lightstage_radius"]
	my_sample = radius_squared * np.concatenate((Xs, Ys, Zs), axis = 1)

	return my_sample


if __name__ == "__main__":
	num_objects = params["num_objects"]
	num_lights = num_objects*params["num_lights"]
	num_cameras = num_objects*params["num_cameras"]
	
	coordinate_data_path = path + "/coordinate_data/"

	if not os.path.exists(coordinate_data_path):
		os.makedirs(coordinate_data_path)

	camera_coordinates = sample_maxwell(num_cameras)
	with open(coordinate_data_path + "/camera_coordinates.csv", "w+") as f:
		np.savetxt(f, camera_coordinates, delimiter = ",", encoding = "utf-8")

	light_coordinates = sample_maxwell(num_lights)
	with open(coordinate_data_path + "/light_coordinates.csv", "w+") as f:
		np.savetxt(f, light_coordinates, delimiter = ",", encoding = "utf-8")


