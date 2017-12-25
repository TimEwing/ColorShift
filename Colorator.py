from __future__ import division
import Image
import math
import argparse
import os
import sys
import time
import colorsys
from collections import deque
import itertools

def main():
	parser = argparse.ArgumentParser(description="Fuck up an image")
	parser.add_argument('filename', type=str, help="File to fuck")
	parser.add_argument('colorsize', type=int, help="Minimum: ceil(cbrt(width*height)) - color resolution")
	parser.add_argument('--order', type=int, nargs=3, default=[0,1,2], help="Order to check cells in, default 0 1 2")
	parser.add_argument('--hsv', action='store_true', default=False, help="Use HSV instead of RGB. Be warned, this breaks the whole uniqueness thing since (255, 0, 0) is the same color as (33, 0, 0)")
	parser.add_argument('--sort', type=int, default=None, help="Sort a thing. Include a number between 0 and however many I end up adding to change modes. I like 0")
	parser.add_argument('--sort_again', type=int, default=None, help="Sort a thing in a different place. 3 is cool")
	parser.add_argument('--be_slow', action='store_true', default=False, help="Do a BFS for end points. This is slow. Don't do this. Literally I'm leaving this code in here in case I accidentally break shit. Note: I'm pretty sure this is broken if you use --order")
	parser.add_argument('--output_dir', type=str, default=os.getcwd(), help="Where to put the fucked file")
	parser.add_argument('--output_file', type=str, help="Where to put the fucked file, but also the name")
	args = parser.parse_args()

	global filename
	filename = args.filename
	print "File: {}\n\n".format(filename)

	# Filename shit
	global output_filename
	if args.output_file is None:
		if args.output_dir is None:
			output_filename = os.path.join(filename, '_output00')
		else:
			output_filename = os.path.join(args.output_dir, os.path.basename(filename) + '_output00')
		# Default to not overwriting files
		filename_version = 0
		while os.path.exists(output_filename + '.bmp'):
			output_filename = output_filename[:-2] + str(filename_version).zfill(2)
			filename_version += 1
		output_filename = output_filename + '.bmp'
	else:
		output_filename = args.output_file

	global color_size
	color_size = args.colorsize

	if args.hsv:
		get_adj = get_adj_HSB
		convert_color = lambda a, b, c : colorsys.rgb_to_hsv(a, b, c)
		unconvert_color = lambda a, b, c : colorsys.hsv_to_rgb(a, b, c)
	else:
		get_adj = get_adj_RGB
		convert_color = lambda a, b, c : (a, b, c)
		unconvert_color = lambda a, b, c : (a, b, c)

	input_image = Image.open(filename).convert()
	width, height = input_image.size

	# Init input pixel list, and modify it to only use appropriate colors
	input_pixels = input_image.load()
	transform_pixels = {}
	for x in range(width):
		for y in range(height):
			a = input_pixels[x, y][0] / 255.0
			b = input_pixels[x, y][1] / 255.0
			c = input_pixels[x, y][2] / 255.0

			a, b, c = convert_color(a, b, c)

			a = a * (color_size - 1)
			b = b * (color_size - 1)
			c = c * (color_size - 1)

			transform_pixels[x, y] = (int(a), int(b), int(c))

	del input_image

	# Init 3d 'color' space, where we will do the smoothing
	# each point in this space is a list of (x,y) coordinates
	transform_colorspace = {}
	for a in range(color_size):
		for b in range(color_size):
			for c in range(color_size):
				transform_colorspace[(a, b, c)] = deque()

	for x in range(width):
		for y in range(height):
			key = transform_pixels[x, y]

			# Reorder shit
			key = get_ordered_args(args.order, *key)

			transform_colorspace[key].append((x, y))

	del transform_pixels

	# Now do the actual color smoothing
	start_keys = [x for x in sorted(transform_colorspace, key=lambda x: len(transform_colorspace[x])) if len(transform_colorspace[x]) > 1] # MY MAX LINE LENGTH IS INFINITY	
	_test_keys = [x for x in transform_colorspace if len(transform_colorspace[x]) == 0]
	_prev = 0
	queue = deque()
	for key_number, start_key in enumerate(start_keys):
		if args.sort == 0:
			transform_colorspace[start_key]= deque(sorted(transform_colorspace[start_key], key=lambda x: x[0] - x[1]))
		elif args.sort == 1:
			transform_colorspace[start_key]= deque(sorted(transform_colorspace[start_key], key=lambda x: get_dist(x[0], x[1], width, height))) # lol this line is actually longer
		else:
			transform_colorspace[start_key]= deque(transform_colorspace[start_key])

		if len(transform_colorspace[start_key]) != _prev:
			prev = len(transform_colorspace[start_key])
			sys.stdout.write('\r' + "{0:.2f}%".format(key_number / len(start_keys) * 100))
			sys.stdout.flush()

		# Maybe BFS if the user hates life
		if args.be_slow:
			## BEGIN REALLY SHITTY INEFFICIENT SEARCH:
			# Declare shit
			end_keys = []
			searched = {} # Use a dict for searched keys because hash maps are fastish
			prev = {}
			queue.clear()

			# Init shit
			start_key_size = len(transform_colorspace[start_key])
			queue.append(start_key)
			searched[start_key] = None # We only care if the key exists, not it's value
			prev[start_key] = None

			# Breadth first search for a viable spot to flatten to
			while queue:
				current_key = queue.popleft()
				# If the size of the point here is zero (ie there are no points 
				# that are this color), it's an end point
				if len(transform_colorspace[current_key]) == 0:
					end_keys.append(current_key)
					# We need to find start_key_size - 1 open spots
					if(len(end_keys) >= start_key_size - 1):
						break

				# Search the nodes that are adjacent to this one
				for adj in get_adj(current_key, searched, args.order, color_size):
					searched[adj] = None
					prev[adj] = current_key
					queue.append(adj)

			# For each end point we found, slide along the path and move the 
			# tail of one point to the head of the next.
			for end_key in end_keys:
				assert prev[end_key] is not None # This would be really bad

				current_key = end_key
				while prev[current_key] is  not None:
					transform_colorspace[current_key].append(transform_colorspace[prev[current_key]].popleft())
					current_key = prev[current_key]
			## END REALLY SHITTY SLOW STUFF
		else:
			# Oh good we're not masochists

			# Find nearby empty spots
			## Dumb way to do it:
			# end_keys = [x for x in transform_colorspace if len(transform_colorspace[x]) == 0]
			# Less dumb way to do it:
			# Use expanding cubic shells of pixels to pick a decent approximation of nearest color

			end_key_count = len(transform_colorspace[start_key]) - 1 # How many empty spaces we need
			end_keys = get_target_keys(end_key_count, start_key, transform_colorspace, color_size)
			assert end_key_count == len(end_keys)

			# Possibly sort the end keys according to xy distance from the start point
			if args.sort_again == 0:
				end_keys = sorted(end_keys, key=lambda x: x[0])
			elif args.sort_again == 1:
				end_keys = sorted(end_keys, key=lambda x: x[1])
			elif args.sort_again == 2:
				end_keys = sorted(end_keys, key=lambda x: x[2])
			elif args.sort_again == 3:
				end_keys = sorted(end_keys, key=lambda x:(x[0]<<1 + x[1]<<1 + x[2]<<1))

			# Slide keys along the path to each end point from this point
			for end_key in end_keys:
				path = get_path_RGB(start_key, end_key)

				prev_key = path[0]
				for curr_key in path[1:]:
					transform_colorspace[curr_key].append(transform_colorspace[prev_key].popleft())
					prev_key = curr_key

		assert len(transform_colorspace[start_key]) == 1

	for key in transform_colorspace:
		if len(transform_colorspace[key]) > 1:
			print len(transform_colorspace[key])
			print key in _test_keys

	# Transform back to 256 colors
	print "\nConverting image..."
	output_image = Image.new("RGB", (width, height))
	for key, point in transform_colorspace.iteritems():
		ordered_key = get_unordered_args(args.order, *key)

		a = float(ordered_key[0]) / (color_size - 1)
		b = float(ordered_key[1]) / (color_size - 1)
		c = float(ordered_key[2]) / (color_size - 1)

		a, b, c = unconvert_color(a, b, c)

		a = int(float(a) * 255)
		b = int(float(b) * 255)
		c = int(float(c) * 255)

		for pos in point:
			x, y = pos
			output_image.putpixel((x, y), (a, b, c))

	try:
		output_image.save(output_filename)
		print "Saved image to {}".format(output_filename)
	except:
		"Couldn't save file {}".format(output_filename)

	output_image.show()

