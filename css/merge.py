import os
import re
import base64

# Funzione per convertire un font in base64
def font_to_base64(font_path):
    with open(font_path, "rb") as font_file:
        encoded_string = base64.b64encode(font_file.read()).decode('utf-8')
    return encoded_string

# Funzione per sostituire gli URL dei font con il codice base64
def replace_font_urls_with_base64(css_content, font_dir):
    # Trova tutti i riferimenti ai font
    font_urls = re.findall(r'url\(["\']?(.*?\.(?:ttf|woff|woff2|otf|eot))["\']?\)', css_content)
    
    for font_url in font_urls:
        # Trova il percorso completo del file di font
        font_path = os.path.join(font_dir, os.path.basename(font_url))
        if os.path.exists(font_path):
            # Converti il font in base64
            font_base64 = font_to_base64(font_path)
            # Determina il MIME type in base base al formato del font
            mime_type = {
                '.ttf': 'font/ttf',
                '.woff': 'font/woff',
                '.woff2': 'font/woff2',
                '.otf': 'font/otf',
                '.eot': 'application/vnd.ms-fontobject'
            }.get(os.path.splitext(font_url)[1], 'font/ttf')
            base64_url = f"url(data:{mime_type};base64,{font_base64})"
            css_content = css_content.replace(f'url("{font_url}")', base64_url)
            css_content = css_content.replace(f"url('{font_url}')", base64_url)
            css_content = css_content.replace(f"url({font_url})", base64_url)
    
    return css_content

# Funzione per elaborare i file CSS e rimuovere commenti e spazi
def process_file(file_path, font_dir=None):
    with open(file_path, 'r') as infile:
        content = infile.read()
    # Rimuove i commenti e gli spazi
    content = remove_css_comments_and_spaces(content)
    if font_dir:
        # Sostituisce gli URL dei font con il codice base64
        content = replace_font_urls_with_base64(content, font_dir)
    return content

# Funzione per rimuovere commenti e spazi dai file CSS
def remove_css_comments_and_spaces(css):
    # Rimuove i commenti multi-linea e a linea singola
    css = re.sub(r'(?<!:)\s*\/\*[\s\S]*?\*\/', '', css)
    css = re.sub(r'(?<!:)\s*//.*', '', css)
    
    # Trova tutte le stringhe e sostituiscile temporaneamente
    strings = re.findall(r'(".*?"|\'.*?\')', css)
    placeholders = [f'__PLACEHOLDER_{i}__' for i in range(len(strings))]
    
    for placeholder, string in zip(placeholders, strings):
        css = css.replace(string, placeholder)
    
    # Rimuove tutti gli spazi non necessari
    css = re.sub(r'\s+', ' ', css)
    
    # Ripristina le stringhe al loro stato originale
    for placeholder, string in zip(placeholders, strings):
        css = css.replace(placeholder, string)
    
    return css

# Funzione principale per unire i file CSS
def merge_css_files(source_dir, fonts_dir, output_file):
    with open(output_file, 'w') as outfile:
        # Prima parte: aggiungi i file CSS dalla cartella fonts con i font incorporati
        for root, dirs, files in os.walk(fonts_dir):
            for file in files:
                if file.endswith('.css'):
                    file_path = os.path.join(root, file)
                    print(f"Aggiungendo font da: {file_path}")
                    # Scrive il commento con il nome del file
                    outfile.write(f'/* {file} */\n')
                    # Scrive il contenuto del file con font incorporati
                    content = process_file(file_path, fonts_dir)
                    outfile.write(content + '\n')
        
        # Seconda parte: aggiungi il resto dei file CSS
        for root, dirs, files in os.walk(source_dir):
            # Ignora la directory 'fonts' durante l'iterazione principale
            if 'fonts' in dirs:
                dirs.remove('fonts')
            
            for file in files:
                # Ignora i file che iniziano con 'import-'
                if file.endswith('.css') and not file.startswith('import-'):
                    file_path = os.path.join(root, file)
                    print(f"Aggiungendo: {file_path}")
                    # Scrive il commento con il nome del file
                    outfile.write(f'/* {file} */\n')
                    # Scrive il contenuto del file
                    content = process_file(file_path)
                    outfile.write(content + '\n')

# Specifica le directory e il file di output
source_directory = 'css'
fonts_directory = os.path.join(source_directory, 'fonts')
output_file = 'ToneCSS.css'

merge_css_files(source_directory, fonts_directory, output_file)
