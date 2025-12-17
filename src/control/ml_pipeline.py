import os
import numpy as np
import pickle
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances
from io import BytesIO
from PIL import Image

class ImageAnalysisPipeline:
    def __init__(self):
        # Embedding InceptionV3 (feature extractor)
        self.embed_model = InceptionV3(weights='imagenet', include_top=False, pooling='avg')
        self.nn_model = None
        self.classes = None
        self.label_encoder = None

    # --------------------------
    # 1. Embedding d'une image
    # --------------------------
    def get_image_embedding(self, img_file):
        if hasattr(img_file, 'read'):
            img_file.seek(0)
            img = Image.open(BytesIO(img_file.read()))
        else:
            img = Image.open(img_file)
        img = img.resize((299, 299))
        x = np.array(img)
        if x.shape[-1] == 4:
            x = x[..., :3]
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        embedding = self.embed_model.predict(x, verbose=0)
        return embedding.flatten()

    # --------------------------
    # 2. Charger dataset d'images
    # --------------------------
    def load_image_dataset(self, root_dir):
        embeddings = []
        labels = []
        self.classes = sorted([
            d for d in os.listdir(root_dir)
            if os.path.isdir(os.path.join(root_dir, d))
        ])
        for klass in self.classes:
            class_dir = os.path.join(root_dir, klass)
            for fname in os.listdir(class_dir):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    path = os.path.join(class_dir, fname)
                    emb = self.get_image_embedding(path)
                    embeddings.append(emb)
                    labels.append(klass)
        X = np.array(embeddings)
        y = np.array(labels)
        return X, y

    # --------------------------
    # 3. Créer le modèle Neural Network
    # --------------------------
    def create_nn_model(self, input_dim, num_classes):
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(512, activation='relu'),
            Dense(256, activation='relu'),
            Dense(num_classes, activation='softmax')
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    # --------------------------
    # 4. Entraîner le NN
    # --------------------------
    def train_nn(self, X, y, epochs=30, batch_size=16, test_size=0.2):
        self.label_encoder = LabelEncoder()
        y_enc = self.label_encoder.fit_transform(y)
        self.classes = self.label_encoder.classes_
        y_cat = to_categorical(y_enc)

        X_train, X_val, y_train, y_val = train_test_split(X, y_cat, test_size=test_size, random_state=42, stratify=y_cat)
        self.nn_model = self.create_nn_model(X.shape[1], y_cat.shape[1])
        self.nn_model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=epochs, batch_size=batch_size, verbose=1)
        return self.nn_model

    # --------------------------
    # 5. Clustering hiérarchique
    # --------------------------
    def hierarchical_clustering(self, X, n_clusters=5):
        dist_matrix = pairwise_distances(X, metric='euclidean')
        clusterer = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric="precomputed",
            linkage="average"
        )
        labels = clusterer.fit_predict(dist_matrix)
        return labels

    # --------------------------
    # 6. Évaluer le modèle
    # --------------------------
    def evaluate_nn(self, X_test, y_test):
        if self.nn_model is None:
            raise ValueError("Neural Network not trained")
        y_pred_prob = self.nn_model.predict(X_test, verbose=0)
        y_pred = y_pred_prob.argmax(axis=1)
        y_true = self.label_encoder.transform(y_test)
        cm = confusion_matrix(y_true, y_pred)
        report = classification_report(y_true, y_pred, target_names=self.classes)
        print("Classification Report:\n", report)
        return y_pred, cm

    # --------------------------
    # 7. Sauvegarder modèle et classes
    # --------------------------
    def save_model(self, model_path="model_pipeline.keras", classes_path="model_classes.pkl"):
        if self.nn_model is None or self.classes is None:
            raise ValueError("NN model or classes not trained")
        self.nn_model.save(model_path)
        with open(classes_path, "wb") as f:
            pickle.dump(self.classes, f)

    # --------------------------
    # 8. Charger modèle et classes
    # --------------------------
    def load_neural_model(self, model_path="model_pipeline.keras", classes_path="model_classes.pkl"):
        from tensorflow.keras.models import load_model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(classes_path):
            raise FileNotFoundError(f"Classes file not found: {classes_path}")
        self.nn_model = load_model(model_path)
        with open(classes_path, "rb") as f:
            self.classes = pickle.load(f)
        self.label_encoder = None  # pas nécessaire après le chargement

    # --------------------------
    # 9. Prédire une image (retourne le nom de classe)
    # --------------------------
    def predict_image_nn(self, img_path):
        if self.nn_model is None or self.classes is None:
            raise ValueError("NN model or classes not loaded")
        emb = self.get_image_embedding(img_path).reshape(1, -1)
        pred_idx = self.nn_model.predict(emb, verbose=0).argmax()
        return self.classes[pred_idx]

    # --------------------------
    # 10. Pipeline complet d'entraînement
    # --------------------------
    def train_pipeline(self, train_dir, epochs=30, batch_size=16):
        X, y = self.load_image_dataset(train_dir)
        self.train_nn(X, y, epochs=epochs, batch_size=batch_size)
        labels_cluster = self.hierarchical_clustering(X, n_clusters=len(self.classes))
        return self.nn_model, X, y, labels_cluster