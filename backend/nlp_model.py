from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import numpy as np

class NLPModel:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.model = LogisticRegression()

    def train(self, questions, answers):
        """Entraîne le modèle NLP sur les questions et réponses."""
        X = self.vectorizer.fit_transform(questions)
        self.model.fit(X, answers)

    def predict(self, question):
        """Prédit une réponse en fonction de la question."""
        question_vector = self.vectorizer.transform([question])
        return self.model.predict(question_vector)[0]

    def find_most_similar(self, questions, user_message):
        """Trouve la question la plus similaire à celle de l'utilisateur."""
        question_vectors = self.vectorizer.transform(questions)
        user_vector = self.vectorizer.transform([user_message])
        similarities = cosine_similarity(user_vector, question_vectors)
        most_similar_index = np.argmax(similarities)
        return questions[most_similar_index]