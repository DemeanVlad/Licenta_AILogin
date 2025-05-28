import os
import tensorflow as tf
import numpy as np
import json
import time
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, top_k_accuracy_score, precision_score
import matplotlib.pyplot as plt
import seaborn as sns

MODEL_PATH = "../face_recognition_model_mobilenetv2_finetuned.h5"
CLASS_INDICES_PATH = "../class_indices.json"
TEST_DIR = "../database/dataset_test_filtered"

model = load_model(MODEL_PATH)
with open(CLASS_INDICES_PATH, "r") as f:
    class_indices = json.load(f)
class_labels = {v: k for k, v in class_indices.items()}

def preprocess_image(image_path, target_size=(224, 224)):
    start_load = time.time()
    img = load_img(image_path, target_size=target_size)
    load_time = time.time() - start_load

    start_enc = time.time()
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    encoding_time = time.time() - start_enc

    return img_array, load_time, encoding_time

def compute_far_frr_gar(y_true, y_pred):
    total = len(y_true)
    correct = sum([yt == yp for yt, yp in zip(y_true, y_pred)])
    false_accept = sum([yt != yp for yt, yp in zip(y_true, y_pred)])
    false_reject = false_accept
    FAR = 100.0 * false_accept / total if total > 0 else 0
    FRR = 100.0 * false_reject / total if total > 0 else 0
    GAR = 100.0 * correct / total if total > 0 else 0
    return FAR, FRR, GAR

def evaluate_model_on_test_folder(test_folder):
    y_true = []
    y_pred = []
    y_pred_probs = []
    load_times = []
    encoding_times = []
    comparison_times = []

    for class_dir in os.listdir(test_folder):
        class_path = os.path.join(test_folder, class_dir)
        if not os.path.isdir(class_path):
            continue

        for image_name in os.listdir(class_path):
            if image_name.startswith("."):
                continue
            image_path = os.path.join(class_path, image_name)
            try:
                img_array, load_time, encoding_time = preprocess_image(image_path)
                load_times.append(load_time)
                encoding_times.append(encoding_time)

                start_cmp = time.time()
                predictions = model.predict(img_array, verbose=0)
                cmp_time = time.time() - start_cmp
                comparison_times.append(cmp_time)

                predicted_class_index = np.argmax(predictions, axis=1)[0]
                predicted_class_label = class_labels[predicted_class_index]
                y_true.append(class_dir)
                y_pred.append(predicted_class_label)
                y_pred_probs.append(predictions[0])
            except Exception as e:
                print(f"Error processing {image_name}: {e}")

    if not y_true or not y_pred:
        print("Nu există imagini valide în folderul de test.")
        return

    y_pred_probs = np.array(y_pred_probs)
    accuracy = accuracy_score(y_true, y_pred)
    precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    report = classification_report(y_true, y_pred, zero_division=0)

    # Timing metrics
    avg_load_time = np.mean(load_times)
    avg_encoding_time = np.mean(encoding_times)
    avg_comparison_time = np.mean(comparison_times)
    total_time = avg_load_time + avg_encoding_time + avg_comparison_time

    # Top-3 accuracy dacă este cazul
    top3_acc = None
    if y_pred_probs.shape[1] >= 3:
        class_list = list(class_labels.values())
        y_true_indices = [class_list.index(c) for c in y_true]
        top3_acc = top_k_accuracy_score(y_true_indices, y_pred_probs, k=3)

    # FAR, FRR, GAR
    FAR, FRR, GAR = compute_far_frr_gar(y_true, y_pred)

    # Scrie totul într-un fișier
    with open("performance_report.txt", "w") as f:
        f.write("--- Timing Metrics ---\n")
        f.write(f"Image Load Time: {avg_load_time:.4f} seconds\n")
        f.write(f"Encoding Time: {avg_encoding_time:.4f} seconds\n")
        f.write(f"Comparison Time: {avg_comparison_time:.4f} seconds\n")
        f.write(f"Total Time: {total_time:.4f} seconds\n\n")
        f.write("--- Performance Metrics ---\n")
        f.write(f"Acuratețe generală: {accuracy * 100:.2f}%\n")
        f.write(f"Precision macro: {precision_macro:.3f}\n")
        if top3_acc is not None:
            f.write(f"Top-3 Accuracy: {top3_acc * 100:.2f}%\n")
        f.write(f"False Acceptance Rate (FAR): {FAR:.2f}%\n")
        f.write(f"False Rejection Rate (FRR): {FRR:.2f}%\n")
        f.write(f"Genuine Acceptance Rate (GAR): {GAR:.2f}%\n\n")
        f.write("Raport clasificare per clasă:\n")
        f.write(report)

    print("Raportul de performanță a fost salvat în 'performance_report.txt'.")

    # Matrice de confuzie
    label_order = sorted(list(set(y_true + y_pred)))
    conf_matrix = confusion_matrix(y_true, y_pred, labels=label_order)
    plt.figure(figsize=(max(8, len(label_order)//2), max(6, len(label_order)//2)))
    sns.heatmap(conf_matrix, annot=False, fmt="d", cmap="Blues",
                xticklabels=label_order, yticklabels=label_order)
    plt.xlabel("Clase prezise")
    plt.ylabel("Clase reale")
    plt.title("Matrice de confuzie")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")
    plt.close()
    print("Matricea de confuzie a fost salvată ca 'confusion_matrix.png'.")

if __name__ == "__main__":
    evaluate_model_on_test_folder(TEST_DIR)