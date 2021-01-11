import os
import numpy as np
import json

path = os.getenv('DATAPATH') #TODO: change to your own :) Path to your data folder
print("PATH", path)
path = path.replace("\\", "/")


# Instead of using the weird shapenet names, lets put them into lookup table indexed by normal ints
def generate_lookup_table():
	table = {}

	k = 0
	for file in os.listdir(path + "shapenet/gltf/"):
		if file.endswith(".gltf"):
			table[str(k)] = file
			k = k + 1

	with open(path + "shapenet/lookup_table.json", "w+") as f:
		json.dump(table, f)


if __name__ == "__main__":
	generate_lookup_table()