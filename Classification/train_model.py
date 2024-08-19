import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import confusion_matrix, classification_report
import joblib

#data collection
df = pd.read_csv('test.csv')

#print(df.info())

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

#features
X = df['Text']
y = df['Class Index']

#training
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#Naive Bayes classifier
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),  
    ('clf', MultinomialNB())
])

#hyperparameter grid
parameters = {
    'tfidf__max_features': [1000, 5000, 10000],
    'clf__alpha': [0.1, 1, 10]
}

#grid search with cross-validation
grid_search = GridSearchCV(pipeline, parameters, cv=5, n_jobs=-1, verbose=1)
grid_search.fit(X_train, y_train)

best_model = grid_search.best_estimator_

y_pred = best_model.predict(X_test)

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("Classification Report:")
print(classification_report(y_test, y_pred))

joblib.dump(best_model, 'news_classifier_model.pkl')

print("Model accuracy:", best_model.score(X_test, y_test))

"""our model shows a strong overall accuracy of 88.2%, making it suitable for our classification tasks with a good balance between precision and recall"""