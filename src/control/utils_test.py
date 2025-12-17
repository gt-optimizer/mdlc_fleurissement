from ml_pipeline import ImageAnalysisPipeline

# Initialisation du pipeline
pipeline = ImageAnalysisPipeline()

# Chargement du modèle Keras et des classes
pipeline.load_neural_model(
    model_path="model_pipeline.keras",
    classes_path="model_classes.pkl"
)

# Prédiction sur une image de test
TEST_IMAGE = "DSCF0507.JPG"
prediction = pipeline.predict_image_nn(TEST_IMAGE)

print("Prédiction :", prediction)