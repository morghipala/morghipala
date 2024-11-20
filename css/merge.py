import os
import base64

# Funzione per convertire un file in base64
def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        file_content = file.read()
    return base64.b64encode(file_content).decode('utf-8')

# Funzione per unire i file CSS e sostituire le risorse con base64
def combine_and_convert_css(directories):
    combined_css = ""
    
    # Itera attraverso le directory fornite
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                # Ignora i file che iniziano con "import-"
                if file.startswith("import-"):
                    continue

                if file.endswith('.css'):
                    file_path = os.path.join(root, file)
                    print(f"Elaborando: {file_path}")
                    
                    with open(file_path, 'r') as f:
                        css_content = f.read()
                        # Sostituisce i riferimenti a file o URL (immagini, font) con base64
                        css_content = convert_references_to_base64(css_content, root)
                        combined_css += css_content + "\n"
    
    return combined_css

# Funzione per convertire i riferimenti (immagini, font) a base64 nel contenuto CSS
def convert_references_to_base64(css_content, css_root):
    # Cerca gli URL delle immagini o dei font nel CSS
    import re
    
    # Espressione regolare per trovare gli URL
    url_pattern = re.compile(r'url\((["\']?)([^"\']+)\1\)')
    
    # Sostituisce ogni URL con il contenuto in base64
    def replace_with_base64(match):
        file_url = match.group(2)
        file_path = os.path.join(css_root, file_url)
        
        if os.path.exists(file_path):
            base64_content = file_to_base64(file_path)
            file_extension = os.path.splitext(file_url)[1].lower()
            
            if file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                mime_type = f'image/{file_extension[1:]}'
            elif file_extension in ['.woff', '.woff2', '.ttf', '.otf']:
                mime_type = f'font/{file_extension[1:]}'
            else:
                mime_type = 'application/octet-stream'
            
            # Aggiungi le virgolette ai dati base64
            return f'url("data:{mime_type};base64,{base64_content}")'
        else:
            return match.group(0)
    
    return url_pattern.sub(replace_with_base64, css_content)

# Percorsi delle sottocartelle da elaborare
css_directories = ['./css/fonts', './css/Material/css', './css/components']

# Unisce i file CSS e converte i riferimenti in base64
combined_css = combine_and_convert_css(css_directories)

# Salva il CSS combinato in un nuovo file
with open('ToneCSS.css', 'w') as output_file:
    output_file.write(combined_css)

print("Unione dei file CSS completata e salvataggio effettuato in 'combined_styles.css'.")
