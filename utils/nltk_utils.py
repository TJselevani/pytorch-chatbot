import numpy as np
import nltk
import string
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


# nltk.download("punkt")
# nltk.download("wordnet")
# nltk.download("stopwords")

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english", "swahili"))


def tokenize(sentence):
    """
    split sentence into array of words/tokens
    a token can be a word or punctuation character, or number
    """
    return nltk.word_tokenize(sentence)


def stem(word):
    """
    stemming = find the root form of the word
    examples:
    words = ["organize", "organizes", "organizing"]
    words = [stem(w) for w in words]
    -> ["organ", "organ", "organ"]
    """
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, words):
    """
    return bag of words array:
    1 for each known word that exists in the sentence, 0 otherwise
    example:
    sentence = ["hello", "how", "are", "you"]
    words = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
    bog   = [  0 ,    1 ,    0 ,   1 ,    0 ,    0 ,      0]
    """
    # stem each word
    sentence_words = [stem(word) for word in tokenized_sentence]
    # initialize bag with 0 for each word
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words:
            bag[idx] = 1

    return bag


def preprocess_text(sentence):
    """Ensuring that words are reduced to their base form to improve model generalization."""
    """Removing unnecessary words that do not contribute to intent detection."""
    tokens = nltk.word_tokenize(sentence)  # Tokenization
    tokens = [
        lemmatizer.lemmatize(word.lower())
        for word in tokens
        if word not in string.punctuation
    ]  # Lemmatization
    tokens = [word for word in tokens if word not in stop_words]  # Stopword Removal
    return tokens


def create_bow(sentence, words):
    """Modifies to you create the Bag-of-Words representation:"""
    sentence_words = preprocess_text(sentence)
    bag = [1 if w in sentence_words else 0 for w in words]
    return np.array(bag)
