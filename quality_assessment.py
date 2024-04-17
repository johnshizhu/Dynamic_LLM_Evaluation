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

def coherence(documents, num_topics, passes, iterations, random_state=42):
    '''
        Calcualtes coherence score using Latent Dirichlet Allocation from:
        - (List) documents, list of lists of tokens, each list is a response / prompt
        - (int) num_topics, defines the number of distinct topics that the LDA model should identify in the corpus
        - (int) passes, the number of full passes of the LDA algorithm over the whole corpus
        - (int) interations, the max number of iterations the model is allowed for each document in a single pass. 
    '''
    dictionary = corpora.Dictionary(documents)
    corpus = [dictionary.doc2bow(document) for document in documents]
    lda_model = LdaModel(corpus=corpus, 
                         id2word=dictionary,
                         iterations=iterations,
                         num_topics=num_topics,
                         passes=passes,
                         random_state=random_state)
    
    coherence_model = CoherenceModel(model=lda_model, 
                                     texts=documents,
                                     dicitonary=dictionary,
                                     coherence='c_v')
    
    coherence_score = coherence_model.get_coherence()

    return coherence_score 