# traitement_video.py
import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import os # Ajouté

# Chemin vers le fichier label_map.txt (supposons qu'il est dans le même répertoire que ce script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LABEL_MAP_PATH = os.path.join(BASE_DIR, "label_map.txt")

# Charger le modèle et les labels une seule fois au démarrage du module si possible
try:
    print("[INFO] Chargement du modèle I3D...")
    model_i3d = hub.load("https://tfhub.dev/deepmind/i3d-kinetics-400/1")
    print("[INFO] Modèle I3D chargé.")

    print("[INFO] Chargement des labels...")
    if not os.path.exists(LABEL_MAP_PATH):
        raise FileNotFoundError(f"Le fichier de labels '{LABEL_MAP_PATH}' est introuvable.")
    with open(LABEL_MAP_PATH, "r") as f:
        labels_i3d = [line.strip() for line in f.readlines()]
    print(f"[INFO] Labels chargés: {len(labels_i3d)} labels trouvés.")

except Exception as e:
    print(f"[ERREUR CRITIQUE] Impossible de charger le modèle I3D ou les labels: {e}")
    model_i3d = None
    labels_i3d = []


def process_video(video_path):
    if not model_i3d or not labels_i3d:
        return {"error": "Modèle ou labels non chargés. Vérifiez les logs du serveur."}

    print(f"[INFO] Traitement de la vidéo: {video_path}")
    if not os.path.exists(video_path):
        return {"error": f"Fichier vidéo introuvable: {video_path}"}

    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (224, 224))
        frame = frame / 255.0
        frames.append(frame)
        frame_count += 1
        if frame_count == 64: # I3D utilise typiquement 64 frames, mais peut en prendre plus.
                              # Pour cet exemple, on se limite à 64 pour simplifier.
            break
    cap.release()

    if len(frames) == 0:
        return {"error": "Aucune frame n'a pu être lue de la vidéo."}
    
    # Si moins de 64 frames, on peut les dupliquer ou retourner une erreur.
    # Pour I3D, un nombre fixe de frames est souvent attendu.
    # Ici, on va s'assurer qu'on a exactement 64 frames, en dupliquant la dernière si besoin.
    # Ou, pour être plus strict, on retourne une erreur si pas assez de frames.
    if len(frames) < 16: # Un minimum pour avoir un sens
        return {"error": f"La vidéo contient seulement {len(frames)} frames. Un minimum (e.g. 16) est requis. 64 sont idéales."}

    # S'assurer que nous avons 64 frames, en dupliquant si nécessaire ou en prenant les 64 premières.
    # Pour cet exemple, prenons les frames disponibles, jusqu'à 64.
    # Le modèle I3D est flexible sur la longueur de la séquence d'entrée, mais attend [batch_size, num_frames, height, width, channels]
    # Si nous avons moins de 64 frames, nous pouvons les "padder" ou en utiliser moins.
    # Pour l'instant, utilisons ce que nous avons, jusqu'à 64.
    # Le modèle Kinetics-400 I3D est entraîné sur des clips de 64 images.
    # Si vous avez moins de 64 images, vous devrez peut-être les répéter pour atteindre 64.
    # Si vous en avez plus, vous pouvez les découper en segments de 64.
    # Pour une simple prédiction sur les premières frames (jusqu'à 64):
    
    processed_frames = frames
    if len(frames) < 64:
        # Option 1: Répéter la dernière frame pour atteindre 64
        # last_frame = frames[-1]
        # while len(processed_frames) < 64:
        #     processed_frames.append(last_frame)
        # Option 2: Erreur (si 64 est strict)
        print(f"[AVERTISSEMENT] La vidéo a {len(frames)} frames, moins que les 64 optimales. Utilisation des frames disponibles.")
        # Pour certains modèles, cela peut ne pas fonctionner. Vérifiez la doc du modèle.
        # Le modèle I3D de TF Hub peut gérer des séquences de longueur variable.

    print(f"[INFO] {len(processed_frames)} frames extraites et traitées.")

    video_tensor = np.array(processed_frames, dtype=np.float32)
    if video_tensor.ndim == 3: # Si c'est une seule image (cas non voulu ici, mais pour robustesse)
        video_tensor = np.expand_dims(video_tensor, axis=0) # Ajoute une dimension pour num_frames
    video_tensor = np.expand_dims(video_tensor, axis=0)  # Ajoute une dimension pour batch_size
                                                         # S'attend à (1, num_frames, 224, 224, 3)

    print("[INFO] Prédiction en cours...")
    try:
        # Assurez-vous que video_tensor a la bonne forme [batch_size, num_frames, height, width, channels]
        # Le modèle sur TF Hub peut prendre une entrée de forme [batch_size, time, height, width, 3]
        # où `time` peut être variable.
        input_tensor = tf.constant(video_tensor, dtype=tf.float32)
        logits = model_i3d.signatures["default"](input_tensor)["default"]
        probs = tf.nn.softmax(logits, axis=-1)
    except Exception as e:
        return {"error": f"Erreur lors de la prédiction: {e}. Shape du tenseur d'entrée: {video_tensor.shape}"}


    top_indices = tf.argsort(probs[0], direction='DESCENDING')[:5].numpy()

    results = []
    for i in top_indices:
        label = labels_i3d[i] if i < len(labels_i3d) else "Label inconnu"
        probability = probs[0][i].numpy() * 100
        results.append({"label": label, "probability": f"{probability:.2f}%"})

    print("\n🎯 Top 5 des actions détectées (dans la fonction):")
    for res in results:
        print(f"- {res['label']} ({res['probability']})")

    return {"predictions": results}

# Pour tester le script directement (optionnel)
if __name__ == '__main__':
    # Créez un faux fichier video.mp4 dans uploads pour tester
    # ou remplacez par un chemin de vidéo existant
    test_video_path = "uploads/video.mp4" # Assurez-vous que ce fichier existe pour le test
    if os.path.exists(test_video_path):
        results = process_video(test_video_path)
        if "error" in results:
            print(f"Erreur de test: {results['error']}")
        else:
            print("Résultats du test:")
            for r in results.get("predictions", []):
                print(r)
    else:
        print(f"Fichier de test {test_video_path} non trouvé. Placez une vidéo pour tester.")