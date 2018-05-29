import keras
import cv2
import numpy as np
import sys
import os

default_model_name = 'keras_alexnet.h5'
default_model_dir = 'saved_models'


def build_model(image_height=224, image_width=224, class_count=1000):
    """keras implementation of the SuperVision NN designed by Alex Krizhevsky et. al.
    NOTE: this implementation deviates from the original design in two ways:
        1) the original was architected to operate distributedly across two systems (this implementation is not distributed)
        2) keras Batch Normalization is used in-place of the original Alexnet's local response normalization
    https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf
    http://vision.stanford.edu/teaching/cs231b_spring1415/slides/alexnet_tugce_kyunghee.pdf
    http://image-net.org/challenges/LSVRC/2012/supervision.pdf
    :return: assembled alexnet/supervision keras model
    """

    model = keras.models.Sequential()

    # layer 1 - "filters the 224 x 224 x 3 input image with 96 kernels
    #           of size 11 x 11 x 3 with a stride of 4 pixels"
    model.add(keras.layers.Conv2D(filters=96,
                                  kernel_size=(11, 11),
                                  strides=4,
                                  input_shape=(image_height, image_width, 3,),
                                  activation="relu",
                                  padding="same"))
    model.add(keras.layers.BatchNormalization())
    model.add(keras.layers.MaxPool2D(pool_size=(3, 3),
                                     strides=(2, 2)))

    # layer 2 - "256 kernels of size 5 x 5 x 48"
    model.add(keras.layers.Conv2D(filters=256,
                                  kernel_size=(5, 5),
                                  activation="relu",
                                  padding="same"))
    model.add(keras.layers.BatchNormalization())
    model.add(keras.layers.MaxPool2D(pool_size=(3, 3),
                                     strides=(2, 2)))

    # layer 3 - "384 kernels of size 3 x 3 x 256"
    model.add(keras.layers.Conv2D(filters=384,
                                  kernel_size=(3, 3),
                                  activation="relu",
                                  padding="same"))
    # layer 4 - "384 kernels of size 3 x 3 x 192"
    model.add(keras.layers.Conv2D(filters=384,
                                  kernel_size=(3, 3),
                                  activation="relu",
                                  padding="same"))
    # layer 5 - "256 kernels of size 3 x 3 x 192"
    model.add(keras.layers.Conv2D(filters=256,
                                  kernel_size=(3, 3),
                                  activation="relu",
                                  padding="same"))
    model.add(keras.layers.MaxPool2D(pool_size=(3, 3),
                                     strides=(2, 2)))

    # flatten before feeding into FC layers
    model.add(keras.layers.Flatten())

    # fully connected layers
    # "The fully-connected layers have 4096 neurons each."
    # "We use dropout in the first two fully-connected layers..."
    model.add(keras.layers.Dense(units=4096))  # layer 6
    model.add(keras.layers.Dropout(0.5))
    model.add(keras.layers.Dense(units=4096))  # layer 7
    model.add(keras.layers.Dropout(0.5))
    model.add(keras.layers.Dense(units=class_count))  # layer 8

    # output layer is softmax
    model.add(keras.layers.Activation('softmax'))
    return model


def preprocess_image(image, image_height=224, image_width=224):
    """resize images to the appropriate dimensions
    :param image_width:
    :param image_height:
    :param image: image
    :return: image
    """
    return cv2.resize(image, (image_height, image_width))


def load_dataset():
    """loads training and testing resources
    :return: x_train, y_train, x_test, y_test
    """
    return keras.datasets.cifar100.load_data(label_mode='fine')


def generator(batch_size, class_count, image_height, image_width, x_data, y_data):
    """generates batch training (and evaluating) data and labels
    """
    while True:
        X = []  # batch training set
        Y = []  # batch labels
        for index in range(0, len(x_data)):
            X.append(preprocess_image(x_data[index], image_height, image_width))
            Y.append(y_data[index])
            if (index + 1) % batch_size == 0:
                yield np.array(X), keras.utils.to_categorical(np.array(Y), class_count)
                X = []
                Y = []


def train_model(model, image_height=224, image_width=224, class_count=1000):
    """train the SuperVision/alexnet NN model
    :param image_height:
    :param class_count:
    :param image_width:
    :param model: NN model (uncompiled, without weights)
    :return: compiled NN model with weights
    """
    # compile with SGD optimizer and mean squared loss function
    model.compile(loss="categorical_crossentropy",
                  optimizer=keras.optimizers.SGD(lr=0.02, momentum=0.9, decay=0.0005),
                  metrics=['accuracy'])

    # training parameters
    (x_train, y_train), (x_test, y_test) = load_dataset()
    batch_size = 128
    epochs = 90
    steps = len(x_train) / batch_size

    # train the model using a batch generator
    batch_generator = generator(batch_size, class_count, image_height, image_width, x_train, y_train)
    model.fit_generator(generator=batch_generator,
                        steps_per_epoch=steps,
                        epochs=epochs)

    # train the model on the dataset
    # count=10000
    # x_train = np.array([preprocess_image(image) for image in x_train[:count]])
    # y_train = keras.utils.to_categorical(y_train[:count], class_count)
    # model.fit(x=x_train, y=y_train, batch_size=batch_size, epochs=epochs)


def evaluate(model, class_count=1000, image_height=224, image_width=224):
    """evaluate the performance of the trained model using the prepared testing set
    :param model: compiled NN model with trained weights
    """

    # training parameters
    (x_train, y_train), (x_test, y_test) = load_dataset()
    batch_size = 128
    steps = len(x_test) / batch_size

    # train the model using a batch generator
    batch_generator = generator(batch_size, class_count, image_height, image_width, x_test, y_test)
    model.fit_generator(generator=batch_generator,
                        steps=steps)
    scores = model.evaluate_generator()
    print("Test Loss:\t", scores[0])
    print("Test Accuracy:\t", scores[1])


def main():
    """build, train, and test an implementation of the alexnet CNN model in keras.
    This model is trained and tested on the CIFAR-100 dataset
    """
    # build and train the model
    model = build_model(class_count=100)
    print(model.summary())
    train_model(model, class_count=100)

    # test the model
    evaluate(model, class_count=100)

    # save the trained model
    if len(sys.argv) == 0:
        model_path = sys.argv[0]
    else:
        save_dir = os.path.join(os.getcwd(), default_model_dir)
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        model_name = default_model_name
        model_path = os.path.join(save_dir, model_name)
    model.save_weights(model_path, True)
    print("Model Saved to: %s", model_path)


if __name__ == "__main__":
    # execute only if run as a script
    main()

