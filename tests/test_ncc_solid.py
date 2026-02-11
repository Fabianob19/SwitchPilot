import cv2
import numpy as np

def test_ncc(val1, val2):
    print(f"Testing NCC with solid colors: {val1} vs {val2}")
    img1 = np.full((128, 128), val1, dtype=np.uint8)
    img2 = np.full((128, 128), val2, dtype=np.uint8)
    
    try:
        res = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        print(f"Result shape: {res.shape}")
        if res.size > 0:
            print(f"Value: {res[0][0]}")
        else:
            print("Empty result")
    except Exception as e:
        print(f"Exception: {e}")

print("--- Same Color (100) ---")
test_ncc(100, 100)

print("\n--- Different Colors (100 vs 200) ---")
test_ncc(100, 200)

print("\n--- Normal Noise vs Normal Noise ---")
img1 = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
img2 = img1.copy()
res = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
print(f"Noise Match: {res[0][0]}")
