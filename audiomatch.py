'''

An audio analysis program that produces fingerprints of training audio files, then matches
the fingerprints to realtime audio.

Primary Author: Will Haering
Date: 8/6/14
Version 1.0
Python Version: 2.7

Sections:
1: TK GUI setup
2: Global Variable Definitions
3: Functions

'''

# You may need to download PyAudio and SciPy, all else is bundled with Python
import ttk
import Tkinter as tk
import tkFileDialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np
import math
import struct
import wave
from sys import stdout
import pyaudio


# ======================== Section 1 ========================
# TK GUI
master = tk.Tk()
master.title("Audio Analysis and Matching")



# TK Variables
# file_label_entry_var = tk.StringVar()


# file_category_entry_var = tk.StringVar()


file_text = tk.StringVar()
file_text.set("Please Select a file...")

result = tk.StringVar()
result.set("Click Analyze after choosing files to begin")

analysis_label = 			tk.Label(text="Choose Files and Analyze:")
file_label_entry_label = 	tk.Label(master, text="Enter a File Label: ")
file_label_entry = 			tk.Entry(master, width=50)
file_selection_label = 		tk.Label(master, text="Choose Training File(s): ")
file_path_display = 		tk.Label(master, textvariable=file_text, fg="red")
file_category_entry_label = tk.Label(master, text="File Category: ")
file_category_entry = 		tk.Entry(master, width=50)
options_label = 			tk.Label(master, text="Options (Leave Blank for Program Defaults): ")
run_times_entry_label = 	tk.Label(master, text="Repeat Analysis (# Times): ")
run_times_entry = 			tk.Entry(master, width=20)
sample_time_entry_label = 	tk.Label(master, text="Sample Time (sec): ")
sample_time_entry = 		tk.Entry(master, width=20)
bands_entry_desc_label = 	tk.Label(master, text="Frequency Bands to Analyze on (Format: 100-200, 320-600): ")
bands_entry_label = 		tk.Label(master, text="Enter Frequency Bands: ")
bands_entry = 				tk.Entry(master, width=50)
results =					tk.Label(master, textvariable=result)

# GUI uses grid geometry manager
analysis_label.grid(			sticky=tk.W, row=0, column=0, columnspan=3, padx=10, pady=10)
file_label_entry_label.grid(	sticky=tk.W, row=1, column=0, padx=10, pady=10)
file_label_entry.grid(			sticky=tk.E, row=1, column=1, columnspan=2, padx=10)
file_selection_label.grid(		sticky=tk.W, row=2, column=0, padx=10, pady=10)
file_path_display.grid(			sticky=tk.W, row=2, column=1, padx=10, pady=10)
file_category_entry_label.grid(	sticky=tk.W, row=3, column=0, padx=10, pady=10)
file_category_entry.grid(		sticky=tk.E, row=3, column=1, columnspan=2, padx=10)
options_label.grid(				sticky=tk.W, row=4, column=0, columnspan=3, padx=10, pady=10)
run_times_entry_label.grid(		sticky=tk.W, row=6, column=0, padx=10, pady=10)
run_times_entry.grid(			sticky=tk.W, row=6, column=1, columnspan=2, padx=10)
sample_time_entry_label.grid(	sticky=tk.W, row=5, column=0, padx=10, pady=10)
sample_time_entry.grid(			sticky=tk.W, row=5, column=1, columnspan=2, padx=10)
bands_entry_desc_label.grid(	sticky=tk.W, row=7, column=0, columnspan=3, padx=10, pady=10)
bands_entry_label.grid(			sticky=tk.W, row=8, column=0, padx=10, pady=10)
bands_entry.grid(				sticky=tk.W, row=8, column=1, columnspan=2, padx=10)
results.grid(					sticky=tk.W, row=9, column=1, columnspan=2, padx=10)


# Figure is shown after analysis (Graph)
figure = Figure(figsize=(8,4), dpi=80)

