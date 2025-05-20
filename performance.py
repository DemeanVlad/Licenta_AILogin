import os
import tensorflow as tf
import numpy as np
import json
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Fixează seed-ul pentru reproducibilitate
SEED = 42
os.environ['PYTHONHASHSEED'] = str(SEED)
tf.random.set_seed(SEED)
np.random.seed(SEED)

# Calea către modelul antrenat și fișierul cu mapping-ul claselor
MODEL_PATH = "face_recognition_model_mobilenetv2.h5"
CLASS_INDICES_PATH = "class_indices.json"

# Încarcă modelul și mapping-ul claselor
model = load_model(MODEL_PATH)

with open(CLASS_INDICES_PATH, "r") as f:
    class_indices = json.load(f)

# Creează mapping-ul invers (index numeric -> nume clasă)
class_labels = {v: k for k, v in class_indices.items()}

# Funcție pentru preprocesarea imaginilor
def preprocess_image(image_path, target_size=(128, 128)):
    img = load_img(image_path, target_size=target_size)
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0  # Normalizează imaginea
    return img_array

# Funcție pentru testarea folderului de test
def evaluate_model_on_test_folder(test_folder, output_file):
    y_true = []
    y_pred = []

    # Parcurge fiecare subfolder din folderul de test
    for class_dir in os.listdir(test_folder):
        class_path = os.path.join(test_folder, class_dir)
        if not os.path.isdir(class_path):  # Ignoră fișierele care nu sunt directoare
            continue

        # Parcurge imaginile din subfolder
        for image_name in os.listdir(class_path):
            if image_name.startswith("."):  # Ignoră fișierele ascunse precum .DS_Store
                continue
            image_path = os.path.join(class_path, image_name)
            try:
                # Preprocesează imaginea
                img_array = preprocess_image(image_path)

                # Obține predicția
                predictions = model.predict(img_array)
                predicted_class_index = np.argmax(predictions, axis=1)[0]
                predicted_class_label = class_labels[predicted_class_index]

                # Salvează etichetele reale și prezise
                y_true.append(class_dir)  # Clasa reală este numele folderului
                y_pred.append(predicted_class_label)  # Clasa prezisă
            except Exception as e:
                print(f"Error processing {image_name}: {e}")

    if not y_true or not y_pred:
        print("Nu există imagini valide în folderul de test.")
        return

    # Calculează acuratețea
    accuracy = accuracy_score(y_true, y_pred) * 100
    print(f"Acuratețea modelului este: {accuracy:.2f}%")

    # Generează raportul de clasificare
    report = classification_report(y_true, y_pred)
    print(report)

    # Generează matricea de confuzie
    conf_matrix = confusion_matrix(y_true, y_pred, labels=list(class_labels.values()))

    # Salvează rezultatele într-un fișier text
    with open(output_file, "w") as f:
        f.write("Performance Report\n")
        f.write("==================\n")
        f.write(f"Acuratețe: {accuracy:.2f}%\n\n")
        f.write("Raport de Clasificare:\n")
        f.write(report)
        f.write("\n")

    # Afișează matricea de confuzie
    plt.figure(figsize=(10, 8))
    sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=list(class_labels.values()), yticklabels=list(class_labels.values()))
    plt.xlabel("Clase Prezise")
    plt.ylabel("Clase Reale")
    plt.title("Matricea de Confuzie")
    plt.savefig("confusion_matrix.png")
    plt.show()

    print(f"Raportul a fost salvat în fișierul: {output_file}")
    print("Matricea de confuzie a fost salvată ca 'confusion_matrix.png'.")

# Exemplu de utilizare
if __name__ == "__main__":
    TEST_FOLDER = "dataset_test/"  # Folderul de test
    OUTPUT_FILE = "performance_report.txt"  # Fișierul de ieșire
    evaluate_model_on_test_folder(TEST_FOLDER, OUTPUT_FILE)