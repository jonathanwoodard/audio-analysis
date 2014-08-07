Audiomatch
==============================
Audiomatch allows users to select audio files (currently only supports .wav files) that are then fingerprinted. Audiomatch then attempts to match (as closely as possible) the audio fingerprints to realtime audio input through a microphone.

Python Version: 2.7

###Dependencies
==============================
PyAudio (v0.2.8): 
Website - http://people.csail.mit.edu/hubert/pyaudio/
Python Package Index - https://pypi.python.org/pypi/PyAudio
```pip install Pyaudio```

Numpy (v1.8.1):
Website - http://www.numpy.org/
Python Package Index - https://pypi.python.org/pypi/numpy/1.8.1
```pip install Numpy```

MatPlotLib (v1.3.1):
Website - http://matplotlib.org/
Python Package Index - https://pypi.python.org/pypi/matplotlib/1.3.1
```pip install Matplotlib```


###Usage
==============================
1. Run the _audiomatch.py_ Python script in the terminal
2. Using the GUI, add a .wav file to match in realtime audio (Label, File Selection, and Category)
3. Press the "Add File" button, feel free to add more files to match (unlimited number)
3. (Optional) Enter your own values in each of the _options_ input boxes
4. Press the "Analyze" Button to begin fingerprinting and matching


###How It Works
==============================
1. User Selects Audio File (.wav) to be matched in realtime audio and gives it a label and category
2. The file and its attached label and category are added to a list of all of the files to analyze
3. When the analysis is started, the software produces a fingerprint of each audio file using Fast Fourier Transforms (FFT's) and stores that fingerprint
4. The microphone is then used to capture realtime audio and produce fingerprints for each slice of the realtime stream
5. The fingerprints for each of the sound files to search for in the realtime audio and the realtime audio's fingerprint are run through a Linear Least-Squares Minimization to best-match each file to the realtime sound and produce a result displaying how much of each sound was present in the realtime audio.


###The Interface
==============================
When the script runs, a TK GUI appears prompting the user to add at least one .wav file containing sounds to match in realtime audio, and has several options to modify how the program analyzes the audio and matches it. If left empty, each option will fallback to a set default. A description of each option is below:

**SampleTime** - The amount of time (in seconds) that the script will sample realtime audio to fingerprint for. Default: 4 Seconds

**Repeat Analysis** - The number of times the program will sample realtime audio, fingerprint it, and scan the fingerprint for the amount of sound from each sound file that is present in the sample. Default: 5 Times

**Frequency Bands** - An entry to limit the frequency bands the program will scan in the realtime sample. For example, if you know a sound you are trying to match is typically between 300 and 500 Hertz, you can enter 300-500 to search only in that band, durastically reducing the time the program takes to scan a sample of realtime audio for matches.


