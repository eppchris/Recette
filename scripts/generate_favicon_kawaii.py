#!/usr/bin/env python3
"""
Générateur de favicon avec marmite kawaii
Usage: python scripts/generate_favicon_kawaii.py
"""

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def generate_kawaii_pot_favicon():
    """Génère un favicon avec marmite kawaii"""
    size = 64

    # Créer image avec fond transparent
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Couleurs
    pot_color = (232, 93, 93)  # Rouge-orange
    pot_dark = (199, 69, 69)   # Rouge foncé
    lid_color = (240, 240, 240)  # Gris clair
    dark_outline = (44, 62, 80)  # Gris foncé
    white = (255, 255, 255)
    pink_cheeks = (255, 153, 153)

    # Corps de la marmite
    draw.rounded_rectangle([16, 32, 48, 52], radius=5, fill=pot_color, outline=dark_outline, width=2)

    # Poignées
    draw.arc([8, 34, 16, 42], 90, 270, fill=dark_outline, width=2)
    draw.arc([48, 34, 56, 42], 270, 90, fill=dark_outline, width=2)

    # Couvercle
    draw.ellipse([14, 28, 50, 36], fill=lid_color, outline=dark_outline, width=2)

    # Poignée du couvercle
    draw.ellipse([28, 24, 36, 28], fill=lid_color, outline=dark_outline, width=1)
    draw.ellipse([30, 22, 34, 26], fill=lid_color, outline=dark_outline, width=1)

    # Visage kawaii
    # Yeux fermés (petites courbes)
    draw.arc([22, 38, 26, 42], 0, 180, fill=white, width=2)
    draw.arc([38, 38, 42, 42], 0, 180, fill=white, width=2)

    # Bouche souriante
    draw.arc([26, 42, 38, 48], 180, 360, fill=white, width=2)

    # Joues roses
    draw.ellipse([20, 44, 24, 48], fill=pink_cheeks)
    draw.ellipse([40, 44, 44, 48], fill=pink_cheeks)

    # Vapeur (petits cercles au-dessus)
    draw.ellipse([30, 16, 34, 20], fill=(white[0], white[1], white[2], 180))
    draw.ellipse([28, 12, 31, 15], fill=(white[0], white[1], white[2], 150))
    draw.ellipse([33, 12, 36, 15], fill=(white[0], white[1], white[2], 150))
    draw.ellipse([30, 8, 33, 11], fill=(white[0], white[1], white[2], 120))

    # Sauvegarder en différentes tailles
    img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save('static/favicon-32x32.png')
    print("✅ Créé: static/favicon-32x32.png")

    img_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
    img_16.save('static/favicon-16x16.png')
    print("✅ Créé: static/favicon-16x16.png")

    img.save('static/favicon-64x64.png')
    print("✅ Créé: static/favicon-64x64.png")

    # favicon.ico multi-tailles
    img.save('static/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (64, 64)])
    print("✅ Créé: static/favicon.ico")

    print("\n🎉 Favicon marmite kawaii créé avec succès !")
    print("   Marmite rouge avec visage souriant et vapeur")

if __name__ == "__main__":
    print("🍲 Générateur de favicon - Marmite Kawaii")
    print("=" * 50)
    print()

    if PIL_AVAILABLE:
        generate_kawaii_pot_favicon()
    else:
        print("⚠️  Pillow requis: pip install Pillow")
