from ml_pipeline import ImageAnalysisPipeline

# Dossier contenant les images organisées par classe
TRAIN_DIR = "/home/optimizerlabsgt/PycharmProjects/orange_fleurissement/src/control/training"

# Initialisation du pipeline
pipeline = ImageAnalysisPipeline()

# Entraînement complet du pipeline (NN + clustering)
nn_model, X, y, clusters = pipeline.train_pipeline(
    train_dir=TRAIN_DIR,
    epochs=30,        # Ajuste si nécessaire
    batch_size=16
)

# Sauvegarde du modèle Keras et des classes
pipeline.save_model(
    model_path="model_pipeline.keras",
    classes_path="model_classes.pkl"
)

print("Entraînement terminé et modèle sauvegardé !")