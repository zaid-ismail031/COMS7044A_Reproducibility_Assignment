import os, sys, math, random

places = [ "bank", "watson_theater", "hayman_theater", "davis_theater", "jones_theater",
		"bookmark_cafe", "library", "cbs", "psychology_bldg", "angazi_cafe", "tav" ]

activity_reqs = { "banking" : [ "bank" ],
		"lecture-1" : [ "watson_theater" ],
		"lecture-2" : [ "hayman_theater" ],
		"lecture-3" : [ "davis_theater" ],
		"lecture-4" : [ "jones_theater" ],
		"group-meeting-1" : ["bookmark_cafe", "library", "cbs"],
		"group-meeting-2" : ["library", "cbs", "psychology_bldg"],
		"group-meeting-3" : ["angazi_cafe", "psychology_bldg"],
		"coffee" : ["tav", "angazi_cafe", "bookmark_cafe"],
		"breakfast" : ["tav", "angazi_cafe", "bookmark_cafe"],
		"lunch" : ["tav", "bookmark_cafe"] }

class Observation :
	
	def __init__( self, src, dst ) :
		self.source = src
		self.destination = dst

	def write( self, stream ) :
		print("(MOVE %s %s)"%(self.source, self.destination), file=stream)

def write_template( output_name, initial_location, true_hyp ) :
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
	instream = open( 'campus-template.pddl' )
	outstream = open( 'template.pddl', 'w' )
	for line in instream :
		line = line.strip()
		if '<NAME>' in line :
			print(line.replace( '<NAME>', output_name.replace('.','_') ), file=outstream)
		elif '<OBJECTS>' in line :
			continue
		elif '<INITIAL>' in line :
			print('(= (total-cost) 0)', file=outstream)
			print('(at %s)'%initial_location, file=outstream)
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

def do_random_choice( chance ) :
	x = random.random()
	if x < chance : return True 
	return False

def add_noise( src, obs_seq, chance ) :
	if do_random_choice( chance ) :
		# choose some random place different
		dst = random.choice( places )
		obs = Observation( src, dst )
		obs_seq.append( obs )
		src = dst
	return src
	
def add_obs_for_activity( src, obs_seq, chance_random, activity ) :
	src = add_noise( src, obs_seq, chance_random )
	dst = random.choice( activity_reqs[activity] )
	obs_seq.append( Observation( src, dst ) )
	src = dst
	src = add_noise( src, obs_seq, chance_random )
	return dst

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

def generate_problem_for_activity_1( output_name, chance_random, ratio ) :
	src = initial_location = random.choice( places )
	obs_seq = []
	x = random.random()
	if x < 0.5 :
		src = add_obs_for_activity( src, obs_seq, chance_random, "breakfast" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-1" )
	else :
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-1" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "breakfast" )
	x = random.random()
	if x < 0.5 :
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-1" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-2" )
	else :
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-2" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-1" )
	src = add_obs_for_activity( src, obs_seq, chance_random, "coffee" )
	print("Generated Observation sequence with", len(obs_seq), "actions")
	write_template( output_name, initial_location, 0)
	sampled_obs = sample( obs_seq, ratio )
	write_observation_sequence( sampled_obs )
	pack_and_clean_up( output_name )

def generate_problem_for_activity_2( output_name, chance_random, ratio ) :
	src = initial_location = random.choice( places )
	obs_seq = []
	x = random.random()
	if x < 0.5 :
		src = add_obs_for_activity( src, obs_seq, chance_random, "banking" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-2" )
	else :
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-2" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "banking" )
	src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-3" )
	x = random.random()
	if x < 0.33 :
		src = add_obs_for_activity( src, obs_seq, chance_random, "lunch" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-4" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-3" )
	elif x >= 0.33 and x < 0.66 :
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-4" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "lunch" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-3" )
	else :
		src = add_obs_for_activity( src, obs_seq, chance_random, "lecture-4" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "group-meeting-3" )
		src = add_obs_for_activity( src, obs_seq, chance_random, "lunch" )
	print("Generated Observation sequence with", len(obs_seq), "actions")
	write_template( output_name, initial_location, 1 )
	sampled_obs = sample( obs_seq, ratio )
	write_observation_sequence( sampled_obs )
	pack_and_clean_up( output_name )

def main() :

	if len(sys.argv) < 3 :
		print("Missing arguments!", file=sys.stderr)
		print("Usage: ./generator.py <# instances> <noise>", file=sys.stderr)
		sys.exit(1)
	
	instances_to_generate = int(sys.argv[1])
	chance_for_random_movement = float(sys.argv[2])
	
	sample_ratios = [ 10, 30, 50, 70, 'full' ]

	i = 1
	for ratio in sample_ratios :	
		for k in range(0,instances_to_generate) :
			activity_index = random.randint(0,1)
			if activity_index == 0 :
				exp_file_pattern = 'bui-campus_generic_hyp-%d_%s_%d'%(activity_index,ratio, i)
				generate_problem_for_activity_1( exp_file_pattern, chance_for_random_movement, ratio )
			if activity_index == 1 :
				exp_file_pattern = 'bui-campus_generic_hyp-%d_%s_%d'%(activity_index,ratio, i)
				generate_problem_for_activity_2( exp_file_pattern, chance_for_random_movement, ratio )
			i += 1

if __name__ == "__main__" :
	main()
