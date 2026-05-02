"""
Alert Prioritization Model Training
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import os

def train_alert_prioritization_model():
    """
    Train Random Forest model for alert prioritization
    """
    
    print("="*70)
    print("🤖 ALERT PRIORITIZATION MODEL TRAINING")
    print("="*70)
    
    # Load preprocessed data
    print("\n📂 Loading preprocessed data...")
    X_train = pd.read_csv('../../data/processed/X_train.csv')
    X_test = pd.read_csv('../../data/processed/X_test.csv')
    y_train = pd.read_csv('../../data/processed/y_train.csv').values.ravel()
    y_test = pd.read_csv('../../data/processed/y_test.csv').values.ravel()
    
    print(f"✅ Training samples: {len(X_train):,}")
    print(f"✅ Testing samples: {len(X_test):,}")
    print(f"✅ Features: {len(X_train.columns)}")
    
    # Initialize model
    print("\n🔧 Initializing Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=100,        # Number of trees
        max_depth=20,            # Maximum depth
        min_samples_split=10,    # Minimum samples to split
        min_samples_leaf=4,      # Minimum samples per leaf
        random_state=42,
        n_jobs=-1,               # Use all CPU cores
        verbose=1                # Show progress
    )
    
    print("✅ Model initialized")
    print(f"   - Trees: 100")
    print(f"   - Max depth: 20")
    print(f"   - Min samples split: 10")
    
    # Train model
    print("\n🚀 Training model...")
    print("   (This may take 2-3 minutes...)")
    model.fit(X_train, y_train)
    print("✅ Training complete!")
    
    # Make predictions
    print("\n🔮 Making predictions on test set...")
    y_pred = model.predict(X_test)
    print("✅ Predictions complete!")
    
    # Evaluate
    print("\n📊 EVALUATION RESULTS")
    print("="*70)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n🎯 Overall Accuracy: {accuracy * 100:.2f}%")
    
    # Classification report
    print("\n📋 Detailed Classification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['CRITICAL', 'HIGH', 'INFO', 'LOW', 'MEDIUM']))
    
    # Confusion matrix
    print("\n🔢 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, 
                         labels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'])
    print(cm)
    
    # Plot confusion matrix
    print("\n📊 Creating confusion matrix visualization...")
    os.makedirs('../../results', exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
               xticklabels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'],
               yticklabels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'],
               cbar_kws={'label': 'Count'})
    plt.title('Confusion Matrix - Alert Prioritization Model\n', fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig('../../results/04_confusion_matrix.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: results/04_confusion_matrix.png")
    plt.close()
    
    # Feature importance
    print("\n⭐ Analyzing feature importance...")
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 15 Most Important Features:")
    print(feature_importance.head(15).to_string(index=False))
    
    # Plot feature importance
    plt.figure(figsize=(12, 8))
    top_15 = feature_importance.head(15)
    plt.barh(range(len(top_15)), top_15['importance'], color='steelblue')
    plt.yticks(range(len(top_15)), top_15['feature'])
    plt.xlabel('Importance Score', fontsize=12)
    plt.title('Top 15 Feature Importance - Alert Prioritization\n', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig('../../results/05_feature_importance.png', dpi=300, bbox_inches='tight')
    print("\n✅ Saved: results/05_feature_importance.png")
    plt.close()
    
    # Priority distribution comparison
    print("\n📊 Creating priority distribution comparison...")
    
    priority_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
    actual_counts = pd.Series(y_test).value_counts()[priority_order]
    predicted_counts = pd.Series(y_pred).value_counts()[priority_order]
    
    x = np.arange(len(priority_order))
    width = 0.35
    
    plt.figure(figsize=(12, 6))
    plt.bar(x - width/2, actual_counts, width, label='Actual', alpha=0.8, color='steelblue')
    plt.bar(x + width/2, predicted_counts, width, label='Predicted', alpha=0.8, color='coral')
    plt.xlabel('Priority Level', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.title('Actual vs Predicted Priority Distribution\n', fontsize=14, fontweight='bold')
    plt.xticks(x, priority_order)
    plt.legend()
    plt.tight_layout()
    plt.savefig('../../results/06_priority_distribution_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: results/06_priority_distribution_comparison.png")
    plt.close()
    
    # Save model
    print("\n💾 Saving trained model...")
    os.makedirs('../../models', exist_ok=True)
    model_path = '../../models/alert_prioritization_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model saved to: {model_path}")
    
    # Save model performance metrics
    print("\n📝 Saving performance metrics...")
    metrics = {
        'accuracy': accuracy,
        'n_samples_train': len(X_train),
        'n_samples_test': len(X_test),
        'n_features': len(X_train.columns),
        'feature_names': X_train.columns.tolist()
    }
    
    with open('../../models/model_metrics.pkl', 'wb') as f:
        pickle.dump(metrics, f)
    print("✅ Metrics saved to: models/model_metrics.pkl")
    
    # Create summary report
    print("\n📄 Creating summary report...")
    with open('../../results/model_training_summary.txt', 'w') as f:
        f.write("ALERT PRIORITIZATION MODEL - TRAINING SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Model Type: Random Forest Classifier\n")
        f.write(f"Training Samples: {len(X_train):,}\n")
        f.write(f"Testing Samples: {len(X_test):,}\n")
        f.write(f"Number of Features: {len(X_train.columns)}\n")
        f.write(f"Overall Accuracy: {accuracy * 100:.2f}%\n\n")
        f.write("Top 10 Important Features:\n")
        for i, row in feature_importance.head(10).iterrows():
            f.write(f"  {row['feature']:30} : {row['importance']:.4f}\n")
    
    print("✅ Summary saved to: results/model_training_summary.txt")
    
    print("\n" + "="*70)
    print("✅ MODEL TRAINING COMPLETE!")
    print("="*70)
    print(f"\n📊 Final Accuracy: {accuracy * 100:.2f}%")
    print(f"📁 Model saved: models/alert_prioritization_model.pkl")
    print(f"📊 Visualizations: results/ folder (3 new files)")
    
    return model, accuracy


if __name__ == "__main__":
    model, accuracy = train_alert_prioritization_model()