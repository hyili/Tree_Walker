#!/bin/env python3

import subprocess
import csv

result = {}

fpath = input()
output = subprocess.check_output("/bin/ls %s" % fpath, shell=True)
filenames = output.decode().replace("\n", " ").split(" ")

for filename in filenames:
	nlines = 0

	try:
		f = open(filename, "r")
		reader = csv.reader(f)
	except FileNotFoundError as e:
		print("FileNotFoundError %s, (%s)" % (e, filename))
		continue

	# Find the index of 狀態碼 column
	index = -1
	res = next(reader)
	nlines += 1
	for r in res:
		if r == "狀態碼":
			index = res.index(r)

	if index == -1:
		continue

	while True:
		try:
			res = next(reader)
			r = res[index]
			nlines += 1
			if result[r] is None:
				pass
			else:
				print("%s add one, (%s, %s ,%s)" % (r, filename, index, nlines))
				result[r] += 1
		except KeyError as e:
			print("KeyError %s, (%s, %s ,%s)" % (e, filename, index, nlines))
			print("%s set to 1" % (r))
			result[r] = 1
		except StopIteration as e:
			print("Stop Iteration %s, (%s, %s ,%s)" % (e, filename, index, nlines))
			break
		except Exception as e:
			print("Exception %s, (%s, %s ,%s)" % (e, filename, index, nlines))
			break

print(result)
