# -*- coding: utf-8 -*-
"""helper.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/164jUwJ0SB2xWtHqCNO3uAXclqhUFQaEP
"""
from tkinter import Image

import pandas as pd
import pickle
import re

# PyTorch dependencies
import torch
import torch.nn.functional as F
from tensorflow.python.keras.utils.vis_utils import plot_model
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader

# General dependencies
import numpy as np
import pandas as pd
from collections import defaultdict
from textwrap import wrap

# Sklearn dependencies
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")

import spacy

nlp = spacy.load("en_core_web_sm")

import pickle
import os

from transformers import *
from tensorflow.keras.preprocessing.sequence import pad_sequences

from tqdm.notebook import tqdm

import spacy

nlp = spacy.load("en_core_web_sm")

import os
import pandas as pd
import numpy as np
import re
import pickle
import sys
from tqdm import tqdm_notebook
from gensim.models import Word2Vec

import tensorflow._api.v2.compat.v1 as tf
# tensorflow.compat.v1 as tf
from tensorflow import keras
from tensorflow.keras import layers

# print(tf.__version__)
# import tensorflow_hub as hub

# Initialize session
sess = tf.compat.v1.Session()

from sklearn.model_selection import train_test_split
from tensorflow.python.keras.preprocessing.text import one_hot
from tensorflow.python.keras.preprocessing.sequence import pad_sequences
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers.core import Activation, Dropout, Dense
from tensorflow.python.keras.layers import Flatten
from tensorflow.python.keras.layers import GlobalMaxPooling1D
from tensorflow.python.keras.layers import Bidirectional
from tensorflow.python.keras.layers import TimeDistributed
from tensorflow.python.keras.layers.recurrent import LSTM
from tensorflow.python.keras.layers.embeddings import Embedding
from tensorflow.python.keras.preprocessing.text import Tokenizer
from tensorflow.python.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans

from tensorflow.python.keras.layers import Input, CuDNNLSTM, CuDNNGRU, Conv1D
from tensorflow.python.keras.layers import GlobalMaxPool1D, GlobalAveragePooling1D, MaxPooling1D
from tensorflow.python.keras.layers import Input, Conv2D, MaxPool2D
from tensorflow.python.keras.layers.merge import concatenate, average, add
from tensorflow.python.keras.layers import Reshape, SpatialDropout1D
from tensorflow.keras.optimizers import Adam
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.layers import Layer, InputSpec
from tensorflow.python.keras.layers import Lambda
from tensorflow.python.keras import initializers, regularizers, constraints, optimizers, layers
from tensorflow.python.keras import backend as K


## INPUT LOADER FOR BERT
def tokenize_sentences(sentences, tokenizer, max_seq_len=128):
    tokenized_sentences = []

    for sentence in tqdm(sentences):
        tokenized_sentence = tokenizer.encode(
            sentence,  # Sentence to encode.
            add_special_tokens=True,  # Add '[CLS]' and '[SEP]'
            max_length=max_seq_len,  # Truncate all sentences.
            truncation=True
        )

        tokenized_sentences.append(tokenized_sentence)

    return tokenized_sentences


def create_attention_masks(tokenized_and_padded_sentences):
    attention_masks = []

    for sentence in tokenized_and_padded_sentences:
        att_mask = [int(token_id > 0) for token_id in sentence]
        attention_masks.append(att_mask)

    return np.asarray(attention_masks)


def sentence2dependency(sentence, ret_sent=False):
    '''
    syntactic dependency: relation between tokens
    '''
    sentence = [token.dep_ for token in nlp(sentence)]
    if ret_sent:
        return ' '.join(sentence).lower()

    return sentence


def sentence2pos(sentence):
    '''
    simple POS tag
    '''
    sentence = [token.pos_ for token in nlp(sentence)]
    return sentence


def sentence2tag(sentence):
    '''
    detailed POS tag
    '''
    sentence = [token.tag_ for token in nlp(sentence)]
    return sentence


def sentence2token(sentence):
    '''
    simple tokenization
    '''
    sentence = [token.text for token in nlp(sentence)]
    return sentence


def get_ngrams(input_list, n, L2S=True):
    ngrams_list = list(zip(*[input_list[i:] for i in range(n)]))

    if L2S:
        for i in range(len(ngrams_list)):
            ngrams_list[i] = ' '.join(ngrams_list[i])

    return ngrams_list


def get_compound(list_tokens):
    for i in range(len(list_tokens)):
        list_tokens[i] = list_tokens[i].replace(" ", "_")

    return list_tokens


