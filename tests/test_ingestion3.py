import pdfplumber

with pdfplumber.open("tests/Cahier_de_recette_L3S.pdf") as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        print(f"\n--- Page {i} ---")
        
        # Tableaux
        tables = page.extract_tables()
        print(f"Tableaux : {len(tables)}")
        
        # Texte
        texte = page.extract_text() or ""
        print(f"Longueur texte : {len(texte)}")
        
        # Images
        print(f"Nombre d'images : {len(page.images)}")
        for j, img in enumerate(page.images):
            print(f"  Image {j+1} : width={img.get('width')}, height={img.get('height')}, name={img.get('name')}")
        
        # Colonnes
        words = page.extract_words()
        print(f"Nombre de mots : {len(words)}")
        
import pdfplumber

with pdfplumber.open("tests/Cahier_de_recette_L3S.pdf") as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        words = page.extract_words()
        
        positions_x = [w["x0"] for w in words]
        x_min = min(positions_x)
        x_max = max(positions_x)
        largeur = x_max - x_min
        moitie = x_min + largeur / 2
        
        mots_gauche = sum(1 for x in positions_x if x < moitie)
        mots_droite = sum(1 for x in positions_x if x >= moitie)
        
        ratio = min(mots_gauche, mots_droite) / max(mots_gauche, mots_droite)
        
        print(f"x_min={x_min:.1f}, x_max={x_max:.1f}")
        print(f"mots_gauche={mots_gauche}, mots_droite={mots_droite}")
        print(f"ratio={ratio:.2f}")
        print(f"Est en colonnes : {ratio > 0.3}")