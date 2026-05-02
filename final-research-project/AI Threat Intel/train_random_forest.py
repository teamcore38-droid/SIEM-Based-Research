import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from pandas.api.types import is_numeric_dtype

DATA_PATH = "X:/AI-TI/data/combined_dataset.csv"
df = pd.read_csv(DATA_PATH)

print("Dataset loaded:", df.shape)

# Remove unnecessary columns
df = df.drop(columns=["device_id", "attack_type", "src_ip"], errors='ignore')

# Encode categorical variables
encoders = {}

for column in df.columns:
    if not is_numeric_dtype(df[column]):
        le = LabelEncoder()
        df[column] = le.fit_transform(df[column].astype(str))
        encoders[column] = le

joblib.dump(encoders, "X:/AI-TI/models/encoders.pkl")

print("Encoders saved")

# Split features and target
X = df.drop(columns=["is_attack", "label"], errors='ignore')
y = df["is_attack"]

joblib.dump(X.columns.tolist(), "X:/AI-TI/models/rf_features.pkl")

print("Training features:")
print(X.columns)

# Train
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, "X:/AI-TI/models/random_forest_model.pkl")

print("Random Forest training completed")