def sent2feature2ngram(sentence, feature="DEP", ngram=3):
    '''
    :params:
    sentence: input text
    feature: linguistic feature opted (DEFAULT: DEP)
    ngram: number of token level grams (DEFAULT: 3)
    '''
    if feature == "POS":
        sentence = get_compound(get_ngrams(sentence2pos(sentence), n=ngram))
    elif feature == "TAG":
        sentence = get_compound(get_ngrams(sentence2tag(sentence), n=ngram))
    else:
        sentence = get_compound(get_ngrams(sentence2dependency(sentence), n=ngram))

    return ' '.join(sentence)


def ParentPositions(sentence):
    '''
    return an array of indices
    : the ith index represents the position of the parent node in a dependency relation :
    '''
    doc = nlp(sentence)
    tidx_to_idx = {}  # CONVERT TOKENIZED INDEX TO ACTUAL INDEX
    for idx, token in enumerate(doc):
        tidx_to_idx[token.idx] = idx + 1

    parent_positions = []
    for token in doc:
        parent_positions.append(tidx_to_idx[token.head.idx])
    parent_positions = list(map(str, parent_positions))
    return ' '.join(parent_positions)


def loadEmbeddingModel(filename):
    embeddings_index = {}
    f = open(os.path.join('', filename), encoding="utf-8")
    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:])
        embeddings_index[word] = coefs
    f.close

    return embeddings_index


def load_tokenizer(pickle_name):
    '''
    loads tokenizer from pickle file
    '''
    with open('tokenizers/' + pickle_name, 'rb') as handle:
        tokenizer = pickle.load(handle)
    return tokenizer


def load_embedding_matrix(pickle_name):
    '''
    loads tokenizer from pickle file
    '''
    with open('embeddingMatrices/' + pickle_name, 'rb') as handle:
        embedding_matrix = pickle.load(handle)
    return embedding_matrix


# attention layer
def dot_product(x, kernel):
    """
    Wrapper for dot product operation, in order to be compatible with both
    Theano and Tensorflow
    Args:
        x (): input
        kernel (): weights
    Returns:
    """
    if K.backend() == 'tensorflow':
        return K.squeeze(K.dot(x, K.expand_dims(kernel)), axis=-1)
    else:
        return K.dot(x, kernel)


