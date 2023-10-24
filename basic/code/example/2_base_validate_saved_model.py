from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, random_state=2022)

scaler_load = joblib.load("scaler.joblib")
classifier_load = joblib.load("classifier.joblib")

scaled_X_train = scaler_load.transform(X_train)
scaled_X_valid = scaler_load.transform(X_valid)

load_train_pred = classifier_load.predict(scaled_X_train)
load_valid_pred = classifier_load.predict(scaled_X_valid)

load_train_acc = accuracy_score(y_true=y_train, y_pred=load_train_pred)
load_valid_acc = accuracy_score(y_true=y_valid, y_pred=load_valid_pred)

print("Load Model Train Accuracy :", load_train_acc)
print("Load Model Valid Accuracy :", load_valid_acc)

# Load Model Train Accuracy : 0.9833333333333333
# Load Model Valid Accuracy : 0.9666666666666667