<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_FILES['video']) && $_FILES['video']['error'] === 0) {
        $uploadDir = __DIR__ . '/';  // Répertoire courant
        $fileName = basename($_FILES['video']['name']);
        $targetPath = $uploadDir . $fileName;

        if (move_uploaded_file($_FILES['video']['tmp_name'], $targetPath)) {
            echo "Vidéo uploadée avec succès : $fileName";
        } else {
            echo "Erreur lors de l'enregistrement de la vidéo.";
        }
    } else {
        echo "Aucune vidéo reçue ou une erreur est survenue.";
    }
}
?>