# ======================== Section 2 ========================
# Program Global Variables
file_dict = {} 				# {<File Label String>: {'path':<File Path String>, 'category':<File Category String>}}
chunk_length = 16384 		# Power of 2, Larger equals more resolution but larger analysis chunks
record_rate = 48000 		# Bitrate of audio from microphone: bits/second
record_channels = 1			# 2 Channels is not compatible yet 
record_time = 4 			# In seconds
repeat_analysis_times = 5 	# Number of times to repeat analysis
bands_array = []			# Empty array for frequency bands over which to analyze
							# [[Bandmin1, Bandmax1], [Bandmin2, Bandmax2], ...]
							# No Check yet on band overlap


# ======================== Section 3 ========================
# Functions

def chooseFile():
	'''Button Handler for "Choose File" Button that opens a file selection dialog and gets the path of a
	user-selected file and displays it.'''
	file_path = tkFileDialog.askopenfilename() # open file dialog
	file_text.set(file_path)
	file_path_display.config(fg='green')
	print(file_path)


def addFile():
	'''Button Handler for "Add File" Button that adds the file and its information to "file_dict"'''
	file_path = file_text.get()
	file_text.set('')
	file_label = file_label_entry.get()
	file_label_entry.delete(0, 1000)
	file_category_entry.delete(0, 1000)
	file_category = file_category_entry.get()

	if file_path:
		if file_label:
			file_dict[file_label] = {'path':file_path,'category':file_category} # Add Bitrate
			print(file_dict)


def buttonAnalyzeCallback():
	'''Button Handler for "Analyze" Button that parses user-inputted bands into an 
	array and runs the "solveForAudioProportions" function, which fingerprints then analyzes 
	the trainging files and realtime audio.
	*GUI Dies when this is called*'''
	
	global bands_array, record_time, repeat_analysis_times
	# Input Validation
	bands_array = []
	
	if len(sample_time_entry.get()) == 0:
		record_time = 4
	else:
		record_time = int(sample_time_entry.get())

	if len(run_times_entry.get()) == 0:
		repeat_analysis_times = 2
	else:
		repeat_analysis_times = int(run_times_entry.get())
	
	# Get entered bands over which to analyze
	makeBandsArray(bands_entry.get())
	
	# Fingerprint training files and column stack them
	fingerprint_array = np.column_stack(getTrainingFileFingerprints())

	# Run realtime analysis
	for i in range(repeat_analysis_times):
		fft_frequencies_hz, fingerprint_realtime = realtimeRecordAndFingerprint()
		# sound_profile, Residuals, Rank, S = np.linalg.lstsq(fingerprint_array, fingerprint_realtime)
		sound_profile = np.linalg.lstsq(fingerprint_array, fingerprint_realtime)[0]
		print(sound_profile)
		result.set("Results: " + str(sound_profile))

	# Graph last instance
	graph(fft_frequencies_hz, np.transpose(fingerprint_array), fingerprint_realtime, sound_profile)


def makeBandsArray(entered_bands):
	'''Parses user entered bands into formatted array, if no bands are entered, it uses a default band'''
	global bands_array
	if len(entered_bands) == 0:
		bands_array = [[100, 1000]]
	else:
		bands = entered_bands.replace(" ", "").split(',')
		for band in bands:
			bands_array.append(band.split('-'))
			for i in range(0, len(bands_array)):
				bands_array[i][:] = [int(x) for x in bands_array[i]]


def getTrainingFileFingerprints():
	num_files = len(file_dict)
	fingerprint_array = ()
	for file_label in file_dict:
		fingerprint = abs(fingerprintTeachingFile(file_dict[file_label]['path']))
		fingerprint_array = fingerprint_array + (fingerprint,)
	return fingerprint_array


def clearFiles():
	'''Empties Training File Info/Path dictionary to allow a different set of 
	files to be used'''
	file_dict.clear()


