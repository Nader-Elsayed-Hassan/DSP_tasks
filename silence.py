import librosa
import soundfile as sf

audio, sr = librosa.load("clean_audio.wav", sr=None)
audio_trimmed, _ = librosa.effects.trim(audio, top_db=20)
sf.write("no_silence.wav", audio_trimmed, sr)
print("Silence removed")