def brensenham_sucks(start_key, end_key):
	keys = []

	x0, y0, z0 = start_key
	x1, y1, z1 = end_key

	dx = abs(x1-x0)
	dy = abs(y1-y0)
	dz = abs(z1-z0)

	dx = abs(end_key[0] - start_key[0])
	sx = 1 if x0 < x1 else -1
	dy = abs(end_key[1] - start_key[1])
	sy = 1 if y0 < y1 else -1
	dz = abs(end_key[2] - start_key[2])
	sz = 1 if z0 < z1 else -1

	dm = max(dx, dy, dz)
	i = dm

	x1 = y1 = z1 = dm/2

	while True:
		keys.append((x0, y0, z0))

		if i == 0:
			return keys
		i -= 1

		x1 -= dx
		if x1 < 0:
			x1 += dm
			x0 += sx

		y1 -= dy
		if y1 < 0:
			y1 += dm
			y0 += sy

		z1 -= dz
		if z1 < 0:
			z1 += dm
			z0 += sz

def get_target_keys(num_keys, start_key, transform_colorspace, color_size):

	# Figure out when to exit the while loop
	limit = max(	color_size - start_key[0],
					color_size - start_key[1],
					color_size - start_key[2],
					start_key[0],
					start_key[1],
					start_key[2])

	end_keys = []
	shell_size = 1
	while shell_size < limit:
		# Get limits
		x_start	= start_key[0] - shell_size
		y_start	= start_key[1] - shell_size
		z_start	= start_key[2] - shell_size
		x_end	= start_key[0] + shell_size
		y_end	= start_key[1] + shell_size
		z_end	= start_key[2] + shell_size

		# Top and bottom (actually front/back but shut up this way is easier to think about)
		for y in range(y_start, y_end + 1):
			for z in range(z_start, z_end + 1):
				# Top
				key = (x_start, y, z)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys
				# Bottom
				key = (x_end, y, z)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys

		# Sides
		for x in range(x_start + 1, x_end):
			for z in range(z_start, z_end + 1):
				# Front row
				key = (x, y_start, z)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys
				# Back row
				key = (x, y_end, z)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys

			for y in range(y_start + 1, y_end):
				# Left side
				key = (x, y, z_start)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys
				# Right side
				key = (x, y, z_end)
				if check_and_append(end_keys, key, num_keys, transform_colorspace, color_size):
					return end_keys
		shell_size += 1
	else:
		# If we get here, someone fucked up their colorsize
		assert all([False, "Dude fix your colorsize..."]) # I mean I could just do a real error, but I don't remember the syntax


