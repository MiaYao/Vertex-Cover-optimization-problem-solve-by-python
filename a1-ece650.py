#!/usr/bin/python

import re
import sys
import operator

class VertexCover:

	def __init__(self):

		'''
		street_nodes: dictionary
		key: string, street_name
		value: list, street_nodes
		'''
		self.street_nodes = {}

		'''
		V: dictionary
		key: int, assigned number of vertex
		value: tuple, GPS_coordinate of the vertex
		'''
		self.V = {}

		'''
		E: list
		element: tuple, connect two elements in v
		'''
		self.E = []

		'''
		error_messages: dictionary
		key: string, error_type
		value: string, error description
		'''
		self.error_messages = {
			"wrong_input_format" 	: "Error: input does not match the required format.\n" ,# Using this format: \n > add a street     :	a street_name GPS_coordinate\n > change a street  :	c street_name GPS_coordinate\n > remove a street  :	r street_name\n > generate a graph :	g\n > exit program     :	exit", # may change the right format to option help
			"street_no_exist" 		: "Error: 'c' or 'r' specified for a street that does not exist.\n",
			#"insufficient_nodes"	: "Error: 'a' or 'c' should specify at least two nodes.\n" ,
			"illegal_node_value"	: "Error: the values in GPS coordinate should be only integer or float numbers.\n" ,
			"add_exist_street"		: "Error: 'a' specified an existing street, use 'c' instead.\n",
			"wrong_coordinate"		: "Error: GPS coordinate specified without right format, should be a tuple with two numbers. No space inside.\n",
			"system_error"			: "Error: I'm sorry this is an unknown system_error. Restart your program. \n"
		}

		'''
		street_lines: dictionary
		key: string, street_name
		value: set, street_lines
		'''
		self.street_lines = {}

		'''
		intersections: set
		elements: tuple, GPS_coordinate
		'''
		self.intersections = set()

		'''
		V_backup: dictionary
		the same as V, just for backup the numbers, so that it will always have the same id for the same vertex
		'''
		self.V_backup = {}

		'''
		count: integer
		value: the max id for the current vertex
		'''
		self.count = 0

		'''
		temp_list: set
		elements: temporarily used for storing the short path
		'''
		self.temp_list = set()

		'''
		end_re: regular expression for exit the program
		'''
		self.end_re = re.compile("^exit$")

	def get_command(self, command):
		'''collect commands from the standard input'''

		while(not re.compile('^g$').search(command) and not self.end_re.search(command)):

			if command != "+" and self.command_handler(command):

				self.V.clear()
				del self.E[0:]
				self.intersections.clear()
				self.temp_list.clear()

				self.construct_tree()

			try:
				command = raw_input()
			except EOFError:
				command = "exit"

		return command

	def run_exp(self):
		'''run the whole experiments'''

		while(1):

			command = '+'

			try:
				command = self.get_command(command)
			except EOFError:
				break

			if re.compile('^g$').search(command):
				self.visualize_tree()
			elif self.end_re.search(command):
				break
			else:
				sys.stderr.write(self.error_messages["system_error"])


	def is_street_exist(self, street_name):
		'''check whether the specified street exists'''

		if street_name in self.street_nodes.keys():
			return True
		else:
			return False

	def command_handler(self, command):
		'''handle exceptions when input commands, and also store the street into the street_nodes'''

		ac_command_re = re.compile("^(a|c)\s*\"(.*)\"\s*(\(.*\))$")
		remove_command_re = re.compile("^r\s*\"(.*)\"$")
		output_command_re = re.compile('^g$')
		node_re = re.compile("(.*),(.*)\)")

		if ac_command_re.search(command):

			info = ac_command_re.findall(command)[0]

			action = info[0]
			street_name = info[1]
			nodes = info[2].strip(" ").split("(")
			del nodes[0]

			if len(nodes) < 2:
				#sys.stderr.write(self.error_messages["insufficient_nodes"])
				return False

			nodes_tuple = []

			if self.is_street_exist(street_name):
				if action == 'a':
					sys.stderr.write(self.error_messages["add_exist_street"])
					return False
			else:
				if action == 'c':
					sys.stderr.write(self.error_messages["street_no_exist"])
					return False



			for node in nodes:
				if not node_re.search(node):
					sys.stderr.write(self.error_messages["wrong_coordinate"])
					return False

				node_info = node_re.findall(node)[0]
				try:
					node = (float(node_info[0]), float(node_info[1]))
					nodes_tuple.append(node)
				except ValueError:
					sys.stderr.write(self.error_messages["illegal_node_value"])
					return False

			self.street_nodes[street_name] = nodes_tuple
			return True

		elif remove_command_re.search(command):

			street_name = remove_command_re.findall(command)[0]
			if not self.is_street_exist(street_name):
				sys.stderr.write(self.error_messages["street_no_exist"])
				return False

			del self.street_nodes[street_name]
			return True

		elif not output_command_re.search(command):
			sys.stderr.write(self.error_messages["wrong_input_format"])
			return False

	def construct_tree(self):
		'''based on the commands, calculate the location of cameras, get the nodes and the edges'''


		street_names = self.street_nodes.keys()

		# get the intersections
		for street_i in range(0, len(street_names) - 1):

			for street_j in range (street_i + 1, len(street_names)):

				street_i_name = street_names[street_i]
				street_j_name = street_names[street_j]

				self.street_lines[street_i_name] = set()
				self.street_lines[street_j_name] = set()

				street_i_nodes = self.street_nodes[street_i_name]
				street_j_nodes = self.street_nodes[street_j_name]

				for node_i in range(0, len(street_i_nodes) - 1):

					for node_j in range(0, len(street_j_nodes) - 1):

						line_i = (street_i_nodes[node_i], street_i_nodes[node_i + 1])
						line_j = (street_j_nodes[node_j], street_j_nodes[node_j + 1])

						self.street_lines[street_i_name].add(line_i)
						self.street_lines[street_j_name].add(line_j)

						point = self.calculate(line_i, line_j)
						if point != False:
							# print point
							self.intersections.add(point)

		# for every line who has the intersection, separate and store into a temporary list
		if len(self.intersections) > 0:
			self.is_intersected()

	def is_intersected(self):
		'''get E,V'''

		for intersection in self.intersections:
			for street_name in self.street_lines.keys():
				temp_remove_list = []
				temp_add_list = []
				for line in self.street_lines[street_name]:
					if self.is_on_line(intersection, line):
						(line_0, line_1) = line
						add_line_0 = (intersection, line_0)
						add_line_1 = (intersection, line_1)

						temp_remove_list.append(line)
						temp_add_list.append(add_line_0)
						temp_add_list.append(add_line_1)

				for remove_line in temp_remove_list:
					self.street_lines[street_name].remove(remove_line)
					if remove_line in self.temp_list:
						self.temp_list.remove(remove_line)
				for add_line in temp_add_list:
					self.street_lines[street_name].add(add_line)
					self.temp_list.add(add_line)

		# separate V
		nodes = set()
		edges = set()
		for temp_nodes in self.temp_list:
			edges.add(temp_nodes)
			for node in temp_nodes:
				if node not in self.V_backup.values():
					self.count += 1
					self.V_backup[self.count] = node

		for edge in edges:
			(node_0, node_1) = edge
			node_id_0 = 0
			node_id_1 = 0
			for node_id in self.V_backup.keys():
				if node_0 == self.V_backup[node_id]:
					node_id_0 = node_id
					self.V[node_id_0] = node_0
				elif node_1 == self.V_backup[node_id]:
					node_id_1 = node_id
					self.V[node_id_1] = node_1
				if node_id_0 and node_id_1:
					break
			self.E.append((node_id_0, node_id_1))

	def is_on_line(self, intersection, line):
		'''check whether a point on the line'''

		(inter_x, inter_y) = intersection
		(start_x, start_y) = line[0]
		(end_x, end_y) = line[1]


		diff_x_inter = inter_x - start_x
		diff_y_inter = inter_y - start_y

		diff_x_line = end_x - start_x;
		diff_y_line = end_y - start_y;

		cross_product = diff_x_inter * diff_y_line - diff_y_inter * diff_x_line

		if abs(cross_product) < sys.float_info.epsilon * 100:
			if self.is_between(line, line, inter_x, inter_y):
				return True

		return False

	def calculate(self, line_i, line_j):
		'''get the result of tuple of intersection GPS coordinate'''

		# Ax+By=C
		# A=y2-y1 B=x1-x2 C=x1y2-x2y1
		# (A1B2-A2B1)x = B2C1 - B1C2
		# (A2B1-A1B2)y = A2C1 - A1C2

		(B_i, A_i) = tuple(map(operator.sub, line_i[1], line_i[0]))
		(B_j, A_j) = tuple(map(operator.sub, line_j[1], line_j[0]))

		B_i = - B_i
		B_j = - B_j

		C_i = line_i[0][0] * line_i[1][1] - line_i[0][1] * line_i[1][0]
		C_j = line_j[0][0] * line_j[1][1] - line_j[0][1] * line_j[1][0]

		k_y = A_j * B_i - A_i * B_j
		b_y = A_j * C_i - A_i * C_j

		k_x = A_i * B_j - A_j * B_i
		b_x = B_j * C_i - B_i * C_j

		if k_y == 0 or k_x == 0:
			# no intrersection
			return False
		else:
			x = b_x / k_x
			y = b_y / k_y

			if self.is_between(line_i, line_j, x, y):
				# intersection not on extension
				return x, y
			return False

	def is_between(self, line_i, line_j, x, y):
		'''check whether the point is between the two/one lines'''
		max_x_i = max(line_i[0][0], line_i[1][0])
		min_x_i = min(line_i[0][0], line_i[1][0])

		max_y_i = max(line_i[0][1], line_i[1][1])
		min_y_i = min(line_i[0][1], line_i[1][1])

		max_x_j = max(line_j[0][0], line_j[1][0])
		min_x_j = min(line_j[0][0], line_j[1][0])

		max_y_j = max(line_j[0][1], line_j[1][1])
		min_y_j = min(line_j[0][1], line_j[1][1])


		if x >= min_x_i and x <= max_x_i and y >= min_y_i and y <= max_y_i:
			if x >= min_x_j and x <= max_x_j and y >= min_y_j and y <= max_y_j:
				return True
			else:
				return False
		else:
			return False

	def visualize_tree(self):
		'''output the tree to the standard output'''

		print 'V = {'
		for v in self.V.keys():
			print ' ', str(v) + ": (" + "%.2f" % self.V[v][0] + "," + "%.2f" % self.V[v][1] + ")"
		print '}'
		print 'E = {'
		count = 0
		for e in self.E:
			if count == len(self.E) - 1:
				if int(e[0]) != 0 and int(e[1]) != 0:
					print ' <' + str(int(e[0])) + "," + str(int(e[1])) + '>'
			else:
				if int(e[0]) != 0 and int(e[1]) != 0:
					print ' <' + str(int(e[0])) + "," + str(int(e[1])) + '>,'
					count += 1

		print '}'


if __name__ == "__main__":
	vertex = VertexCover()
	vertex.run_exp()
