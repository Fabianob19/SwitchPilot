import cv2
import mss
import numpy as np
import pyautogui

print("\nInstruções:")
print("1. Deixe a tela do PGM visível na sua área de trabalho.")
print("2. Quando solicitado, clique e arraste o mouse para selecionar a região do PGM.")
print("3. As coordenadas serão exibidas ao final.")
# input("\nPressione Enter para começar...")

# Captura a tela inteira
with mss.mss() as sct:
    monitor = sct.monitors[1]
    img = np.array(sct.grab(monitor))
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

# Função de callback para selecionar a região
ref_point = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    global ref_point, cropping
    if event == cv2.EVENT_LBUTTONDOWN:
        ref_point = [(x, y)]
        cropping = True
    elif event == cv2.EVENT_LBUTTONUP:
        ref_point.append((x, y))
        cropping = False
        cv2.rectangle(img, ref_point[0], ref_point[1], (0, 255, 0), 2)
        cv2.imshow("Selecione a região do PGM", img)

cv2.namedWindow("Selecione a região do PGM")
cv2.setMouseCallback("Selecione a região do PGM", click_and_crop)

while True:
    clone = img.copy()
    if len(ref_point) == 2:
        cv2.rectangle(clone, ref_point[0], ref_point[1], (0, 255, 0), 2)
    cv2.imshow("Selecione a região do PGM", clone)
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or len(ref_point) == 2:  # ESC ou seleção feita
        break

cv2.destroyAllWindows()

if len(ref_point) == 2:
    x1, y1 = ref_point[0]
    x2, y2 = ref_point[1]
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    resultado = f"Região selecionada:\ntop = {top}\nleft = {left}\nwidth = {width}\nheight = {height}"
    print(f"\n{resultado}")
    pyautogui.alert(resultado, title="Coordenadas capturadas")
else:
    print("Seleção não realizada.")
    pyautogui.alert("Seleção não realizada.", title="Coordenadas capturadas") 