import tensorflow as tf
import numpy as np
import cv2
import os

print('\nLoading model...')
# Load the trained model
model = tf.keras.models.load_model('model/model.h5')

# Define image properties
IMG_HEIGHT, IMG_WIDTH = 150, 150

def preprocess_image(image_path):
    """
    Load and preprocess an image for prediction.
    - Reads the image.
    - Resizes it to match the training dimensions.
    - Normalizes pixel values to [0,1].
    - Adds batch dimension (1, 150, 150, 3).
    """
    img = cv2.imread(image_path)  # Read image
    img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))  # Resize
    img = img / 255.0  # Normalize
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

def predict(image_path):
    """
    Predict whether the given image is a cat or a dog.
    """
    processed_img = preprocess_image(image_path)
    prediction = model.predict(processed_img)[0][0]  # Get prediction score
    return "Dog 🐶" if prediction > 0.5 else "Cat 🐱"

# Example usage
if __name__ == "__main__":

    #Get Image Name:
    input_image_name = "12492" + ".jpg" # Change image path to pass different examples

    test_image_path = f"example_images/" + input_image_name  # Replace with an image path
    if not os.path.exists(test_image_path):
        print(f"Error: {test_image_path} not found.")
    else:
        result = predict(test_image_path)
        print(f"Prediction: {input_image_name} is a {result}")
