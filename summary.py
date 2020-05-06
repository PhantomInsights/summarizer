"""
This script extracts and ranks the sentences and words of an article.

IT is inspired by the tf-idf algorithm.
"""

from collections import Counter

import spacy

# The stop words files.
ES_STOPWORDS_FILE = "./assets/stopwords-es.txt"
EN_STOPWORDS_FILE = "./assets/stopwords-en.txt"

# The number of sentences we need.
NUMBER_OF_SENTENCES = 5

# The number of top words we need.
NUMBER_OF_TOP_WORDS = 5

# Multiplier for uppercase and long words.
IMPORTANT_WORDS_MULTIPLIER = 2.5

# Financial sentences often are more important than others.
FINANCIAL_SENTENCE_MULTIPLIER = 1.5

# The minimum number of characters needed for a line to be valid.
LINE_LENGTH_THRESHOLD = 150

# It is very important to add spaces on these words.
# Otherwise it will take into account partial words.
COMMON_WORDS = {
    " ", "  ", "\xa0", "#", ",", "|", "-", "‘", "’", ";", "(", ")", ".", ":", "¿", "?", '“', "/",
    '”', '"', "'", "%", "•", "«", "»", "foto", "photo", "video", "redacción", "nueve", "diez", "cien",
    "mil", "miles", "ciento", "cientos", "millones", "vale"
}

# These words increase the score of a sentence. They don't require whitespaces around them.
FINANCIAL_WORDS = ["$", "€", "£", "pesos", "dólar", "libras", "euros",
                   "dollar", "pound", "mdp", "mdd"]


# Don't forget to specify the correct model for your language.
NLP = spacy.load("es_core_news_sm")


def add_extra_words():
    """Adds the title and uppercase forms of all words to COMMON_WORDS.

    We parse local copies of stop words downloaded from the following repositories:

    https://github.com/stopwords-iso/stopwords-es
    https://github.com/stopwords-iso/stopwords-en
    """

    with open(ES_STOPWORDS_FILE, "r", encoding="utf-8") as temp_file:
        for word in temp_file.read().splitlines():
            COMMON_WORDS.add(word)

    with open(EN_STOPWORDS_FILE, "r", encoding="utf-8") as temp_file:
        for word in temp_file.read().splitlines():
            COMMON_WORDS.add(word)


add_extra_words()


def get_summary(article):
    """Generates the top words and sentences from the article text.

    Parameters
    ----------
    article : str
        The article text.

    Returns
    -------
    dict
        A dict containing the title of the article, reduction percentage, top words and the top scored sentences.

    """

    # Now we prepare the article for scoring.
    cleaned_article = clean_article(article)

    # We start the NLP process.
    doc = NLP(cleaned_article)

    article_sentences = [sent for sent in doc.sents]

    words_of_interest = [
        token.text for token in doc if token.lower_ not in COMMON_WORDS]

    # We use the Counter class to count all words ocurrences.
    scored_words = Counter(words_of_interest)

    for word in scored_words:

        # We add bonus points to words starting in uppercase and are equal or longer than 4 characters.
        if word[0].isupper() and len(word) >= 4:
            scored_words[word] *= IMPORTANT_WORDS_MULTIPLIER

        # If the word is a number we punish it by settings its points to 0.
        if word.isdigit():
            scored_words[word] = 0

    top_sentences = get_top_sentences(article_sentences, scored_words)
    top_sentences_length = sum([len(sentence) for sentence in top_sentences])
    reduction = 100 - (top_sentences_length / len(cleaned_article)) * 100

    summary_dict = {
        "top_words": get_top_words(scored_words),
        "top_sentences": top_sentences,
        "reduction": reduction,
        "article_words": " ".join(words_of_interest)
    }

    return summary_dict


def clean_article(article_text):
    """Cleans and reformats the article text.

    Parameters
    ----------
    article_text : str
        The article string.

    Returns
    -------
    str
        The cleaned up article.

    """

    # We divide the script into lines, this is to remove unnecessary whitespaces.
    lines_list = list()

    for line in article_text.split("\n"):

        # We remove whitespaces.
        stripped_line = line.strip()

        # If the line is too short we ignore it.
        if len(stripped_line) >= LINE_LENGTH_THRESHOLD:
            lines_list.append(stripped_line)

    # Now we have the article fully cleaned.
    return "   ".join(lines_list)


def get_top_words(scored_words):
    """Gets the top scored words from the prepared article.

    Parameters
    ----------
    scored_words : collections.Counter
        A Counter containing the article words and their scores.

    Returns
    -------
    list
        An ordered list with the top words.

    """

    # Once we have our words scored it's time to get top ones.
    top_words = list()

    for word, score in scored_words.most_common():

        add_to_list = True

        # We avoid duplicates by checking if the word already is in the top_words list.
        if word.upper() not in [item.upper() for item in top_words]:

            # Sometimes we have the same word but in plural form, we skip the word when that happens.
            for item in top_words:
                if word.upper() in item.upper() or item.upper() in word.upper():
                    add_to_list = False

            if add_to_list:
                top_words.append(word)

    return top_words[0:NUMBER_OF_TOP_WORDS]


def get_top_sentences(article_sentences, scored_words):
    """Gets the top scored sentences from the cleaned article.

    Parameters
    ----------
    cleaned_article : str
        The original article after it has been cleaned and reformatted.

    scored_words : collections.Counter
        A Counter containing the article words and their scores.

    Returns
    -------
    list
        An ordered list with the top sentences.

    """

    # Now its time to score each sentence.
    scored_sentences = list()

    # We take a reference of the order of the sentences, this will be used later.
    for index, sent in enumerate(article_sentences):

        # In some edge cases we have duplicated sentences, we make sure that doesn't happen.
        if sent.text not in [sent for score, index, sent in scored_sentences]:
            scored_sentences.append(
                [score_line(sent, scored_words), index, sent.text])

    top_sentences = list()
    counter = 0

    for score, index, sentence in sorted(scored_sentences, reverse=True):

        if counter >= NUMBER_OF_SENTENCES:
            break

        # When the article is too small the sentences may come empty.
        if len(sentence) >= 3:

            # We clean the sentence and its index so we can sort in chronological order.
            top_sentences.append([index, sentence])
            counter += 1

    return [sentence for index, sentence in sorted(top_sentences)]


def score_line(line, scored_words):
    """Calculates the score of the given line using the word scores.

    Parameters
    ----------
    line : spacy.tokens.span.Span
        A tokenized sentence from the article.

    scored_words : collections.Counter
        A Counter containing the article words and their scores.

    Returns
    -------
    int
        The total score of all the words in the sentence.

    """

    # We remove the common words.
    cleaned_line = [
        token.text for token in line if token.lower_ not in COMMON_WORDS]

    # We now sum the total number of ocurrences for all words.
    temp_score = 0

    for word in cleaned_line:
        temp_score += scored_words[word]

    # We apply a bonus score to sentences that contain financial information.
    line_lowercase = line.text.lower()

    for word in FINANCIAL_WORDS:
        if word in line_lowercase:
            temp_score *= FINANCIAL_SENTENCE_MULTIPLIER
            break

    return temp_score
