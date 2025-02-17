from datetime import date as dt
import os
import gc
import pickle as pkl  # module for serialization
from tensorflow.keras import backend as K

today = dt.today()
date = today.strftime("%b-%d-%Y")
from colab_utils import *

load = False
inception = False
resnet = False
exp_name, baseline, cutout, shear, gblur, crop, randcomb, mobius, allcomb_sparse, allcomb_full, resnet, inception = read_args()
print('exp_name '+exp_name)
path = os.path.join(os.getcwd(), 'data_10_early_late')


if load:

    split_dict = load_test_set("PATH_TO_PKL_SPLITS")
    print(split_dict.keys())
    X = split_dict['X']
    Y = split_dict['Y']
    X_test = split_dict['X_test']
    y_test = split_dict['y_test']

    print(f"Data sizes: X: {len(X)}, Y: {len(Y)}, test_images: {len(X_test)}, test_labels: {len(y_test)}")

    print(
        "ratios of labels in the data set are {} {} {}".format(round(Y.count(0) / len(Y), 2),
                                                               round(Y.count(1) / len(Y), 2)))
    print(
        "ratios of labels in the test set are {} : {} : {}".format(round(y_test.count(0) / len(y_test), 2),
                                                                     round(y_test.count(1) / len(y_test), 2)))
else:

    if mobius or resnet or inception:
        data = create_data(path, duplicate_channels=True, equalize=True)
    else:
        data = create_data(path, duplicate_channels=False, equalize=True)

    print(len(data))
    # should be 152
    data_list = []
    data_list.append(data[0:len(data)])

    X = []
    Y = []
    for i in data_list:
        for feature, label in i:
            X.append(feature)
            Y.append(label)

    print(
        "ratios of labels in the data set are {} : {}".format(round(Y.count(0) / len(Y), 2), round(Y.count(1) / len(Y), 2),
                                                               round(Y.count(2) / len(Y), 2)))

    print(f"Data sizes: X: {len(X)}, Y: {len(Y)}")
    X, X_test, Y, y_test = train_test_split(X, Y, test_size=0.2, stratify=Y)
    print("ratios of labels in the test set are {} : {} ".format(round(y_test.count(0) / len(y_test), 2),
                                                                     round(y_test.count(1) / len(y_test), 2)))

    split_dict = save_test_set(os.path.join(os.getcwd(), 'saved_test_sets'), exp_name, X, X_test, Y, y_test)

if mobius or resnet or inception:
    print("converting to RGB")
    for i in range(0, len(X)):
        X[i] = Image.fromarray(X[i])
        X[i] = X[i].convert("RGB")
        X[i] = np.array(X[i])
        print("x shape is {}".format(X[i].shape))
    for i in range(0, len(X_test)):
        X_test[i] = Image.fromarray(X_test[i])
        X_test[i] = X_test[i].convert("RGB")
        X_test[i] = np.array(X_test[i])
        print("x test shape is {}".format(X_test[i].shape))

# Kfold CV (k=10)
X_train, y_train, X_val, y_val = kfoldcv(X, Y, k=10)
# from utils import augment_data
X_train_aug, y_train_aug, X_val_aug, y_val_aug = augment_data(X_train, y_train, X_val, y_val, baseline, cutout, shear,
                                                              gblur, crop, randcomb, mobius, allcomb_sparse, allcomb_full, resnet, inception, limb=False)


results = {"accuracies": [], "losses": [], "val_accuracies": [],
           "val_losses": [], "test_performance": [], "test_accuracies": [], "test_losses": []}
hyperparams = {"configuration": [], "loss_func": [], "optimizer": [], "learning_rate": [], "lambda": []}

if resnet and not inception:
    for i in range(0, len(X_train_aug)):
        K.clear_session()
        tf.compat.v1.reset_default_graph()
        gc.collect()

        print("re-training_resnet50_model_{}".format(i))
        print("train shape before sending to resnet {}".format(np.array(X_train_aug[i]).shape))
        results = train_model_resnet50(X_train_aug[i], X_val_aug[i], y_train_aug[i], y_val_aug[i], X_test, y_test,
                                       exp_name, results, hyperparams, i, model = None, pretrained= False, freeze=True)
        K.clear_session()
        tf.compat.v1.reset_default_graph()
        gc.collect()

if inception and not resnet:
    for i in range(0, len(X_train_aug)):
        K.clear_session()
        tf.compat.v1.reset_default_graph()
        gc.collect()

        print("re-training_InceptionV3_model_{}".format(i))
        print("train shape before sending to inception {}".format(np.array(X_train_aug[i]).shape))
        results = train_model_inception(X_train_aug[i], X_val_aug[i], y_train_aug[i], y_val_aug[i], X_test, y_test,
                                       exp_name, results, hyperparams, i, model = None, pretrained= False)
        K.clear_session()
        tf.compat.v1.reset_default_graph()
        gc.collect()


else:

    for i in range(0, len(X_train_aug)):
        print("training_our_model_{}".format(i))
        results, hyperparams = train_model(X_train_aug[i], X_val_aug[i], y_train_aug[i], y_val_aug[i], X_test, y_test, exp_name,
                              results, hyperparams, i, lr=0.00001, lmbd=0.0001)
        K.clear_session()
        tf.compat.v1.reset_default_graph()
        gc.collect()


print('Results:', results, file=open('results/Results_{}_{}.txt'.format(exp_name, date), "w"))
print('Hyperparams:', hyperparams, file=open('results/Hyperparams{}_{}.txt'.format(exp_name, date), "w"))