def initializeButtons():
	'''Initializes TK buttons in Master'''
	button_analyze = tk.Button(master, text = "Analyze", width=10, command = buttonAnalyzeCallback)
	button_analyze.grid(row=9, column=3, padx=5, pady=10)

	button_choose = tk.Button(master, text = "Choose File", width = 10, command = chooseFile)
	button_choose.grid(row=2, column=3, padx=10, sticky=tk.E)

	button_add = tk.Button(master, text = "Add File", width = 10, command = addFile)
	button_add.grid(row=3, column=3, padx=10, sticky=tk.E)

	button_remove = tk.Button(master, text = "Remove All Files", width = 15, command = clearFiles)
	button_remove.grid(row=9, column=0, padx=5, pady=10, sticky=tk.W)


def getRMS(data):
	'''Gets Root Mean Square of raw signal data from either training files
	or realtime microphone input
	*Currently Unused* - Potentially useful for normalization'''
	count = len(data)/2
	format = "%dh"%(count)
	shorts = struct.unpack(format, data)
	shorts = np.array(shorts)
	rms = np.sqrt(np.mean(shorts**2))
	print(str(np.log(rms)/np.log(20)) + "Db")
	

def getChunkFFT(data, chunk_length, num_channels):
	'''Given raw chunk data from either training files or realtime microphone input
	this runs an FFT on the frames of the chunk (Number of frames per chunk = chunk_length),
	then returns a Numpy Array of the FFT values'''
	data = struct.unpack('{n}h'.format(n=chunk_length*num_channels), data)
	data = np.array(data)
	fft_values = np.fft.fft(data)[0:chunk_length]
	return (fft_values)


def getBands(fft_frequencies_hz, chunk_frequencies):
	'''Using user entered frequency bands from "bands_array" this finds the indices of the band's minimum and
	maximum value, then slices the band out from the rest of the data. Uses "fft_frequencies_hz" to
	find the indices of the band's minimum and maximum from the user inputted values, then because each
	value in "fft_frequencies_hz" corresponds to a value in "chunk_frequencies" (thus corresponding indices),
	the band min and max values obtained are used to slice out bands from both arrays. Works for any number
	of frequency bands in "bands_array".'''
	num_bands = len(bands_array)
	fft_frequencies_bands_array = []
	chunk_bands_array = []
	print("Bands Shown:")
	for i in range(0, num_bands):
		band_min = bands_array[i][0]
		band_max = bands_array[i][1]
		band_min_index = np.amin(np.where(fft_frequencies_hz >= band_min))	
		band_max_index = np.amax(np.where(fft_frequencies_hz <= band_max))
		print("Band: " + str(band_min) + "-" + str(band_max) + " : " + str(band_max_index+1-band_min_index))

		fft_frequencies_bands_array.append(fft_frequencies_hz[band_min_index:band_max_index+1])
		chunk_bands_array.append(chunk_frequencies[band_min_index:band_max_index+1, :])

	fft_frequencies_bands = np.concatenate(tuple(fft_frequencies_bands_array))
	chunk_bands = np.concatenate(tuple(chunk_bands_array))
	return fft_frequencies_bands, chunk_bands
	

def fingerprintTeachingFile(wavepath):
	''' Finds the FFT Frequencies represented in the data using Numpy's fftfreq() function 
	and the length of a chunk. Then it calculates the total number of chunks in the 
	.wav file to be read, based on "chunk_length" and the total number of samples in the .wav file.
	Loops through the entire .wav file, chunk by chunk (Length of chunk = "chunk_length"), and gets the
	FFT values for each chunk from the "getChunkFFT" function above. Each chunk's FFT values is stored 
	in the 2-Dimensional array "chunk_frequencies", which is then sliced into bands using the "getBands"
	function above. The 2-Dimensional array "chunk_frequencies" is returned with only the frequency band values,
	with all other values discarded. This array is then sorted along its second axis (horizontal), and the
	50th percentile chunk values are returned.'''
	f = wave.open(wavepath,"r")
	num_samples = f.getnframes()
	num_channels = f.getnchannels()
	rate = f.getframerate()
	num_chunks = num_samples/chunk_length # Cuts remainder when it casts to int
	print("Number of Chunks: ", num_chunks)
	fft_frequencies = np.fft.fftfreq(chunk_length*2)[0:chunk_length/2]
	fft_frequencies_hz = fft_frequencies*rate # Convert to HZ = abs(fft frequency * frame rate)
	chunk_frequencies = np.zeros((chunk_length, num_chunks))
	for i in range(0, num_chunks):
		data = f.readframes(chunk_length)
		chunk_frequencies[:, i] = getChunkFFT(data, chunk_length, num_channels)
		stdout.write("Fingerprinting Audio Files... " + str(100*i/num_chunks) + "%\r")
		stdout.flush()
	print("100% - Done")
	fft_frequencies_hz, chunk_frequencies = getBands(fft_frequencies_hz, chunk_frequencies)
	chunk_frequencies.sort(axis=1)
	return (chunk_frequencies[:, int(.5*num_chunks)])


