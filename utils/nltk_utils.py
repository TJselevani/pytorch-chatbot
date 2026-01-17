"""
NLTK utilities for text processing.
"""

import nltk
import string
import numpy as np

from nltk.stem.porter import PorterStemmer

from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")
    nltk.download("punkt-tab")
    nltk.download("wordnet")
    nltk.download("stopwords")

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english", "swahili"))


def tokenize(sentence):
    """
    Split sentence into array of words/tokens.

    Args:
        sentence: String to tokenize

    Returns:
        List of tokens
    """
    return nltk.word_tokenize(sentence.lower())


def stem(word):
    """
    Stemming: find the root form of the word.

    Examples:
        words = ["organize", "organizes", "organizing"]
        stemmed = [stem(w) for w in words]
        # -> ["organ", "organ", "organ"]

    Args:
        word: Word to stem

    Returns:
        Stemmed word
    """
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, words):
    """
    Return bag of words array:
    1 for each known word that exists in the sentence, 0 otherwise.

    Example:
        sentence = ["hello", "how", "are", "you"]
        words = ["hi", "hello", "I", "you", "bye", "thank", "cool"]
        bog = [0, 1, 0, 1, 0, 0, 0]

    Args:
        tokenized_sentence: List of tokens
        words: List of vocabulary words

    Returns:
        Numpy array of bag of words
    """
    # Stem each word
    sentence_words = [stem(word) for word in tokenized_sentence]

    # Initialize bag with 0 for each word
    bag = np.zeros(len(words), dtype=np.float32)

    for idx, w in enumerate(words):
        if w in sentence_words:
            bag[idx] = 1

    return bag


def preprocess_text(text):
    if isinstance(text, list):  # Convert list to a string if needed
        text = " ".join(text)

    words = nltk.word_tokenize(text.lower())
    words = [lemmatizer.lemmatize(word) for word in words if word.isalnum()]
    return words


def pre_process_text(sentence):
    """
    Preprocesses a given sentence by:
    1. Ensuring words are reduced to their base form (lemmatization) for better generalization.
    2. Removing punctuation and stopwords to focus on meaningful content.

    Args:
        sentence (str or list): The input sentence or list of words.

    Returns:
        list: A list of cleaned and processed words.
    """
    if isinstance(sentence, list):
        sentence = " ".join(sentence)  # Convert list to string if needed

    tokens = nltk.word_tokenize(sentence)  # Tokenization
    tokens = [
        lemmatizer.lemmatize(word.lower())
        for word in tokens
        if word not in string.punctuation  # Remove punctuation
    ]
    tokens = [word for word in tokens if word not in stop_words]  # Stopword Removal

    return tokens


def create_bow(sentence, words):
    """Modifies to you create the Bag-of-Words representation:"""
    sentence_words = preprocess_text(sentence)
    bag = [1 if w in sentence_words else 0 for w in words]
    return np.array(bag)


def augment_sentence(sentence):
    words = sentence.split()
    augmented = []
    for word in words:
        synonyms = wordnet.synsets(word)
        if synonyms:
            synonym = synonyms[0].lemmas()[0].name()
            augmented.append(synonym)
        else:
            augmented.append(word)
    return " ".join(augmented)