class AttentionWithContext(Layer):
    """
    Attention operation, with a context/query vector, for temporal data.
    Supports Masking.
    Follows the work of Yang et al. [https://www.cs.cmu.edu/~diyiy/docs/naacl16.pdf]
    "Hierarchical Attention Networks for Document Classification"
    by using a context vector to assist the attention
    # Input shape
        3D tensor with shape: `(samples, steps, features)`.
    # Output shape
        2D tensor with shape: `(samples, features)`.
    How to use:
    Just put it on top of an RNN Layer (GRU/LSTM/SimpleRNN) with return_sequences=True.
    The dimensions are inferred based on the output shape of the RNN.
    Note: The layer has been tested with Keras 2.0.6
    Example:
        model.add(LSTM(64, return_sequences=True))
        model.add(AttentionWithContext())
        # next add a Dense layer (for classification/regression) or whatever...
    """

    def __init__(self,
                 W_regularizer=None, u_regularizer=None, b_regularizer=None,
                 W_constraint=None, u_constraint=None, b_constraint=None,
                 bias=True, **kwargs):

        self.supports_masking = True
        self.init = initializers.get('glorot_uniform')

        self.W_regularizer = regularizers.get(W_regularizer)
        self.u_regularizer = regularizers.get(u_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.u_constraint = constraints.get(u_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        super(AttentionWithContext, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 3

        self.W = self.add_weight(shape=(input_shape[-1], input_shape[-1],),
                                 initializer=self.init,
                                 name='{}_W'.format(self.name),
                                 regularizer=self.W_regularizer,
                                 constraint=self.W_constraint)
        if self.bias:
            self.b = self.add_weight(shape=(input_shape[-1],),
                                     initializer='zero',
                                     name='{}_b'.format(self.name),
                                     regularizer=self.b_regularizer,
                                     constraint=self.b_constraint)

        self.u = self.add_weight(shape=(input_shape[-1],),
                                 initializer=self.init,
                                 name='{}_u'.format(self.name),
                                 regularizer=self.u_regularizer,
                                 constraint=self.u_constraint)

        super(AttentionWithContext, self).build(input_shape)

    def compute_mask(self, input, input_mask=None):
        # do not pass the mask to the next layers
        return None

    def call(self, x, mask=None):
        uit = dot_product(x, self.W)

        if self.bias:
            uit += self.b

        uit = K.tanh(uit)
        ait = dot_product(uit, self.u)

        a = K.exp(ait)

        # apply mask after the exp. will be re-normalized next
        if mask is not None:
            # Cast the mask to floatX to avoid float64 upcasting in theano
            a *= K.cast(mask, K.floatx())

        # in some cases especially in the early stages of training the sum may be almost zero
        # and this results in NaN's. A workaround is to add a very small positive number ε to the sum.
        # a /= K.cast(K.sum(a, axis=1, keepdims=True), K.floatx())
        a /= K.cast(K.sum(a, axis=1, keepdims=True) + K.epsilon(), K.floatx())

        a = K.expand_dims(a)
        weighted_input = x * a
        return K.sum(weighted_input, axis=1)

    def compute_output_shape(self, input_shape):
        return input_shape[0], input_shape[-1]


# tranformer layer
class MultiHeadSelfAttention(layers.Layer):
    def __init__(self, embed_dim, num_heads=8):
        super(MultiHeadSelfAttention, self).__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        if embed_dim % num_heads != 0:
            raise ValueError(
                f"embedding dimension = {embed_dim} should be divisible by number of heads = {num_heads}"
            )
        self.projection_dim = embed_dim // num_heads
        self.query_dense = layers.Dense(embed_dim)
        self.key_dense = layers.Dense(embed_dim)
        self.value_dense = layers.Dense(embed_dim)
        self.combine_heads = layers.Dense(embed_dim)

    def attention(self, query, key, value):
        score = tf.matmul(query, key, transpose_b=True)
        dim_key = tf.cast(tf.shape(key)[-1], tf.float32)
        scaled_score = score / tf.math.sqrt(dim_key)
        weights = tf.nn.softmax(scaled_score, axis=-1)
        output = tf.matmul(weights, value)
        return output, weights

    def separate_heads(self, x, batch_size):
        x = tf.reshape(x, (batch_size, -1, self.num_heads, self.projection_dim))
        return tf.transpose(x, perm=[0, 2, 1, 3])

    def call(self, inputs):
        # x.shape = [batch_size, seq_len, embedding_dim]
        batch_size = tf.shape(inputs)[0]
        query = self.query_dense(inputs)  # (batch_size, seq_len, embed_dim)
        key = self.key_dense(inputs)  # (batch_size, seq_len, embed_dim)
        value = self.value_dense(inputs)  # (batch_size, seq_len, embed_dim)
        query = self.separate_heads(
            query, batch_size
        )  # (batch_size, num_heads, seq_len, projection_dim)
        key = self.separate_heads(
            key, batch_size
        )  # (batch_size, num_heads, seq_len, projection_dim)
        value = self.separate_heads(
            value, batch_size
        )  # (batch_size, num_heads, seq_len, projection_dim)
        attention, weights = self.attention(query, key, value)
        attention = tf.transpose(
            attention, perm=[0, 2, 1, 3]
        )  # (batch_size, seq_len, num_heads, projection_dim)
        concat_attention = tf.reshape(
            attention, (batch_size, -1, self.embed_dim)
        )  # (batch_size, seq_len, embed_dim)
        output = self.combine_heads(
            concat_attention
        )  # (batch_size, seq_len, embed_dim)
        return output


class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = MultiHeadSelfAttention(embed_dim, num_heads)
        self.ffn = keras.Sequential(
            [layers.Dense(ff_dim, activation="relu"), layers.Dense(embed_dim), ]
        )
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training=True):
        attn_output = self.att(inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)


class TokenAndPositionEmbedding(layers.Layer):
    def __init__(self, maxlen, vocab_size_token, vocab_size_parentPos, embed_dim):
        super(TokenAndPositionEmbedding, self).__init__()
        self.token_emb = layers.Embedding(input_dim=vocab_size_token, output_dim=embed_dim)
        self.pos_emb = layers.Embedding(input_dim=maxlen, output_dim=embed_dim)
        self.parentPos_emb = layers.Embedding(input_dim=vocab_size_parentPos, output_dim=embed_dim)

    def call(self, x, y):
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        y = self.parentPos_emb(y)
        return x + y + positions


def ind_model_noisy(embed_dim, num_heads, ff_dim, maxlen, vocab_label, vocab_parent_pos):
    inputs_1 = layers.Input(shape=(maxlen,), name="label_noisy")
    inputs_2 = layers.Input(shape=(maxlen,), name="parent_pos_noisy")
    embedding_layer = TokenAndPositionEmbedding(maxlen, vocab_label, vocab_parent_pos, embed_dim)
    x = embedding_layer(inputs_1, inputs_2)
    transformer_block = TransformerBlock(embed_dim, num_heads, ff_dim)
    x = transformer_block(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    outputs = layers.Dense(2, activation="softmax")(x)

    model = keras.Model(inputs=[inputs_1, inputs_2], outputs=outputs)
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])

    model.summary()

    return model


def ind_model_semi(embed_dim, num_heads, ff_dim, maxlen, vocab_label, vocab_parent_pos):
    inputs_1 = layers.Input(shape=(maxlen,), name="label_semi")
    inputs_2 = layers.Input(shape=(maxlen,), name="parent_pos_semi")
    embedding_layer = TokenAndPositionEmbedding(maxlen, vocab_label, vocab_parent_pos, embed_dim)
    x = embedding_layer(inputs_1, inputs_2)
    transformer_block = TransformerBlock(embed_dim, num_heads, ff_dim)
    x = transformer_block(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    outputs = layers.Dense(2, activation="softmax")(x)

    model = keras.Model(inputs=[inputs_1, inputs_2], outputs=outputs)
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])

    model.summary()

    return model


