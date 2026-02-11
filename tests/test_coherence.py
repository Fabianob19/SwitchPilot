import cv2
import numpy as np

def calculate_coherence_score(name, img):
    # Shift image by 1 pixel right and 1 pixel down
    rows, cols = img.shape
    M = np.float32([[1, 0, 1], [0, 1, 1]])
    shifted = cv2.warpAffine(img, M, (cols, rows))
    
    # Calculate NCC between original and shifted
    res = cv2.matchTemplate(img, shifted, cv2.TM_CCOEFF_NORMED)
    score = res[0][0]
    print(f"[{name}] Coherence Score (Shift 1px): {score:.3f}")
    return score

# 1. Solid Color (Coherence should be High)
img_solid = np.full((100, 100), 127, dtype=np.uint8)
calculate_coherence_score("Solid Grey", img_solid)

# 2. Random Noise (Coherence should be Low)
img_noise = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
calculate_coherence_score("Random Noise", img_noise)

# 3. Structured Shape (e.g., a circle/button) - Coherence should be Medium-High
img_struct = np.zeros((100, 100), dtype=np.uint8)
cv2.circle(img_struct, (50, 50), 30, 255, -1)
calculate_coherence_score("White Circle", img_struct)

# 4. Text-like pattern (High frequency but structured)
img_text = np.zeros((100, 100), dtype=np.uint8)
for i in range(0, 100, 10):
    cv2.line(img_text, (0, i), (100, i), 255, 1)
calculate_coherence_score("Grid Lines", img_text)
