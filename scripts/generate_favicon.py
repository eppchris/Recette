#!/usr/bin/env python3
"""
Générateur de favicon avec emoji chef 👨‍🍳
Usage: python scripts/generate_favicon.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL/Pillow n'est pas installé")
    print("Installation: pip install Pillow")

def generate_favicon_with_pil():
    """Génère un favicon avec PIL si disponible"""
    # Créer une image 64x64 avec fond blanc
    size = 64
    img = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Dessiner une toque de chef simplifiée
    # Toque (cercle blanc en haut)
    draw.ellipse([12, 8, 52, 28], fill=(240, 240, 240), outline=(51, 51, 51), width=2)

    # Base de la toque (rectangle)
    draw.rectangle([12, 20, 52, 38], fill=(255, 255, 255), outline=(51, 51, 51), width=2)

    # Bande noire
    draw.rectangle([12, 34, 52, 40], fill=(51, 51, 51))

    # Visage (cercle chair)
    draw.ellipse([20, 40, 44, 64], fill=(253, 213, 177))

    # Yeux
    draw.ellipse([26, 48, 30, 52], fill=(51, 51, 51))
    draw.ellipse([34, 48, 38, 52], fill=(51, 51, 51))

    # Sourire
    draw.arc([24, 52, 40, 62], 0, 180, fill=(51, 51, 51), width=2)

    # Sauvegarder en différentes tailles
    # 32x32 pour favicon classique
    img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save('static/favicon-32x32.png')
    print("✅ Créé: static/favicon-32x32.png")

    # 16x16 pour petit favicon
    img_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
    img_16.save('static/favicon-16x16.png')
    print("✅ Créé: static/favicon-16x16.png")

    # 64x64 original
    img.save('static/favicon-64x64.png')
    print("✅ Créé: static/favicon-64x64.png")

    # Créer favicon.ico multi-tailles
    img.save('static/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (64, 64)])
    print("✅ Créé: static/favicon.ico")

    print("\n🎉 Favicons générés avec succès !")
    print("\nFichiers créés:")
    print("  - static/favicon.ico (multi-tailles)")
    print("  - static/favicon-16x16.png")
    print("  - static/favicon-32x32.png")
    print("  - static/favicon-64x64.png")

def generate_simple_text_favicon():
    """Génère un favicon texte simple sans PIL"""
    print("⚠️  Mode simple sans PIL")
    print("\nPour générer un favicon avec l'emoji chef 👨‍🍳:")
    print("\n1. Ouvrez: static/favicon-emoji.html dans votre navigateur")
    print("2. Le favicon.ico sera téléchargé automatiquement")
    print("3. Placez-le dans static/favicon.ico")
    print("\nOu installez Pillow: pip install Pillow")

if __name__ == "__main__":
    print("🎨 Générateur de favicon - Chef 👨‍🍳")
    print("=" * 50)
    print()

    if PIL_AVAILABLE:
        generate_favicon_with_pil()
    else:
        generate_simple_text_favicon()
