import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, classification_report
import joblib
import numpy as np

# Data collection
df = pd.read_csv('modules/test.csv')

# Handle blank
df = df.dropna(subset=['Class Index'])

df['Class Index'] = df['Class Index'].astype(int)
label_mapping = {
    1: 'World',
    2: 'Sports',
    3: 'Business',
    4: 'Sci/Tech'
}
df['Class Index'] = df['Class Index'].map(label_mapping)
df['Text'] = df['Title'] + ' ' + df['Description']

# Features
X = df['Text']
y = df['Class Index']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define individual models
model_nb = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
    ('clf', MultinomialNB())
])
model_lr = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
    ('clf', LogisticRegression(max_iter=1000, class_weight='balanced')) 
])
model_svc = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
    ('clf', SVC(probability=True, class_weight='balanced')) 
])

#parameter grids for individual models
param_grid_nb = {
    'tfidf__max_features': [1000, 5000, 10000],
    'clf__alpha': [0.01, 0.1, 1, 10]
}

param_grid_lr = {
    'tfidf__max_features': [1000, 5000, 10000],
    'clf__C': [0.1, 1, 10]
}

param_grid_svc = {
    'tfidf__max_features': [1000, 5000, 10000],
    'clf__C': [0.1, 1, 10],
    'clf__kernel': ['linear', 'rbf']
}

# Grid search for each model
grid_search_nb = GridSearchCV(model_nb, param_grid_nb, cv=5, n_jobs=-1, verbose=1)
grid_search_lr = GridSearchCV(model_lr, param_grid_lr, cv=5, n_jobs=-1, verbose=1)
grid_search_svc = GridSearchCV(model_svc, param_grid_svc, cv=5, n_jobs=-1, verbose=1)

# Fit grid search models
grid_search_nb.fit(X_train, y_train)
grid_search_lr.fit(X_train, y_train)
grid_search_svc.fit(X_train, y_train)

# Best models
best_model_nb = grid_search_nb.best_estimator_
best_model_lr = grid_search_lr.best_estimator_
best_model_svc = grid_search_svc.best_estimator_

#Voting Classifier with the best models
voting_clf = VotingClassifier(estimators=[
    ('nb', best_model_nb),
    ('lr', best_model_lr),
    ('svc', best_model_svc)
], voting='soft')

# Train the ensemble model
voting_clf.fit(X_train, y_train)

# Evaluate the model
y_pred = voting_clf.predict(X_test)

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the model
joblib.dump(voting_clf, 'news_classifier_model.pkl')

print("Model accuracy:", voting_clf.score(X_test, y_test))


