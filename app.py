from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from traitement_video import process_video # Assurez-vous que ce fichier est correct et importable
import datetime # Ajout de l'import pour datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Limite à 50MB pour les vidéos

# IMPORTANT : Changez ceci par une clé secrète forte et unique !
app.secret_key = "remplacez_par_une_vraie_cle_secrete_difficile_a_deviner"

# Assurez-vous que le dossier d'upload existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Vous pourriez aussi passer current_year à index.html si vous avez un footer là-bas
    # current_year = datetime.datetime.now().year
    # return render_template('index.html', current_year=current_year)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return "Aucun fichier vidéo n'a été envoyé.", 400 # Message d'erreur plus clair

    file = request.files['video']
    if file.filename == '':
        return "Le fichier vidéo n'a pas de nom.", 400 # Message d'erreur plus clair

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        _, ext = os.path.splitext(original_filename)
        
        # Pour cet exemple, on garde un nom de fichier simple pour le traitement.
        # Dans une application multi-utilisateurs, un nom unique (ex: UUID) serait préférable.
        processing_filename = f"video_to_process{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], processing_filename)
        
        try:
            file.save(save_path)
            print(f"Vidéo sauvegardée : {save_path}")

            # Lancer le traitement de la vidéo
            print(f"Lancement du traitement pour : {save_path}")
            results = process_video(save_path) # Votre fonction de traitement
            print(f"Résultats du traitement : {results}")
            
            # Stocker les résultats et le nom original dans la session
            session['video_results'] = results
            session['video_filename'] = original_filename

            return "Traitement terminé. Résultats stockés.", 200

        except Exception as e:
            print(f"Erreur critique lors de la sauvegarde ou du traitement : {e}")
            # Il serait bon de logger l'erreur complète ici pour le débogage
            # import traceback
            # traceback.print_exc()
            return f"Une erreur est survenue sur le serveur lors du traitement de la vidéo: {str(e)}", 500
    elif not allowed_file(file.filename):
        return "Type de fichier non autorisé. Veuillez utiliser un format vidéo supporté (mp4, mov, avi, mkv).", 400
    else:
        # Cas peu probable si les vérifications précédentes sont passées
        return "Une erreur inconnue est survenue avec le fichier.", 400


@app.route('/result')
def result_page():
    results = session.get('video_results', None)
    video_filename = session.get('video_filename', "Inconnue") # Nom par défaut plus neutre
    current_year = datetime.datetime.now().year

    # Même si 'results' est None (par exemple, si l'utilisateur accède directement à /result),
    # nous rendons toujours la page result.html, qui gérera l'affichage d'un message approprié.
    return render_template('result.html',
                           results=results,
                           video_name=video_filename,
                           current_year=current_year)

if __name__ == '__main__':
    # Il est généralement recommandé de ne pas utiliser app.run(debug=True) en production.
    # Utilisez un serveur WSGI comme Gunicorn ou Waitress pour la production.
    app.run(debug=True, host='0.0.0.0', port=5000) # host='0.0.0.0' pour rendre accessible sur le réseau local