def ind_model_structured(embed_dim, num_heads, ff_dim, maxlen, vocab_label, vocab_parent_pos):
    inputs_1 = layers.Input(shape=(maxlen,), name="label_structured")
    inputs_2 = layers.Input(shape=(maxlen,), name="parent_pos_structured")
    embedding_layer = TokenAndPositionEmbedding(maxlen, vocab_label, vocab_parent_pos, embed_dim)
    x = embedding_layer(inputs_1, inputs_2)
    transformer_block = TransformerBlock(embed_dim, num_heads, ff_dim)
    x = transformer_block(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation="relu")(x)
    outputs = layers.Dense(2, activation="softmax")(x)

    model = keras.Model(inputs=[inputs_1, inputs_2], outputs=outputs)
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])

    model.summary()

    return model


def final(noisy_model, semi_model, structured_model,
          parameters_dict_noisy, parameters_dict_semi, parameters_dict_structured,
          max_seq_length):
    ## DEPENDENCY
    base_noisy = noisy_model
    base_noisy.layers.pop()
    base_noisy.trainable = False
    base_noisy.layers[-1].trainable = True
    x_noisy = Dense(256, activation="relu")(base_noisy.layers[-1].output)
    x_noisy = Dropout(0.3)(x_noisy)
    x_noisy = Reshape((8, 32), input_shape=(256,))(x_noisy)
    x_noisy = AttentionWithContext()(x_noisy)
    x_noisy = Reshape((1, 32), input_shape=(32,))(x_noisy)

    base_semi = semi_model
    base_semi.layers.pop()
    base_semi.trainable = False
    base_semi.layers[-1].trainable = True
    x_semi = Dense(256, activation="relu")(base_semi.layers[-1].output)
    x_semi = Dropout(0.3)(x_semi)
    x_semi = Reshape((8, 32), input_shape=(256,))(x_semi)
    x_semi = AttentionWithContext()(x_semi)
    x_semi = Reshape((1, 32), input_shape=(32,))(x_semi)

    base_structured = structured_model
    base_structured.layers.pop()
    base_structured.trainable = False
    base_structured.layers[-1].trainable = True
    x_structured = Dense(256, activation="relu")(base_structured.layers[-1].output)
    x_structured = Dropout(0.3)(x_structured)
    x_structured = Reshape((8, 32), input_shape=(256,))(x_structured)
    x_structured = AttentionWithContext()(x_structured)
    x_structured = Reshape((1, 32), input_shape=(32,))(x_structured)

    concat_dep_out = concatenate([x_noisy, x_semi, x_structured], axis=1)
    x_dep = AttentionWithContext()(concat_dep_out)
    x_dep_re = Reshape((1, 32), input_shape=(32,))(x_dep)
    aux_dep_out = Dense(2, activation="softmax", name='dep_output')(x_dep)
    ## ________________________________________________________________________

    ## PART OF SPEECH
    inp_noisy = Input(shape=(parameters_dict_noisy['maxlen_tag'],), name='inp_noisy')
    emb_noisy = Embedding(parameters_dict_noisy['vocab_size_tag'], 20,
                          weights=[parameters_dict_noisy['embedding_matrix_tag']], trainable=False)(inp_noisy)
    x_tag_noisy = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.2, return_sequences=True))(emb_noisy)
    x_tag_noisy = AttentionWithContext()(x_tag_noisy)
    x_tag_noisy = Reshape((8, 32), input_shape=(256,))(x_tag_noisy)

    inp_semi = Input(shape=(parameters_dict_semi['maxlen_tag'],), name='inp_semi')
    emb_semi = Embedding(parameters_dict_semi['vocab_size_tag'], 20,
                         weights=[parameters_dict_semi['embedding_matrix_tag']], trainable=False)(inp_semi)
    x_tag_semi = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.2, return_sequences=True))(emb_semi)
    x_tag_semi = AttentionWithContext()(x_tag_semi)
    x_tag_semi = Reshape((8, 32), input_shape=(256,))(x_tag_semi)

    inp_structured = Input(shape=(parameters_dict_structured['maxlen_tag'],), name='inp_structured')
    emb_structured = Embedding(parameters_dict_structured['vocab_size_tag'], 20,
                               weights=[parameters_dict_structured['embedding_matrix_tag']], trainable=False)(
        inp_structured)
    x_tag_structured = Bidirectional(LSTM(128, dropout=0.2, recurrent_dropout=0.2, return_sequences=True))(
        emb_structured)
    x_tag_structured = AttentionWithContext()(x_tag_structured)
    x_tag_structured = Reshape((8, 32), input_shape=(256,))(x_tag_structured)

    concat_tag_out = concatenate([x_tag_noisy, x_tag_semi, x_tag_structured], axis=1)
    x_tag = AttentionWithContext()(concat_tag_out)
    x_tag_re = Reshape((1, 32), input_shape=(32,))(x_tag)
    aux_tag_out = Dense(2, activation="softmax", name='tag_output')(x_tag)
    ## ________________________________________________________________________

    ## BERT
    token_inputs = Input((max_seq_length), dtype=tf.int32, name='input_word_ids')
    mask_inputs = Input((max_seq_length,), dtype=tf.int32, name='input_masks')
    bert_inputs = [token_inputs, mask_inputs]

    # --------------------------------------------------------------------------------------------------------------------
    cwd = os.getcwd()
    model_save_path = os.path.join(cwd, "seven_finetuned")
    # --------------------------------------------------------------------------------------------------------------------
    bert_model = TFBertModel.from_pretrained(model_save_path)
    bert_model.trainable = False
    _, pooled_out = bert_model(bert_inputs)
    x_bert = Dropout(0.3)(pooled_out)
    x_bert = Dense(768, activation='relu')(x_bert)
    x_bert = Dense(32, activation='relu')(x_bert)
    x_bert_re = Reshape((1, 32), input_shape=(32,))(x_bert)
    aux_bert_out = Dense(2, activation='softmax', name='bert_output')(x_bert)
    ## ________________________________________________________________________

    ## COMBINE
    final_state = concatenate([x_tag_re, x_dep_re, x_bert_re], axis=1)
    # final_state = Reshape((1, 6), input_shape=(6,))(final_state)

    x = AttentionWithContext()(final_state)
    x = Dense(16, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(8, activation='relu')(x)
    main_out = Dense(2, activation="softmax", name='main_output')(x)

    '''
    ## COMBINE
    syntactic_state = add([x_dep_re, x_tag_re])
    final_state = add([x_bert_re] + syntactic_state)
    
    x = AttentionWithContext()(final_state)
    x = Dense(32, activation='relu')(x)
    x = Dropout(0.3)(x)
    main_out = Dense(2, activation="softmax", name='main_output')(final_state)
    '''
    ## ________________________________________________________________________

    ## COMPILE
    pos_inputs = [inp_noisy, inp_semi, inp_structured]
    transformer_inputs = base_noisy.inputs + base_semi.inputs + base_structured.inputs
    model = Model(inputs=pos_inputs + transformer_inputs + bert_inputs,
                  outputs=[aux_dep_out, aux_tag_out, aux_bert_out, main_out])
    model.compile(optimizer='adam',
                  loss={'dep_output': 'sparse_categorical_crossentropy',
                        'tag_output': 'sparse_categorical_crossentropy',
                        'bert_output': 'sparse_categorical_crossentropy',
                        'main_output': 'sparse_categorical_crossentropy'},
                  loss_weights={'main_output': 1., 'dep_output': 0.10, 'tag_output': 0.10, 'bert_output': 0.10})
    model.summary()

    plot_model(model, show_shapes=True, show_layer_names=True, to_file='model.png')
    Image(retina=True, filename='model.png')

    return model
