import time

from flask import Flask

app = Flask(__name__)

import sys
from itertools import zip_longest
from pathlib import Path

import spacy
from germalemma import GermaLemma
from spacy_iwnlp import spaCyIWNLP

# setup IWNLP
nlp = spacy.load('de', disable=['parser', 'ner'])
iwnlp = spaCyIWNLP(
    lemmatizer_path='IWNLP.Lemmatizer_20181001.json')
nlp.add_pipe(iwnlp)

# setup GermaLemma
lemmatizer = GermaLemma()


def escape_text(text):
    return text.replace("\n", "\\n")


def unescape_text(text):
    return text.replace("\\n", "\n")


def replace_with_lemma(token_text, iwnlp_lemmas, pos):
    # iwnlp_lemmas is list, this is single string
    other_canditate = None

    if pos == 'NOUN':
        other_canditate = lemmatizer.find_lemma(token_text, 'N')

    if pos == 'VERB' or pos == 'AUX':
        other_canditate = lemmatizer.find_lemma(token_text, 'V')

    if pos == 'ADJ':
        other_canditate = lemmatizer.find_lemma(token_text, 'ADJ')

    if pos == 'ADV':
        other_canditate = lemmatizer.find_lemma(token_text, 'ADV')

    if iwnlp_lemmas is None:
        if other_canditate is None:
            # default return text
            return token_text
        else:
            # if there are no  iwnlp_lemmas from IWNLP, we take the one from Germ Lemma
            return other_canditate
    else:
        if other_canditate != token_text and other_canditate in iwnlp_lemmas:
            return other_canditate  # both found the same
        else:
            return iwnlp_lemmas[0]  # always first to be reproducible


def process_token(token_text, iwnlp_lemmas, pos, ws):
    # process and make some that some information about the case remains
    prc_tkn = replace_with_lemma(token_text, iwnlp_lemmas, pos)
    res_word = ''
    for x, y in zip_longest(list(prc_tkn), list(token_text), fillvalue=''):
        # keep orginal case if the characters are the same
        if x.lower() == y.lower():
            res_word += y
        else:
            res_word += x

    # remain upper case
    if token_text.isupper() and not res_word.isupper():
        res_word = res_word.upper()

    # remain title case
    if token_text.istitle() and not res_word.istitle():
        res_word = res_word.title()

    # prepend original whitespace
    return res_word + ws


def _lemma(doc):
    lemmatized = [process_token(str(token), token._.iwnlp_lemmas, token.pos_, token.whitespace_) for token in doc]
    return ''.join(lemmatized)


def lemma(text):
    doc = nlp(text)
    for token in doc:
        print('POS: {}\tIWNLP:{}'.format(token.pos_, token._.iwnlp_lemmas))
    return _lemma(doc)


def process_file(path, per_line, escape):
    if per_line:
        with open(Path('/output/' + path.name), 'w') as outfile:
            with open(path) as infile:
                # process docs with spacy.pipe for performance reasons
                lines = []
                for text in infile:
                    if escape:
                        text = text.strip()
                        text = unescape_text(text)
                    lines.append(text)
                docs = nlp.pipe(lines)
                results = []
                for d in docs:
                    results.append(_lemma(d))

                if escape:
                    results = [escape_text(txt) for txt in results]
                    results = '\n'.join(results)
                else:
                    # no need to add newlines because there are still part of the spacy whitespace
                    results = ''.join(results)
                outfile.write(results)

    else:
        text = path.read_text()
        Path('/output/' + path.name).write_text(lemma(text))


@app.route('/')
def hello():
    results = lemma("Was ist das für ein Leben?")
    return results+ format(count)
  
app.run(debug=True, host='0.0.0.0')
