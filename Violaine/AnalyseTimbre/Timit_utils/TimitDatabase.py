import os
import numpy as np

from TimitSample import TimitSample
from TimitDataset import TimitDataset

class TimitDatabase(object):
    def __init__(self, timit_database_path : str, mfcc_features_count = 40):
      self.timit_database_path = timit_database_path
      self.mfcc_features_count = mfcc_features_count
      self.datasets_names = ("train", "test")

      # Datasets
      self.train_dataset = TimitDataset(timit_database_path, "train", mfcc_features_count)
      #self.test_dataset = TimitDataset(os.path.join(timit_database_path, "TEST"), "test", mfcc_features_count)
      self.datasets = [self.train_dataset]
      self.load_samples_lists()

      # Dictionnaires
      self.words_dictionary_path = os.path.join(self.timit_database_path, "words_dictionary.txt")
      self.phonemes_dictionary_path = os.path.join(self.timit_database_path, "phonemes_dictionary.txt")
      #self.load_words_dictionary()
      #self.load_phonemes_dictionary()

      #for i in range(len(self.datasets)):
      #  dataset = self.datasets[i]
      #  dataset.phonemes_dictionary_size = self.phonemes_dictionary_size
      #  dataset.words_dictionary_size = self.words_dictionary_size

    def load_samples_lists(self) -> dict:
      for dataset in self.datasets:
        dataset.load_samples_list()

    def build_samples_mfcc_features(self):
      for dataset in self.datasets:
        dataset.build_samples_mfcc_features()
        
    def build_dictionaries(self): # word and phonemes
      words = []
      phonemes = []
      for dataset in self.datasets:
        dataset_samples = dataset.load_samples(load_phonemes = True, load_words = True)
        for sample in dataset_samples:
          sample_words = sample.words
          sample_phonemes = sample.phonemes
          for _, _, word in sample_words:
            if not word in words:
              words.append(word)
          for _, _, phoneme in sample_phonemes:
            if not phoneme in phonemes:
              phonemes.append(phoneme)
      
      words_dict_string = ""
      phonemes_dict_string = ""
      for word in words:
        words_dict_string += word + '\n'
      words_dict_string += "<EOS>"
      for phoneme in phonemes:
        phonemes_dict_string += phoneme + '\n'
      phonemes_dict_string += "<EOS>"
      
      with open(self.words_dictionary_path, 'w') as words_dict_file:
        words_dict_file.write(words_dict_string)

      with open(self.phonemes_dictionary_path, 'w') as phonemes_dict_file:
        phonemes_dict_file.write(phonemes_dict_string)

    def load_words_dictionary(self):
      with open(self.words_dictionary_path, 'r') as words_dict_file:
        words = words_dict_file.readlines()
      self.word_to_id_dictionary = dict()
      self.id_to_word_dictionary = dict()
      for i in range(len(words)):
        word = words[i]
        if word.endswith('\n'):
          word = word[:-1]
        self.word_to_id_dictionary[word] = i
        self.id_to_word_dictionary[i] = word
      self.words_dictionary_size = len(self.word_to_id_dictionary)

    def load_phonemes_dictionary(self):
      with open(self.phonemes_dictionary_path, 'r') as phonemes_dict_file:
        phonemes = phonemes_dict_file.readlines()
      self.phoneme_to_id_dictionary = dict()
      self.id_to_phoneme_dictionary = dict()
      for i in range(len(phonemes)):
        phoneme = phonemes[i]
        if phoneme.endswith('\n'):
          phoneme = phoneme[:-1]
        self.phoneme_to_id_dictionary[phoneme] = i
        self.id_to_phoneme_dictionary[i] = phoneme
      self.phonemes_dictionary_size = len(self.phoneme_to_id_dictionary)

    def load_mfcc_lengths(self, by_word = False):
      self.max_mfcc_length = 0
      self.max_mfcc_length_by_word = 0

    def build_batches(self):
      #self.build_mfcc_lengths_batches()
      #self.build_mfcc_lengths_batches_byword()
      #self.build_mfcc_batches()
      #self.build_mfcc_batches_byword()
      self.build_phonemes_lengths_batches()
      self.build_phonemes_ids_batches()

    def build_mfcc_lengths_batches(self):
      for dataset in self.datasets:
        dataset.build_mfcc_lengths_batch()

    def build_mfcc_lengths_batches_byword(self):
      for dataset in self.datasets:
        dataset.build_mfcc_lengths_batch_byword()

    def build_mfcc_batches(self):
      # Getting max length across all datasets (for padding)
      max_mfcc_features_length = self.get_max_mfcc_features_length()
      for dataset in self.datasets:
        dataset.build_mfcc_batch(max_mfcc_features_length)

    def build_mfcc_batches_byword(self):
      # Getting max length across all datasets (for padding)
      max_mfcc_features_length_byword = self.get_max_mfcc_features_length_byword()
      for dataset in self.datasets:
        dataset.build_mfcc_batch_byword(max_mfcc_features_length_byword)

    def build_phonemes_ids_batches(self):
      # Getting max length across all datasets (for padding)
      max_phonemes_length = self.get_max_phonemes_length()
      for dataset in self.datasets:
        dataset.build_phonemes_ids_batch(self.phoneme_to_id_dictionary, max_phonemes_length)

    def build_phonemes_lengths_batches(self):
      for dataset in self.datasets:
        dataset.build_phonemes_lengths_batch()

    def get_max_mfcc_features_length(self):
      max_mfcc_features_length = 0
      for dataset in self.datasets:
        dataset.load_mfcc_lengths()
        max_mfcc_features_length = max(np.max(dataset.mfcc_features_lengths), max_mfcc_features_length)
      return max_mfcc_features_length
    
    def get_max_mfcc_features_length_byword(self):
      max_mfcc_features_length_byword = 0
      for dataset in self.datasets:
        dataset.load_mfcc_lengths_byword()
        max_mfcc_features_length = max(np.max(dataset.mfcc_features_lengths_byword), max_mfcc_features_length_byword)
      return max_mfcc_features_length_byword

    def get_max_phonemes_length(self):
      max_phonemes_length = 0
      for dataset in self.datasets:
        dataset.load_phonemes_lengths()
        max_phonemes_length = max(max_phonemes_length, np.max(dataset.phonemes_lengths))
      return max_phonemes_length

def main():
    timit_database_path = r"C:\Users\Violaine Fayolle\Documents\M2\Projet Senior\DataBase\TimbreAnalysis\BerlinEMO"
    data = TimitDatabase(timit_database_path)
    data.build_samples_mfcc_features()
    #data.load_samples_lists()

main()
#
##data.build_samples_mfcc_features(by_word = False)
##(by_word = True)
##data.build_dictionaries()
##samples = data.samples_list["train"][:1]
##for sample_name in samples:
##  sample_info = TimitSample(sample_name, data.datasets_paths["train"])
##  sample_info.load(load_phonemes = False, load_sentence = False, load_words = True, load_mfcc = False)
#data.build_batches()
##data.datasets[0].build_mfcc_lengths_batch()
#_, mfcc_features_lengths_batch, _, phonemes_lengths_batch = data.datasets[0].next_batch(1)
#print(mfcc_features_lengths_batch, phonemes_lengths_batch)