import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.cross_decomposition import PLSRegression
import matplotlib.pyplot as plt

# Load the CSV with experiment results
df = pd.read_csv(r"C:\Chemistry\Compound Lists\40mix\VCONF_outputs\Experiments\experiment_log.csv")

# Select the settings and results (target variables) for PCA, RandomForest, and PLS
X = df[['NUM_STEPS', 'SEARCH_WIDTH', 'ENERGY_CUTOFF',
        'DISTANCE_TOLERANCE', 'ANGLE_TOLERANCE', 'ENERGY_TOLERANCE']]

Y = df[['Unique Conformers', 'Min Energy', 'Max Energy', 'Avg Energy', 'Energy Slope', 'R^2']]

# Scale the features before running PCA and other algorithms
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# # ---- PCA Analysis ---- #
# # Initialize PCA and fit it to the scaled data
# pca = PCA(n_components=6)  # Set the number of components to retain the full dimensionality initially
# pca_result = pca.fit_transform(X_scaled)
#
# # Display how much variance is explained by each principal component
# explained_variance = pca.explained_variance_ratio_
# print(f"Explained variance ratio of each principal component: {explained_variance}")
#
# # Plot the explained variance to decide how many components to keep
# plt.figure(figsize=(8, 5))
# plt.bar(range(1, len(explained_variance) + 1), explained_variance, alpha=0.5, align='center', label='Individual explained variance')
# plt.step(range(1, len(explained_variance) + 1), np.cumsum(explained_variance), where='mid', label='Cumulative explained variance')
# plt.ylabel('Explained variance ratio')
# plt.xlabel('Principal components')
# plt.legend(loc='best')
# plt.show()
#
# # Get the loading scores for each feature (the contribution of each feature to each component)
# loading_scores = pd.DataFrame(pca.components_.T, index=X.columns, columns=[f'PC{i+1}' for i in range(pca.n_components_)])
# print("Loading Scores (Feature Contributions):")
# print(loading_scores)
#
# # Project original data into the reduced PCA space for further analysis
# pca_df = pd.DataFrame(pca_result, columns=[f'PC{i+1}' for i in range(pca.n_components_)])
# pca_df['Unique Conformers'] = df['Unique Conformers']
# pca_df['Min Energy'] = df['Min Energy']
# pca_df['Max Energy'] = df['Max Energy']
# pca_df['Avg Energy'] = df['Avg Energy']
# pca_df['Energy Slope'] = df['Energy Slope']
# pca_df['R^2'] = df['R^2']
#
# # Look at the correlation of each PC with the target outcomes
# correlations = pca_df.corr()
# print("Correlation between Principal Components and Target Variables:")
# print(correlations)
#
# # Plot the first two PCs for visualization
# plt.figure(figsize=(10, 7))
# plt.scatter(pca_df['PC1'], pca_df['PC2'], c=pca_df['Min Energy'], cmap='viridis')
# plt.colorbar(label='Min Energy')
# plt.xlabel('Principal Component 1')
# plt.ylabel('Principal Component 2')
# plt.title('PCA of Experimental Settings')
# plt.show()

# ---- Random Forest Feature Importance ---- #
# Using RandomForestRegressor to determine feature importance for each target variable
print("\nRandom Forest Feature Importances:")
for target in Y.columns:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, df[target])
    feature_importance = pd.Series(model.feature_importances_, index=X.columns)
    print(f"\nFeature importances for {target}:")
    print(feature_importance)
    feature_importance.plot(kind='bar', title=f'Feature importance for {target}')
    plt.ylabel('Importance')
    plt.show()

# ---- Partial Least Squares (PLS) Regression ---- #
# PLS can be used to directly correlate X (settings) with Y (target outcomes)
print("\nPartial Least Squares (PLS) Regression:")
pls = PLSRegression(n_components=2)
pls.fit(X_scaled, Y)
pls_coefficients = pd.DataFrame(pls.coef_, index=X.columns, columns=Y.columns)
print("PLS Coefficients (Feature Contributions):")
print(pls_coefficients)

# Plot the relationship between predicted and actual values for one of the target outcomes (e.g., Min Energy)
Y_pred = pls.predict(X_scaled)
plt.figure(figsize=(10, 7))
plt.scatter(Y['Min Energy'], Y_pred[:, 1], c='blue', label='Predicted vs Actual')
plt.plot([min(Y['Min Energy']), max(Y['Min Energy'])], [min(Y['Min Energy']), max(Y['Min Energy'])], color='red')
plt.xlabel('Actual Min Energy')
plt.ylabel('Predicted Min Energy')
plt.title('PLS Regression: Predicted vs Actual Min Energy')
plt.legend()
plt.show()
