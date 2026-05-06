#!/usr/bin/env python3
import os, sys, math, random

objects = [ "water_jug", "keetle", "cloth", "tea_bag", "cup", "sugar", "bowl", "milk",
		"cereal", "creamer", "cup", "sugar", "coffee", "bread", "cheese",
		"plate", "bread", "toaster", "butter", "knife", "peanut_butter", 
		"spoon", "pill_box", "juice", "popcorn", "dressing", "salad_tosser",
		"lunch_bag" ]
useables = [ "microwave", "phone", "toaster", "plants" ]

class Observation :
	
	def __init__( self, action, argument ) :
		self.action = action
		self.argument = argument

	def write( self, stream ) :
		print("(%s %s)"%(self.action, self.argument), file=stream)

class Take( Observation ) :
	
	def __init__( self, object ) :
		Observation.__init__(self, "take", object )

class Use( Observation ) :
		
	def __init__( self, object ) :
		Observation.__init__(self, "use", object )

class Activity :
	
	def __init__( self, name ) :
		self.name = name
		self.methods = []

	def generate_obs_seq( self, obs ) :
		# select method
		m = random.choice(self.methods)
		idx_vector = [ i for i in range(1,len(m)) ]
		if m[0] == 'u' :
			random.shuffle( idx_vector )
		for i in idx_vector :
			try :
				m[i].generate_obs_seq( obs )
			except AttributeError :
				# it is an observation
				obs.append( m[i] )

def write_template( output_name, true_hyp ) :
	# load hyps
	instream = open( 'hyps.dat' )
	hyps = []
	for line in instream :
		hyps.append( line.strip() )
	instream.close()
	# write true hyp
	outstream = open( 'real_hyp.dat', 'w' )
	print(hyps[true_hyp], file=outstream)
	outstream.close()		
	instream = open( 'kitchen-template.pddl' )
	outstream = open( 'template.pddl', 'w' )
	for line in instream :
		line = line.strip()
		if '<NAME>' in line :
			print(line.replace( '<NAME>', output_name.replace('.','_') ), file=outstream)
		elif '<OBJECTS>' in line :
			continue
		elif '<INITIAL>' in line :
			print('(= (total-cost) 0)', file=outstream)
			print("(dummy)", file=outstream)
		else :
			print(line, file=outstream)
	instream.close()
	outstream.close()

def write_observation_sequence( obs ) :
	outstream = open( 'obs.dat', 'w' )
	for o in obs :
		o.write( outstream )
	outstream.close()

def pack_and_clean_up( output_name ) :
	cmd = 'tar jcvf %s.tar.bz2 domain.pddl hyps.dat real_hyp.dat template.pddl obs.dat'%output_name
	os.system( cmd )
	cmd = 'rm -rf template.pddl real_hyp.dat obs.dat'
	os.system( cmd )

