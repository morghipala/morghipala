import os
import json

# Mappatura delle categorie: codice -> nome visualizzato
CATEGORY_NAMES = {
    "nintendo": "Nintendo",
    # Aggiungi altre categorie qui
}

# Mappatura dei giochi: codice -> nome visualizzato
GAME_NAMES = {
    "SMO": "Super Mario Odyssey",
    "MK8D": "Mario Kart 8 (& Deluxe)",
    # Aggiungi altri giochi qui
}

def scan_media_folder():
    """Scansiona la cartella media e costruisce la struttura dati"""
    result = {"categories": {}}
    
    # Controlla se la cartella media esiste
    if not os.path.exists('media'):
        print("La cartella 'media' non esiste!")
        return result
    
    # Scansiona la cartella media
    for category in os.listdir('media'):
        category_path = os.path.join('media', category)
        if not os.path.isdir(category_path):
            continue
            
        # Inizializza la categoria
        result["categories"][category] = {
            "name": CATEGORY_NAMES.get(category, category.capitalize()),
            "games": {}
        }
            
        # Scansiona le sottocartelle dei giochi
        for game in os.listdir(category_path):
            game_path = os.path.join(category_path, game)
            if not os.path.isdir(game_path):
                continue
                
            # Inizializza il gioco
            result["categories"][category]["games"][game] = {
                "name": GAME_NAMES.get(game, game),
                "media": []
            }
            
            # Trova tutti i file .wav e verifica l'esistenza dei corrispondenti .json e .brstm
            wav_files = []
            for file in os.listdir(game_path):
                if file.endswith('.wav'):
                    base_name = file
                    json_file = os.path.splitext(file)[0] + '.json'
                    brstm_file = os.path.splitext(file)[0] + '.brstm'
                    
                    # Verifica che esistano tutti i file necessari
                    if (os.path.exists(os.path.join(game_path, json_file)) and 
                        os.path.exists(os.path.join(game_path, brstm_file))):
                        wav_files.append(base_name)
                    else:
                        print(f"Attenzione: file mancanti per {base_name} in {game_path}")
            
            # Aggiorna la lista dei media
            result["categories"][category]["games"][game]["media"] = sorted(wav_files)
    
    return result

def write_medialist(data):
    """Scrive il dizionario nel file mediaList.js nel formato corretto"""
    with open('./mediaList.js', 'w', encoding='utf-8') as f:
        # Converte il dizionario in stringa JSON con indentazione
        json_str = json.dumps(data, indent=2)
        
        # Rimuove le virgolette dalle chiavi per mantenere lo stile JavaScript
        json_str = ' '.join(line.strip() for line in json_str.splitlines())
        json_str = json_str.replace('"categories":', 'categories:')
        json_str = json_str.replace('"games":', 'games:')
        json_str = json_str.replace('"name":', 'name:')
        json_str = json_str.replace('"media":', 'media:')
        
        # Formatta il JSON per una migliore leggibilità
        json_str = json_str.replace('{', '{\n  ')
        json_str = json_str.replace('}', '\n}')
        json_str = json_str.replace(':{', ': {')
        json_str = json_str.replace(',[', ',\n  [')
        json_str = json_str.replace(']}', ']\n  }')
        
        f.write(f'window.media_list = {json_str};\n')

def main():
    # Scansiona la cartella media e crea la struttura da zero
    data = scan_media_folder()
    
    # Scrive il risultato nel file
    write_medialist(data)
    print("File mediaList.js aggiornato con successo!")

if __name__ == "__main__":
    main()