"""Create test files for forensic tool validation."""
import struct
import wave
import math
import numpy as np
from PIL import Image, ImageDraw

# PDF
import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), 'CrimeGPT Forensic Report\nCase: FIR/2024/TEST\nEvidence collected at crime scene.\nSuspect identified via CCTV footage.')
doc.save('/tmp/test.pdf')
doc.close()
print('PDF created')

# Image with text
img = Image.new('RGB', (400, 300), 'white')
draw = ImageDraw.Draw(img)
draw.text((20, 20), 'Crime Scene Photo\nLocation: Delhi')
draw.rectangle([100, 100, 300, 250], outline='red', width=3)
draw.text((110, 120), 'EVIDENCE TAG 001', fill='red')
img.save('/tmp/test_image.png')
print('Image created')

# Fingerprint with ridge patterns
img_fp = np.zeros((300, 300), dtype=np.uint8)
for i in range(0, 300, 5):
    offset = int(20 * np.sin(i / 30.0))
    for j in range(300):
        if (j + offset) % 10 < 5:
            img_fp[i:min(i+3, 300), j] = 200
Image.fromarray(img_fp).save('/tmp/test_fingerprint.png')
print('Fingerprint created')

# DNA report
with open('/tmp/test_dna.txt', 'w') as f:
    f.write("""DNA Analysis Report
Laboratory: Central Forensic Science Laboratory, Delhi
Case: FIR/2024/001
Sample: Blood stain from crime scene

STR Profile:
D3S1358: 15/17
vWA: 16/18
FGA: 22/24
D8S1179: 12/14
D21S11: 29/31
D18S51: 14/16
D5S818: 11/13
D13S317: 9/12
D7S820: 10/11
TH01: 7/9.3
TPOX: 8/11
CSF1PO: 10/12
""")
print('DNA report created')

# Audio WAV (3 seconds of 440Hz tone)
sr = 16000
n = sr * 3
with wave.open('/tmp/test_audio.wav', 'w') as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sr)
    for i in range(n):
        v = int(16000 * math.sin(2 * math.pi * 440 * i / sr))
        f.writeframes(struct.pack('<h', v))
print('Audio WAV created')

print('\nAll test files ready at /tmp/')
