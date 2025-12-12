#!/usr/bin/env python3
"""
Générateur de favicon moderne avec lettre R
Usage: python scripts/generate_favicon_v2.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def generate_modern_favicon():
    """Génère un favicon moderne avec lettre R"""
    size = 64

    # Créer image avec transparence
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dessiner cercle dégradé (simulé avec couleur unie)
    circle_color = (255, 107, 107)  # Rouge-orange
    draw.ellipse([2, 2, size-2, size-2], fill=circle_color)

    # Essayer de charger une belle police, sinon utiliser par défaut
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        except:
            font = ImageFont.load_default()

    # Dessiner la lettre R centrée
    text = "R"
    # Calculer position pour centrer
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Petit point décoratif
    draw.ellipse([48, 14, 54, 20], fill=(255, 255, 255, 230))

    # Sauvegarder en différentes tailles
    img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save('static/favicon-32x32.png')
    print("✅ Créé: static/favicon-32x32.png")

    img_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
    img_16.save('static/favicon-16x16.png')
    print("✅ Créé: static/favicon-16x16.png")

    img.save('static/favicon-64x64.png')
    print("✅ Créé: static/favicon-64x64.png")

    img.save('static/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (64, 64)])
    print("✅ Créé: static/favicon.ico")

    print("\n🎉 Nouveau favicon moderne créé !")
    print("   Lettre R sur fond rouge-orange")

if __name__ == "__main__":
    print("🎨 Générateur de favicon - Version 2")
    print("=" * 50)
    print()

    if PIL_AVAILABLE:
        generate_modern_favicon()
    else:
        print("⚠️  Pillow requis: pip install Pillow")
