import os
import shutil

# === CONFIG ===
ACCURACY_THRESHOLD = 0.7  # Modifică în funcție de ce consideri "face recogn mare"
EVAL_REPORT_PATH = "../performance_report.txt"  # Raportul de evaluare salvat ca text (output-ul tău)
TESTSET_PATH = "../database/dataset_test_min20"  # Folderul SETULUI DE TEST
TRAINSET_PATH = "../database/dataset_train_min20"  # Folderul SETULUI DE TRAIN
DEST_TEST = "../database/dataset_test_filtered"
DEST_TRAIN = "../database/dataset_train_filtered"


def parse_eval_report(report_path, acc_threshold=ACCURACY_THRESHOLD):
    persons = []
    with open(report_path, "r") as f:
        for line in f:
            # Caută linii cu formatul: Nume_Persoana   prec  rec  f1  support
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    precision = float(parts[-4])
                    recall = float(parts[-3])
                    f1 = float(parts[-2])
                    support = int(parts[-1])
                    name = " ".join(parts[:-4])
                    # Consideră o persoană "bună" dacă recall sau f1-score peste prag
                    if recall >= acc_threshold or f1 >= acc_threshold:
                        persons.append(name.replace(" ", "_"))
                except ValueError:
                    continue  # Linie neconformă, sari peste
    return set(persons)

def copy_selected_persons(src_dir, dest_dir, person_names):
    os.makedirs(dest_dir, exist_ok=True)
    found = 0
    for person in person_names:
        src_path = os.path.join(src_dir, person)
        dest_path = os.path.join(dest_dir, person)
        if os.path.exists(src_path) and os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            found += 1
    return found

if __name__ == "__main__":
    good_persons = parse_eval_report(EVAL_REPORT_PATH)
    print(f"{len(good_persons)} persoane selectate cu valoare recall/f1 >= {ACCURACY_THRESHOLD}")
    print("Exemple:", list(good_persons)[:5])

    found_test = copy_selected_persons(TESTSET_PATH, DEST_TEST, good_persons)
    found_train = copy_selected_persons(TRAINSET_PATH, DEST_TRAIN, good_persons)

    print(f"Au fost copiate {found_test} persoane în {DEST_TEST}")
    print(f"Au fost copiate {found_train} persoane în {DEST_TRAIN}")
    print("Gata! Acum ai doar persoanele cu acuratețe mare.")