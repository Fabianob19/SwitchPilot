import cv2
import numpy as np
import requests
import mss
import time
import xml.etree.ElementTree as ET

REFERENCE_IMAGE = "fora_do_ar.png"
VMIX_API_URL_BASE = "http://localhost:8088/api"

def get_vmix_inputs():
    try:
        resp = requests.get(VMIX_API_URL_BASE)
        root = ET.fromstring(resp.content)
        entradas = []
        for input_elem in root.findall(".//inputs/input"):
            entradas.append(input_elem.attrib["title"])
        return entradas
    except Exception as e:
        print("Erro ao buscar entradas do vMix:", e)
        return []

def is_off_air(frame, reference_image_path, threshold=0.90):
    ref = cv2.imread(reference_image_path)
    if ref is None:
        print("Imagem de referência não encontrada!")
        return False
    frame_resized = cv2.resize(frame, (ref.shape[1], ref.shape[0]))
    # Converter para tons de cinza
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
    # Calcular histogramas
    hist_ref = cv2.calcHist([ref_gray], [0], None, [256], [0, 256])
    hist_frame = cv2.calcHist([frame_gray], [0], None, [256], [0, 256])
    # Normalizar
    hist_ref = cv2.normalize(hist_ref, hist_ref).flatten()
    hist_frame = cv2.normalize(hist_frame, hist_frame).flatten()
    # Comparar histogramas (correlação)
    similarity = cv2.compareHist(hist_ref, hist_frame, cv2.HISTCMP_CORREL)
    print(f"Similaridade (histograma): {similarity:.2f}")
    cv2.imshow("Frame capturado", frame_resized)
    cv2.waitKey(1)
    return similarity > threshold

def capture_screen(region):
    with mss.mss() as sct:
        img = np.array(sct.grab(region))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def main():
    entradas = get_vmix_inputs()
    if not entradas:
        print("Nenhuma entrada encontrada no vMix. Verifique se o vMix está aberto e a API ativada.")
        return

    print("Entradas disponíveis no vMix:")
    for idx, entrada in enumerate(entradas):
        print(f"{idx}: {entrada}")

    while True:
        try:
            indice = int(input("Digite o número da entrada que deseja usar quando detectar 'fora do ar': "))
            if 0 <= indice < len(entradas):
                break
            else:
                print("Índice inválido. Tente novamente.")
        except ValueError:
            print("Digite um número válido.")

    entrada_padrao = entradas[indice]
    vmix_api_url_nome = f"{VMIX_API_URL_BASE}/?Function=CutDirect&Input={entrada_padrao}"
    vmix_api_url_numero = f"{VMIX_API_URL_BASE}/?Function=CutDirect&Input={indice+1}"

    print("\nAjuste a região do PGM na tela (em pixels).")
    print("Se não souber, use os valores padrão e ajuste depois.")
    try:
        top = int(input("Top (padrão 100): ") or 100)
        left = int(input("Left (padrão 100): ") or 100)
        width = int(input("Width (padrão 1280): ") or 1280)
        height = int(input("Height (padrão 720): ") or 720)
    except ValueError:
        print("Valor inválido, usando padrão.")
        top, left, width, height = 100, 100, 1280, 720

    region = {"top": top, "left": left, "width": width, "height": height}

    print("\nMonitorando o PGM... Pressione Ctrl+C para sair.")
    while True:
        try:
            frame = capture_screen(region)
            if is_off_air(frame, REFERENCE_IMAGE):
                print(f"Tela fora do ar detectada! Tentando cortar para a entrada: {entrada_padrao}")
                response_nome = requests.get(vmix_api_url_nome)
                print("Resposta da API (por nome):", response_nome.text)
                if '<status>OK</status>' not in response_nome.text:
                    print(f"Tentando cortar usando o número da entrada: {indice+1}")
                    response_numero = requests.get(vmix_api_url_numero)
                    print("Resposta da API (por número):", response_numero.text)
            else:
                print("Tudo normal no PGM.")
        except KeyboardInterrupt:
            print("\nEncerrando monitoramento.")
            break
        except Exception as e:
            print("Erro durante execução:", e)
            time.sleep(0.2)

if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...") 