import os
import re

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

def process_file(file_path):
    with open(file_path, 'r') as infile:
        content = infile.read()
    # Rimuove i commenti e gli spazi
    content = remove_css_comments_and_spaces(content)
    return content

def merge_css_files(source_dir, output_file):
    with open(output_file, 'w') as outfile:
        for root, dirs, files in os.walk(source_dir):
            # Ignora la directory 'Poppins'
            if 'Poppins' in dirs:
                dirs.remove('Poppins')
            
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

# Specifica la sottodirectory e il file di output
source_directory = 'css'
output_file = 'merged.css'

merge_css_files(source_directory, output_file)
4