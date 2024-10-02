import os
import re
import base64

# Percorso della cartella CSS
css_folder = 'css'
output_file = 'ToneCSS.css'

def encode_file_base64(file_path):
    """Legge un file e lo codifica in base64."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def replace_references_with_base64(content, css_dir):
    """Sostituisce ogni riferimento a file (non URL) con il loro contenuto codificato in Base64."""
    # Espressione regolare per trovare riferimenti a file (url('file.ext') o url("file.ext"))
    regex = re.compile(r'url\((["\']?)(?!https?://)([^"\')]+)\1\)')
    
    def replace_match(match):
        file_ref = match.group(2)
        file_path = os.path.join(css_dir, file_ref)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file_ref)[1][1:].lower()
            base64_data = encode_file_base64(file_path)
            return f"url(data:image/{file_ext};base64,{base64_data})"
        return match.group(0)  # Se non è un file, lascia invariato

    return regex.sub(replace_match, content)

def collect_css_files(folder):
    """Raccoglie tutti i file CSS nella cartella, processando per primi quelli nella cartella fonts."""
    css_files = []
    fonts_files = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.css') and not file.startswith('import-'):
                full_path = os.path.join(root, file)
                if 'fonts' in full_path:
                    fonts_files.append(full_path)
                else:
                    css_files.append(full_path)

    # I file della cartella fonts vengono inseriti per primi
    return fonts_files + css_files

def process_css_files(files):
    """Processa i file CSS, sostituendo i riferimenti con base64 e unendoli in un file unico."""
    combined_css = ""

    for css_file in files:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            css_dir = os.path.dirname(css_file)
            # Sostituisce riferimenti ai file con base64
            content_with_base64 = replace_references_with_base64(content, css_dir)
            combined_css += content_with_base64 + '\n'

    return combined_css

def main():
    # Raccoglie tutti i file CSS dalla cartella e sottocartelle
    css_files = collect_css_files(css_folder)

    # Processa i file CSS
    combined_css = process_css_files(css_files)

    # Scrive il CSS combinato nel file di output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_css)

    print(f"Combinazione completata. Il file {output_file} è stato creato con successo.")

if __name__ == "__main__":
    main()