def realtimeRecordAndFingerprint():
	''' Finds the FFT Frequencies represented in the data using Numpy's fftfreq() function 
	and the length of a chunk. Then it calculates the total number of chunks to read from the microphone
	using the Sample rate (48000), "chunk_length", and the amount of time to sample for (user-inputted).
	It then runs a loop and records and and gets the FFT values for each chunk from the "getChunkFFT"
	Each chunk's FFT values are stored in the 2-Dimensional array "chunk_frequencies", which is then sliced 
	into bands using the "getBands" function above. The 2-Dimensional array "chunk_frequencies" is 
	returned with only the frequency band values, with all other values discarded. This array is then 
	sorted along its second axis (horizontal), and the 50th percentile chunk values are returned.'''
	num_chunks = record_rate / chunk_length * record_time
	fft_frequencies = np.fft.fftfreq(chunk_length*2)[0:chunk_length/2]
	fft_frequencies_hz = fft_frequencies*record_rate
	p = pyaudio.PyAudio()
	mic_stream = p.open(format = pyaudio.paInt16,
	channels = record_channels, 
	rate = record_rate,
	input = True,
	output = True,
	frames_per_buffer = chunk_length)
	chunk_frequencies = np.zeros((chunk_length, num_chunks))
	
	for i in range(0, num_chunks):
		data = mic_stream.read(chunk_length)
		chunk_frequencies[:, i] = getChunkFFT(data, chunk_length, record_channels)
		stdout.write("Sampling Audio... " + str(100*i/num_chunks) + "%\r")
		stdout.flush()


	fft_frequencies_hz, chunk_frequencies = getBands(fft_frequencies_hz, chunk_frequencies)
	return (fft_frequencies_hz, abs(chunk_frequencies[:, int(.5*num_chunks)]))


def graph(fft_frequencies_hz, fingerprint_array, fingerprint_realtime, sound_profile):
	'''Given fft_frequencies_hz (X-axis), the array of FFT values from all the processed training files,
	the array of FFT values from the realtime audio, and the array of Linear minimization values ("sound_profile"),
	this graphs the realtime audio FFT values against the training files FFT values, which have been scaled by the
	Linear minimization values for each training file to show how similar the audio recorded was to 
	each of the individual training files'''
	figure.clf()
	axis = figure.add_subplot(1,1,1)
	axis.set_xscale('log')
	axis.set_yscale('log')
	axis.set_title('Frequency Graph From Last Analysis')
	axis.set_xlabel('Frequencies (Hz)')
	axis.set_ylabel('Amplitude')

	for i in range(0, len(fingerprint_array)):
		axis.plot(fft_frequencies_hz, fingerprint_array[i]*sound_profile[i], '.')

	axis.plot(fft_frequencies_hz, fingerprint_realtime, 'r.')
	canvas = FigureCanvasTkAgg(figure, master=master)
	canvas.show()
	canvas.get_tk_widget().grid(row=10, column=0, columnspan=5, padx=0, pady=20)


initializeButtons()
tk.mainloop()