def make_activities() :
	
	boil_water = Activity( "boil_water" )
	boil_water.methods.append( [ 'o', Take("water_jug"), Take("keetle"), Take("cloth") ] )
	make_tea = Activity( "make_tea" )
	make_tea.methods.append( [ 'u', boil_water, Take( "tea_bag" ), Take( "cup" ), Take( "sugar" ) ] )
	make_tea.methods.append( [ 'u', boil_water, Take( "tea_bag" ), Take( "cup" ), Take( "sugar" ), Take( "milk" ) ] )
	make_tea.methods.append( [ 'u', boil_water, Take( "tea_bag" ), Take( "cup" ), boil_water ] )
	make_cereals = Activity( "make_cereals" )
	make_cereals.methods.append( [ 'u', Take( "bowl" ), Take( "cereal" ), Take( "milk" ) ] )
	make_coffee = Activity( "make_coffee" )
	make_coffee.methods.append( [ 'u', Take( "cup" ), Take( "coffee" ), Take( "creamer" ), Take( "sugar" ), boil_water ] )
	make_coffee.methods.append( [ 'u', Take( "cup" ), Take( "coffee" ), Take( "milk" ), Take( "sugar" ), boil_water ] )
	make_cheese_sandwich = Activity( "make_cheese_sandwich" )
	make_cheese_sandwich.methods.append( [ 'o', Take( "plate" ), Take( "bread" ), Take( "cheese" ) ] )
	make_toast = Activity( "make_toast" )
	make_toast.methods.append( [ 'o', Take( "bread" ), Use( "toaster" ) ] )
	make_buttered_toast = Activity( "make_buttered_toast" )
	make_buttered_toast.methods.append( [ 'o', make_toast, Take( "knife" ), Take( "butter" ) ] )
	make_buttered_toast.methods.append( [ 'o', make_toast, Take( "butter" ), Take( "knife" ) ] )
	make_peanut_butter_sandwich = Activity( "make_peanut_butter_sandwich" )
	make_peanut_butter_sandwich.methods.append( [ 'u', Take( "bread" ), Take( "peanut_butter" ), Take( "knife" ), Take( "plate" ) ] )
	pack_lunch = Activity( "pack_lunch" )
	pack_lunch.methods.append( [ 'u', Take( "lunch_bag" ), make_cheese_sandwich ] )
	pack_lunch.methods.append( [ 'u', Take( "lunch_bag" ), make_peanut_butter_sandwich ] )
	make_breakfast = Activity( "make_breakfast" )
	make_breakfast.methods.append( [ 'o', make_tea, make_buttered_toast, make_cereals, Take( "spoon" ) ] )
	make_breakfast.methods.append( [ 'o', make_buttered_toast, make_tea, make_cereals, Take( "spoon" ) ] )
	make_breakfast.methods.append( [ 'o', make_coffee, make_buttered_toast, make_cereals, Take( "spoon" ) ] )
	make_breakfast.methods.append( [ 'o', make_buttered_toast, make_coffee, make_cereals, Take( "spoon" ) ] )
	make_salad = Activity( "make_salad" )
	make_salad.methods.append( [ 'u', Take( "bowl" ), Take( "plate" ), Take( "dressing" ), Take( "salad_tosser" ) ] )
	make_salad.methods.append( [ 'u', Take( "bowl" ), Take( "plate" ), Take( "salad_tosser" ) ] )
	make_dinner = Activity( "make_dinner" )
	make_dinner.methods.append( [ 'u', make_salad, make_cheese_sandwich ] )
	make_dinner.methods.append( [ 'u', make_cheese_sandwich ] )
	make_dinner.methods.append( [ 'u', make_salad ] )
	take_medicine = Activity( "take_medicine" )
	take_medicine.methods.append( [ 'u', Take( "medicine" ) ] )
	watch_movie = Activity( "watch_movie" )
	watch_movie.methods.append( [ 'o', Take( "popcorn" ), Use( "microwave" ) ] )
	wipe_counter = Activity( "wipe_counter" )
	wipe_counter.methods.append( ['o', Take( "cloth" ) ] )
	tend_to_plants = Activity( "tend_to_plants" )
	tend_to_plants.methods.append( [ 'o', Take( "water_jug" ), Use( "plants" ) ] )
	drink_juice = Activity( "drink_juice" )
	drink_juice.methods.append( [ 'u', Take( 'juice' ), Take( 'cup' ) ] )
	leave_for_work = Activity( "leave_for_work" )
	leave_for_work.methods.append( [ 'u', pack_lunch, make_breakfast, tend_to_plants ] )
	go_to_bed = Activity( "go_to_bed" )
	go_to_bed.methods.append( [ 'o', make_dinner, take_medicine ] )
	return make_dinner, make_breakfast, pack_lunch 

def sample( obs, ratio ) :
	if not ratio == 'full' :
		k = int( math.ceil( (float(ratio)/100.0) * len(obs) ) )
		if k < 1 : k = 1
		indices = range(0,len(obs))
		sample_idx = random.sample( indices, k )
		sample_idx.sort()
		sample = [ obs[i] for i in sample_idx ]
	else :
		sample = obs
	return sample	

def main() :

	if len(sys.argv) < 2 :
		print("Missing arguments!", file=sys.stderr)
		print("Usage: ./generator.py <# instances to generate per % Obs >", file=sys.stderr)
		sys.exit(1)

	num_instances_pct_obs = int( sys.argv[1] )
	make_dinner, make_breakfast, pack_lunch = make_activities()


	output_name = 'kitchen_generic_hyp-%d'
	activities = [ make_breakfast, pack_lunch, make_dinner ]
	sample_ratios = [ 10, 30, 50, 70, 'full' ]
	for pct_obs in sample_ratios :
		for i in range(0, num_instances_pct_obs ) :
			obs = []
			act_index = random.randint(0,2)
			activities[act_index].generate_obs_seq( obs )
			sampled_obs = sample( obs, pct_obs )
			experiment_name = '_'.join( [output_name, str(pct_obs), str(i)] ) 
			write_template( experiment_name%act_index, act_index )
			write_observation_sequence( sampled_obs )
			pack_and_clean_up( experiment_name%act_index )

if __name__ == "__main__" :
	main()
		
