import kokoro_onnx, numpy as np, soundfile as sf

k = kokoro_onnx.Kokoro('backend/voice/models/kokoro-v1.0.onnx', 'backend/voice/models/voices-v1.0.bin')

s_liam = k.get_voice_style('am_liam')
s_psi = k.get_voice_style('hm_psi')
s_adam = k.get_voice_style('am_adam')
s_echo = k.get_voice_style('am_echo')

# Tailor exact founder blend: 50% am_liam (youthful, energetic) + 35% hm_psi (Indian accent/cadence) + 15% am_adam (clear projection)
custom_founder = (0.50 * s_liam + 0.35 * s_psi + 0.15 * s_adam).astype(np.float32)
np.save('backend/voice/clones/my_voice_style.npy', custom_founder)

test_text = "Hey Priya! Our hoodies start at 1499 for the AK Don's Edition, and 1599 for the Kismat cracked hoodie. Which color are you looking for?"

samples, sr = k.create(test_text, voice=custom_founder, speed=1.06, lang='en-us')
sf.write('backend/voice/clones/test_custom_founder_youthful.wav', samples, sr)
print(f"Generated {len(samples)} samples ({len(samples)/sr:.2f}s) in test_custom_founder_youthful.wav")
