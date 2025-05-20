import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.regularizers import l2
import json

# Fixează seed-ul pentru reproducibilitate
SEED = 42
os.environ['PYTHONHASHSEED'] = str(SEED)
tf.random.set_seed(SEED)

# Configurare dataset
TRAIN_DIR = "dataset/"
VALID_DIR = "dataset_test/"

# Generator pentru antrenare cu augmentare
train_datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    rotation_range=40,  # Rotește imaginile
    width_shift_range=0.3,  # Deplasare pe orizontală
    height_shift_range=0.3,  # Deplasare pe verticală
    shear_range=0.3,  # Transformare shear
    zoom_range=0.3,  # Zoom
    horizontal_flip=True,  # Flip orizontal
    fill_mode='nearest'
)

train_generator = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=(224, 224),  # Dimensiunea imaginilor
    batch_size=32,
    class_mode='categorical'
)

# Generator pentru validare
valid_datagen = ImageDataGenerator(rescale=1.0/255.0)
valid_generator = valid_datagen.flow_from_directory(
    VALID_DIR,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical'
)

# Încarcă modelul preantrenat MobileNetV2
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Adaugă straturi personalizate
x = base_model.output
x = GlobalAveragePooling2D()(x)  # Reduce dimensiunea caracteristicilor
x = Dense(256, activation='relu', kernel_regularizer=l2(0.01))(x)  # Strat dens cu regularizare L2
x = Dropout(0.5)(x)  # Regularizare Dropout
predictions = Dense(train_generator.num_classes, activation='softmax')(x)  # Strat de ieșire

# Creează modelul final
model = Model(inputs=base_model.input, outputs=predictions)

# Îngheață straturile preantrenate
for layer in base_model.layers:
    layer.trainable = False

# Compilează modelul
model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# Callback-uri pentru Early Stopping, reducerea ratei de învățare și TensorBoard
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=0.00001)
tensorboard = TensorBoard(log_dir='./logs', histogram_freq=1)

# Antrenează modelul
history = model.fit(
    train_generator,
    epochs=20,  # Număr inițial de epoci
    validation_data=valid_generator,
    callbacks=[early_stopping, reduce_lr, tensorboard]
)

# Dezgheață ultimele 30 de straturi ale modelului preantrenat pentru Fine-Tuning
for layer in base_model.layers[-30:]:
    layer.trainable = True

# Recompilează modelul cu un learning rate mai mic
model.compile(optimizer=Adam(learning_rate=0.0001), loss='categorical_crossentropy', metrics=['accuracy'])

# Continuă antrenarea cu Fine-Tuning
history = model.fit(
    train_generator,
    epochs=10,  # Epoci suplimentare pentru Fine-Tuning
    validation_data=valid_generator,
    callbacks=[early_stopping, reduce_lr, tensorboard]
)

# Salvează modelul
model.save("face_recognition_model_mobilenetv2_finetuned.h5")

# Salvează mapping-ul claselor
class_indices = train_generator.class_indices
with open("class_indices.json", "w") as f:
    json.dump(class_indices, f)

print("Antrenarea s-a terminat și modelul a fost salvat.")