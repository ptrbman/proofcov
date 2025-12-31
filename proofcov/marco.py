############################################
# Copyright (c) 2016 Microsoft Corporation
# 
# Basic core and correction set enumeration.
#
# Author: Nikolaj Bjorner (nbjorner)
############################################

"""
Enumeration of Minimal Unsatisfiable Cores and Maximal Satisfying Subsets
This tutorial illustrates how to use Z3 for extracting all minimal unsatisfiable
cores together with all maximal satisfying subsets. 

Origin
The algorithm that we describe next represents the essence of the core extraction
procedure by Liffiton and Malik and independently by Previti and Marques-Silva: 
 Enumerating Infeasibility: Finding Multiple MUSes Quickly
 Mark H. Liffiton and Ammar Malik
 in Proc. 10th International Conference on Integration of Artificial Intelligence (AI)
 and Operations Research (OR) techniques in Constraint Programming (CPAIOR-2013), 160-175, May 2013. 

Partial MUS Enumeration
 Alessandro Previti, Joao Marques-Silva in Proc. AAAI-2013 July 2013 

Z3py Features

This implementation contains no tuning. It was contributed by Mark Liffiton and it is
a simplification of one of the versions available from his Marco Polo Web site.
It illustrates the following features of Z3's Python-based API:
   1. Using assumptions to track unsatisfiable cores. 
   2. Using multiple solvers and passing constraints between them. 
   3. Calling the C-based API from Python. Not all API functions are supported over the
	  Python wrappers. This example shows how to get a unique integer identifier of an AST,
	  which can be used as a key in a hash-table. 

Idea of the Algorithm
The main idea of the algorithm is to maintain two logical contexts and exchange information
between them:

	1. The MapSolver is used to enumerate sets of clauses that are not already
	   supersets of an existing unsatisfiable core and not already a subset of a maximal satisfying
	   assignment. The MapSolver uses one unique atomic predicate per soft clause, so it enumerates
	   sets of atomic predicates. For each minimal unsatisfiable core, say, represented by predicates
	   p1, p2, p5, the MapSolver contains the clause  !p1 | !p2 | !p5. For each maximal satisfiable
	   subset, say, represented by predicats p2, p3, p5, the MapSolver contains a clause corresponding
	   to the disjunction of all literals not in the maximal satisfiable subset, p1 | p4 | p6. 
	2. The SubsetSolver contains a set of soft clauses (clauses with the unique indicator atom occurring negated).
	   The MapSolver feeds it a set of clauses (the indicator atoms). Recall that these are not already a superset
	   of an existing minimal unsatisfiable core, or a subset of a maximal satisfying assignment. If asserting
	   these atoms makes the SubsetSolver context infeasible, then it finds a minimal unsatisfiable subset
	   corresponding to these atoms. If asserting the atoms is consistent with the SubsetSolver, then it
	   extends this set of atoms maximally to a satisfying set. 
"""

from z3 import *

def main():
	return
	

def get_MUSes(formula):
	csolver = SubsetSolver(formula)
	msolver = MapSolver(n=csolver.n)
	muses = []
	
	for orig, lits in enumerate_sets(csolver, msolver):
		# Exclude non-MUSes from being returned
		if orig != "MUS":
			continue

		# For every Z3 literal, convert it to its string name and place it in the list
		mus_names = [lit.decl().name() for lit in lits]

		# MUSes containing agnostic conditions are skipped
		if any("agnostic" in name for name in mus_names):
			continue

		print("MUS: ", mus_names)
		muses.append(mus_names)

	return muses

class SubsetSolver:
	n = 0
	s = Solver()
	guards = [] # The assumption literals
	bodies = [] # The actual conditions

	def __init__(self, formula):
		assumptions = parse_smt2_string(formula)
		
		for a in assumptions:
			if is_implies(a):
				# An assumption looks like this: Implies(a_line5.0, x.1 == 1)
				# Put the first argument in the guards list, put the second in the bodies list
				self.guards.append(a.arg(0))
				self.bodies.append(a.arg(1)) 
			# Add all assumptions to the solver
			self.s.add(a)

		# print("solver:\n", self.s)
		# print("solver_smt2:\n",self.s.to_smt2())
		self.n = len(self.guards)


	# Takes a seed, ex. [0, 3, 5] and returns a list of the corresponding assumption literals
	def to_literals(self, seed):
		list = []
		for i in seed:
			list.append(self.guards[i])

		return list

	# Check for SAT
	def check_subset(self, seed):
		# Pass the assumption literals to the solver.
		# Equivalent of doing check-sat-assuming()
		return self.s.check(self.to_literals(seed)) == sat

	## Convert an unsat core back to the corresponding indices
	def seed_from_core(self):
		core = self.s.unsat_core()
		result = []
		for i, g in enumerate(self.guards):
			if g in core:
				result.append(i)

		return result

	def complement(self, aset):
		return set(range(self.n)).difference(aset)

	def shrink(self, seed):
		current = set(seed)
		for i in seed:
			if i not in current:
				continue
			current.remove(i)
			if self.check_subset(list(current)):
				# If core is SAT after removing an element, its already minimal
				current.add(i)
			else:
				# If core is UNSAT after removing, return the smaller core
				current = set(self.seed_from_core())
		return list(current)

	def grow(self, seed):
		seed = list(seed)
		for i in range(self.n):
			if i not in seed:
				seed.append(i)
				if not self.check_subset(seed):
					# If the problem becomes unsat when adding the seed, remove it
					seed.pop()
		return seed



class MapSolver:
	def __init__(self, n):
		"""Initialization.
				Args:
				n: The number of constraints to map.
		"""
		self.solver = Solver()
		self.n = n
		self.all_n = set(range(n))  # used in complement fairly frequently

	def next_seed(self):
		"""Get the seed from the current model, if there is one.
				Returns:
				A seed as an array of 0-based constraint indexes.
		"""
		if self.solver.check() == unsat:
				return None
		seed = self.all_n.copy()  # default to all True for "high bias"
		model = self.solver.model()
		for x in model:
			if is_false(model[x]):
				seed.remove(int(x.name()))
		return list(seed)

	def complement(self, aset):
		"""Return the complement of a given set w.r.t. the set of mapped constraints."""
		return self.all_n.difference(aset)

	def block_down(self, frompoint):
		"""Block down from a given set."""
		comp = self.complement(frompoint)
		self.solver.add( Or( [Bool(str(i)) for i in comp] ) )

	def block_up(self, frompoint):
		"""Block up from a given set."""
		self.solver.add( Or( [Not(Bool(str(i))) for i in frompoint] ) )
	


def enumerate_sets(csolver, map):
	"""Basic MUS/MCS enumeration, as a simple example."""
	while True:
		seed = map.next_seed()
		if seed is None:
		   	return
		if csolver.check_subset(seed):
			# SAT, 
			MSS = csolver.grow(seed)
			yield ("MSS", csolver.to_literals(MSS))
			map.block_down(MSS)
		else:
			#UNSAT
			seed = csolver.seed_from_core()
			MUS = csolver.shrink(seed)
			yield ("MUS", csolver.to_literals(MUS))
			map.block_up(MUS)

main()

