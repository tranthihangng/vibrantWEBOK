import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Load dataset
data = pd.read_csv("merged_data_finalxyyz.csv")

# Remove 'bearing' and 'State' columns from features
X = data.drop(columns=['state'], errors='ignore')
y = data["state"]

# Encode labels
le = LabelEncoder()
y = le.fit_transform(y)
print("Label mapping:", dict(zip(le.classes_, range(len(le.classes_)))))

# Normalize dataset (-1 to +1 scale)
scaler = MinMaxScaler(feature_range=(-1, 1))
X_scaled = scaler.fit_transform(X)

# StratifiedKFold để chia dữ liệu đồng đều
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Function to compute weighted accuracy
def weighted_acc(predictions, actual):
    freqs = actual.value_counts().to_dict()
    correct = (predictions == actual).astype(int)
    acc_pc = correct.groupby(actual).mean()
    return acc_pc.mean()

# Tối ưu các tham số với cross-validation
results = []
alphas = [0.0001, 0.001, 0.01, 0.1]  # Thêm các giá trị alpha khác nhau
hidden_layers = range(2, 51, 2)  # Giảm số lượng hidden layers và tăng bước nhảy

for alpha in alphas:
    for h in hidden_layers:
        model = MLPClassifier(
            hidden_layer_sizes=(h,),
            max_iter=1000,
            alpha=alpha,  # L2 regularization
            activation="tanh",
            solver="adam",
            learning_rate_init=0.0005,
            early_stopping=True,  # Thêm early stopping
            validation_fraction=0.2,  # 20% dữ liệu training làm validation
            n_iter_no_change=10,  # Số epoch không cải thiện trước khi dừng
            random_state=42
        )
        
        # Sử dụng cross-validation
        cv_scores = cross_val_score(model, X_scaled, y, cv=skf, scoring='accuracy')
        
        results.append({
            'alpha': alpha,
            'hidden_layers': h,
            'mean_cv_score': cv_scores.mean(),
            'std_cv_score': cv_scores.std()
        })

# Chuyển kết quả thành DataFrame
results_df = pd.DataFrame(results)

# Tìm mô hình tốt nhất
best_result = results_df.loc[results_df['mean_cv_score'].idxmax()]
print("\nBest Model Configuration:")
print(f"Hidden Layers: {best_result['hidden_layers']}")
print(f"Alpha: {best_result['alpha']}")
print(f"Mean CV Score: {best_result['mean_cv_score']:.4f} ± {best_result['std_cv_score']:.4f}")

# Vẽ heatmap để visualize kết quả
pivot_table = results_df.pivot(
    index='hidden_layers',
    columns='alpha',
    values='mean_cv_score'
)

plt.figure(figsize=(10, 6))
sns.heatmap(pivot_table, annot=True, fmt='.3f', cmap='YlOrRd')
plt.title('Cross-validation Accuracy for Different Hyperparameters')
plt.xlabel('Alpha (L2 Regularization)')
plt.ylabel('Number of Hidden Neurons')
plt.tight_layout()
plt.savefig('hyperparameter_tuning.png')

# Train mô hình cuối cùng với cấu hình tốt nhất
final_model = MLPClassifier(
    hidden_layer_sizes=(int(best_result['hidden_layers']),),
    max_iter=1000,
    alpha=best_result['alpha'],
    activation="tanh",
    solver="adam",
    learning_rate_init=0.0005,
    early_stopping=True,
    validation_fraction=0.2,
    n_iter_no_change=10,
    random_state=42
)

# Chia dữ liệu cuối cùng
train_idx, test_idx = next(skf.split(X_scaled, y))
X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

# Train và evaluate
final_model.fit(X_train, y_train)
y_pred = final_model.predict(X_test)

# In kết quả chi tiết
print("\nFinal Model Evaluation:")
print(f"Test Accuracy: {accuracy_score(y_test, y_pred):.4f}")

# Vẽ confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig('confusion_matrix.png')
plt.close()

# Lưu learning curves
plt.figure(figsize=(10, 6))
plt.plot(final_model.loss_curve_, label='Training Loss')
if hasattr(final_model, 'validation_scores_'):
    plt.plot(final_model.validation_scores_, label='Validation Score')
plt.title('Learning Curves')
plt.xlabel('Iterations')
plt.ylabel('Loss / Score')
plt.legend()
plt.savefig('learning_curves.png')
plt.close()

# Save the trained model and scaler
print("\nSaving model and scaler...")
joblib.dump(final_model, "practical_mlp_best_model.joblib")
joblib.dump(scaler, "practical_scaler.joblib")
print("✅ Model and scaler saved successfully!")