def check_and_append(l, key, count, transform_colorspace, color_size):
	for channel in key:
		if channel < 0 or channel >= color_size:
			return False

	if len(transform_colorspace[key]) == 0:
		l.append(key)
		return len(l) >= count
	return False

def get_path_RGB(start_key, end_key):
	return brensenham_sucks(start_key, end_key)
	# current_key = start_key
	# path = deque()
	# path.append(current_key)
	# tribool = (False, False, False) # Optimization bullshit
	# while True:
	# 	for x in [0, 1, 2]:
	# 		if not tribool[x]:
	# 			if current_key[x] > end_key[x]:
	# 				current_key = current_key[:x] + (current_key[x]-1,) + current_key[x+1:]
	# 			elif current_key[x] < end_key[x]:
	# 				current_key = current_key[:x] + (current_key[x]+1,) + current_key[x+1:]
	# 			else:
	# 				tribool = tribool[:x] + (True,) + tribool[x+1:] # Magic ass slicing bullshit
	# 	path.append(current_key)
	# 	if tribool[0] and tribool[1] and tribool[2]:
	# 		return path

def get_dist(x, y, width, height):
	return ((width/2 - x) ** 2 + (height/2 - y) ** 2) ** 0.5

def get_adj_RGB(color, searched, order, color_size):
	cs = color_size - 1
	adj = []
	for channel in order:
		if color[channel] > 0:
			c = color[:channel] + (color[channel]-1,) + color[channel+1:]
			if c not in searched:
				adj.append(c)
		if color[channel] < cs:
			c = color[:channel] + (color[channel]+1,) + color[channel+1:]
			if c not in searched:
				adj.append(c)
	return adj

def get_adj_HSB(color, searched, order, color_size):
	cs = color_size - 1
	adj = []
	for channel in order:
		if channel == 0:
			c = color[:channel] + ((color[channel]+1)%color_size,) + color[channel+1:]	
			if c not in searched:
				adj.append(c)
			c = color[:channel] + ((color[channel]-1)%color_size,) + color[channel+1:]	
			if c not in searched:
				adj.append(c)
		else:
			if color[channel] > 0:
				c = color[:channel] + (color[channel]-1,) + color[channel+1:]	
				if c not in searched:
					adj.append(c)
			if color[channel] < cs:
				c = color[:channel] + (color[channel]+1,) + color[channel+1:]
				if c not in searched:
					adj.append(c)
	return adj

def get_ordered_args(order, a, b, c):
	abc = (a,b,c)
	return (abc[order[0]], abc[order[1]], abc[order[2]])

def get_unordered_args(order, a, b, c):
	# I can't figure out how to calculate the inverses for the life of me so I'm just gonna hardcode
	hardcoded_map = {	(0, 1, 2) : (0, 1, 2),
						(0, 2, 1) : (0, 2, 1),
						(1, 0, 2) : (1, 0, 2),
						(2, 0, 1) : (1, 2, 0),
						(1, 2, 0) : (2, 0, 1),
						(2, 1, 0) : (2, 1, 0)}
	abc = (a,b,c)
	new_order = hardcoded_map[tuple(order)]
	return (abc[new_order[0]], abc[new_order[1]], abc[new_order[2]])

if __name__ == '__main__':
	main()
