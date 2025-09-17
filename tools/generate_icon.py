import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PRIMARY_BG = (32, 34, 37, 255)   # #202225
ACCENT = (0, 122, 204, 255)      # #007acc
ACCENT_DARK = (0, 92, 164, 255)
ACCENT_LIGHT = (20, 152, 234, 255)
TEXT = (234, 238, 242, 255)

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PNG_PATH = os.path.join(ASSETS_DIR, 'LOGO.png')
ICO_PATH = os.path.join(ASSETS_DIR, 'ICONE.ico')


def _try_truetype(size: int) -> ImageFont.FreeTypeFont:
    """Tenta carregar uma fonte robusta (Windows) para o S.
    Cai para Arial/Default se não encontrar Segoe UI.
    """
    candidates = [
        'segoeuib.ttf',                 # Segoe UI Bold
        'segoeuiz.ttf',                 # Segoe UI Semibold Italic (fallback estiloso)
        'SegoeUI-Semibold.ttf',
        'arialbd.ttf',                  # Arial Bold
        'arial.ttf',
        'tahomabd.ttf',
        'tahoma.ttf',
    ]
    windir = os.environ.get('WINDIR', 'C:/Windows')
    font_dirs = [os.path.join(windir, 'Fonts'), os.getcwd()]
    for name in candidates:
        for base in font_dirs:
            path = os.path.join(base, name)
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        # também tenta só pelo nome (alguns ambientes resolvem via path do sistema)
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _draw_highlight(overlay: Image.Image, bbox: tuple, radius: int):
    """Desenha um brilho elíptico suave na parte superior esquerda."""
    ox, oy, ox2, oy2 = bbox
    iw, ih = overlay.size
    highlight = Image.new('RGBA', (iw, ih), (0, 0, 0, 0))
    d = ImageDraw.Draw(highlight)
    # elipse de brilho menor que o círculo e deslocada para cima/esquerda
    pad = radius // 3
    ellipse = (ox + pad, oy + pad, ox2 - pad, oy2 - pad)
    d.ellipse(ellipse, fill=(255, 255, 255, 34))
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=max(1, radius // 6)))
    overlay.alpha_composite(highlight)


def draw_logo(size: int = 512) -> Image.Image:
    """Desenha o logo no tamanho pedido com supersampling para nitidez."""
    scale = 4  # supersampling 4x para qualidade
    W = size * scale

    # canvas grande
    base = Image.new('RGBA', (W, W), PRIMARY_BG)

    # círculo/acento
    margin = int(W * 0.12)
    ring_width = max(4, int(W * 0.06))
    circle_bbox = (margin, margin, W - margin, W - margin)

    circle_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    dc = ImageDraw.Draw(circle_layer)

    if size <= 32:
        # Em tamanhos pequenos, preenchido para legibilidade
        dc.ellipse(circle_bbox, fill=ACCENT)
    else:
        # Preenchimento com leve gradiente (dark->light)
        dc.ellipse(circle_bbox, fill=ACCENT_DARK)
        inner = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        di = ImageDraw.Draw(inner)
        shrink = int(W * 0.04)
        inner_bbox = (margin + shrink, margin + shrink, W - margin - shrink, W - margin - shrink)
        di.ellipse(inner_bbox, fill=ACCENT_LIGHT)
        inner = inner.filter(ImageFilter.GaussianBlur(radius=max(2, W // 80)))
        circle_layer.alpha_composite(inner)
        # anel externo
        dc.ellipse(circle_bbox, outline=ACCENT_LIGHT, width=ring_width)
        # brilho superior
        _draw_highlight(circle_layer, circle_bbox, radius=max(4, W // 20))

    base.alpha_composite(circle_layer)

    # texto S
    text_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    dt = ImageDraw.Draw(text_layer)

    font_size = int(W * (0.58 if size >= 64 else (0.62 if size > 32 else 0.66)))
    font = _try_truetype(font_size)

    s_text = 'S'

    if size <= 32:
        # Centralização ótica: sem sombra/contorno e ancorado ao centro
        try:
            dt.text((W / 2, W / 2), s_text, font=font, fill=TEXT, anchor='mm')
        except TypeError:
            bbox = dt.textbbox((0, 0), s_text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (W - tw) / 2
            y = (W - th) / 2
            dt.text((x, y), s_text, font=font, fill=TEXT)
        base.alpha_composite(text_layer)
    else:
        # sombra + contorno leves para tamanhos médios/grandes
        bbox = dt.textbbox((0, 0), s_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (W - tw) / 2
        y = (W - th) / 2 - int(W * 0.02)

        shadow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        ds = ImageDraw.Draw(shadow)
        shadow_offset = max(1, W // 200)
        try:
            ds.text((x + shadow_offset, y + shadow_offset), s_text, font=font, fill=(0, 0, 0, 130),
                    stroke_width=max(1, W // 160), stroke_fill=(0, 0, 0, 160))
        except TypeError:
            ds.text((x + shadow_offset, y + shadow_offset), s_text, font=font, fill=(0, 0, 0, 130))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(1, W // 180)))

        try:
            dt.text((x, y), s_text, font=font, fill=TEXT,
                    stroke_width=max(1, W // 140), stroke_fill=(0, 0, 0, 90))
        except TypeError:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                dt.text((x + dx, y + dy), s_text, font=font, fill=(0, 0, 0, 120))
            dt.text((x, y), s_text, font=font, fill=TEXT)

        base.alpha_composite(shadow)
        base.alpha_composite(text_layer)

    # downscale com LANCZOS
    final_img = base.resize((size, size), Image.LANCZOS)
    return final_img


def main():
    # PNG grande para uso geral
    big = draw_logo(1024)
    big.save(PNG_PATH)

    # múltiplos tamanhos para .ico
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [draw_logo(s) for s in sizes]
    imgs[0].save(ICO_PATH, sizes=[(s, s) for s in sizes])
    print(f"Gerado: {PNG_PATH} e {ICO_PATH}")


if __name__ == '__main__':
    main()
