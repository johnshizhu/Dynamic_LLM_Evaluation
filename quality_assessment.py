import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer 
from nltk.stem import WordNetLemmatizer
import gensim
from gensim import corpora
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel

import string

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

def preprocess_text(text):

    # Initialize lemmatizer
    lemmatizer = WordNetLemmatizer()

    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    
    cleaned_tokens = []
    for token in tokens:
        # Remove punctuation and numbers
        token = ''.join([char for char in token if char not in string.punctuation and not char.isdigit()])
        if token:
            # Convert to lowercase to handle case inconsistencies
            token = token.lower()
            if token not in stop_words:
                # Apply stemming or lemmatization
                lemmatized_token = lemmatizer.lemmatize(token)  # Use lemmatizer
                cleaned_tokens.append(lemmatized_token)  # Choose one: stemmed_token or lemmatized_token

    return cleaned_tokens

def coherence(documents):
    '''
        Calcualtes coherence score from:
        - (List) documents, list of list of tokens, each list is a response / prompt
    '''
    dictionary = corpora.Dictionary(documents)
    corpus = [dictionary.doc2bow(document) for document in documents]
    lda_model = LdaModel(corpus=corpus, num_topics=2)


    return coherence_score 