import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, precision_recall_curve
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE
import sys

# Debugging: Track script start
print("Script started...")

try:
    # Load your stock data (CSV file, for example)
    print("Loading data...")
    df = pd.read_csv('stock_data.csv', parse_dates=['Date'])
    print("Data loaded successfully!")
    print(f"Dataset shape: {df.shape}")

    df.set_index('Date', inplace=True)

    # Feature Engineering
    print("Starting feature engineering...")
    # Previous day's close price
    df['Prev Close'] = df['Close'].shift(1)

    # Moving Averages
    df['50 Day MA'] = df['Close'].rolling(window=50).mean()
    df['200 Day MA'] = df['Close'].rolling(window=200).mean()

    # RSI (Relative Strength Index)
    window_length = 14
    delta = df['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window_length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window_length).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['20 Day MA'] = df['Close'].rolling(window=20).mean()
    df['20 Day StdDev'] = df['Close'].rolling(window=20).std()
    df['Upper Band'] = df['20 Day MA'] + (df['20 Day StdDev'] * 2)
    df['Lower Band'] = df['20 Day MA'] - (df['20 Day StdDev'] * 2)

    # Day of the Week (Temporal Feature)
    df['Day of Week'] = df.index.dayofweek

    # Volume Trend (relative change in volume)
    df['Volume Change'] = df['Volume'].pct_change()

    # Target Label: 1 if next day's close is higher, 0 otherwise
    df['Price Change'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)

    # Check missing values before cleaning
    print("Missing values in each column before cleaning:")
    print(df.isnull().sum())

    # Handle missing values using SimpleImputer (mean strategy for numerical columns)
    imputer = SimpleImputer(strategy='mean')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    
    # Verify data shape after imputing missing values
    print(f"Dataset shape after imputing missing values: {df_imputed.shape}")

    # Define features (X) and target (y)
    features = ['Prev Close', '50 Day MA', '200 Day MA', 'RSI', 'Upper Band', 
                'Lower Band', 'Day of Week', 'Volume Change']
    X = df_imputed[features]
    y = df_imputed['Price Change']
    print("Feature and target sets defined.")
    print(f"Feature shape: {X.shape}, Target shape: {y.shape}")

    # Check if there's enough data for TimeSeriesSplit
    if len(df_imputed) < 6:
        print("Not enough data for TimeSeriesSplit (must be at least 6 samples). Exiting.")
        sys.exit(1)

    # Split data using TimeSeriesSplit (walk-forward validation)
    tscv = TimeSeriesSplit(n_splits=5)
    scaler = StandardScaler()
    smote = SMOTE(random_state=42)
    scores = []

    print("Starting TimeSeriesSplit...")
    for train_index, test_index in tscv.split(X):
        print(f"Processing split: Train {len(train_index)}, Test {len(test_index)}")
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        # Handle imbalance with SMOTE
        print("Applying SMOTE...")
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"SMOTE applied. Resampled Train shape: {X_train.shape}, {y_train.shape}")

        # Scale the features
        print("Scaling features...")
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train the model (Gradient Boosting)
        print("Training model...")
        model = GradientBoostingClassifier(random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate the model
        print("Evaluating model...")
        y_pred = model.predict(X_test_scaled)
        y_pred_prob = model.predict_proba(X_test_scaled)[:, 1]
        accuracy = accuracy_score(y_test, y_pred)
        auc_score = roc_auc_score(y_test, y_pred_prob)
        scores.append((accuracy, auc_score))
        print(f"Split results - Accuracy: {accuracy:.2f}, AUC: {auc_score:.2f}")

    # average scores
    avg_accuracy = np.mean([score[0] for score in scores])
    avg_auc = np.mean([score[1] for score in scores])
    print(f'Average Accuracy: {avg_accuracy:.2f}')
    print(f'Average AUC-ROC: {avg_auc:.2f}')

    #Model Training
    print("Training final model on full dataset...")
    X_train_scaled = scaler.fit_transform(X)
    y_train = y
    X_train, y_train = smote.fit_resample(X_train_scaled, y_train)
    final_model = GradientBoostingClassifier(random_state=42)
    final_model.fit(X_train, y_train)

    print("Generating feature importance plot...")
    importances = final_model.feature_importances_
    plt.barh(features, importances)
    plt.title("Feature Importance")
    plt.xlabel("Importance")
    plt.ylabel("Features")
    plt.show()

    print("Generating predictions for backtesting...")
    df_imputed['Prediction'] = final_model.predict(scaler.transform(X))
    plt.plot(df_imputed['Close'], label='Actual Prices')
    plt.plot(df_imputed['Prediction'], label='Predicted Movements', alpha=0.7)
    plt.legend()
    plt.title("Stock Price and Predicted Movements")
    plt.show()

except FileNotFoundError as e:
    print(f"File not found: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("Script completed.")
