import librosa
import noisereduce as nr
import soundfile as sf

audio, sr = librosa.load("DSP_task.wav", sr=None)
reduced_noise = nr.reduce_noise(y=audio, sr=sr)
sf.write("clean_audio.wav", reduced_noise, sr)
print("Noise removed successfully")