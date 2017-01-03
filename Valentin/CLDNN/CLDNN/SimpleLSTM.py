import tensorflow as tf
from tqdm import tqdm
import functools
from SpeechDataUtils import SpeechDataUtils

def define_scope(function):
  attribute = '_cache_' + function.__name__

  @property
  @functools.wraps(function)
  def decorator(self):
    if not hasattr(self, attribute):
      with tf.variable_scope(function.__name__):
        setattr(self, attribute, function(self))
    return getattr(self, attribute)

  return decorator

class SimpleLSTMOptions(object):
  def __init__(self,
               learning_rate = 1e-4,
               lstm_hidden_units = 512,
               time_major = False):

    self.learning_rate = learning_rate
    self.lstm_hidden_units = lstm_hidden_units
    self.time_major = time_major

  default_options = None
SimpleLSTMOptions.default_options = SimpleLSTMOptions()

class SimpleLSTM(object):
  def __init__(self,
                input_placeholder, lengths_placeholder, output_placeholder,
                options = SimpleLSTMOptions.default_options
                ):
    self.input_placeholder = input_placeholder
    self.lengths_placeholder = lengths_placeholder
    self.output_placeholder = output_placeholder

    self.output_size = int(self.output_placeholder.get_shape()[1])

    self.options = options

  @define_scope
  def inference(self):
    with tf.name_scope("LSTM"):
      cell = tf.nn.rnn_cell.LSTMCell(self.options.lstm_hidden_units)
      outputs, state = tf.nn.dynamic_rnn(cell, self.input_placeholder, self.lengths_placeholder, dtype = tf.float32, time_major = self.options.time_major)

      output_shape = outputs.get_shape()
      output_shape = [-1, int(output_shape[1] * output_shape[2])]
      outputs = tf.reshape(outputs, output_shape)

      weights = tf.Variable(tf.truncated_normal([output_shape[1], self.output_size], stddev = 0.1))
      biaises = tf.Variable(tf.constant(0.1, shape=[self.output_size]))

      logits = tf.matmul(outputs, weights) + biaises
    
    return logits

  @define_scope
  def loss(self):
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(self.inference, self.output_placeholder)
    return tf.reduce_mean(cross_entropy)

  @define_scope
  def train(self):
    tf.summary.scalar('loss', self.loss)
    optimizer = tf.train.AdamOptimizer(self.options.learning_rate)

    # Create a variable to track the global step.
    global_step = tf.Variable(0, name='global_step', trainable=False)
    train_op = optimizer.minimize(self.loss, global_step=global_step)
    #train_op = optimizer.minimize(self.loss)
    return train_op

  @define_scope
  def evaluate(self):
    correct_inference = tf.equal(tf.argmax(self.inference, 1), tf.argmax(self.output_placeholder, 1))
    return tf.reduce_mean(tf.cast(correct_inference, tf.float32))


def main():
  #hyperparams
  BATCH_SIZE = 64
  MAX_INPUT_SEQUENCE_LENGTH = 100
  MAX_OUTPUT_SEQUENCE_LENGTH = 10
  FEATURES_COUNT = 40
  TRAINING_ITERATION_COUNT = 1000

  #get batch
  data = SpeechDataUtils(librispeech_path = 'D:\\tmp\\LibriSpeech')
  data.preload_batch(BATCH_SIZE)

  dictionnary_size = data.dictionnary_size

  with tf.Graph().as_default():
    #Placeholders
    input_placeholder = tf.placeholder(tf.float32, [None, MAX_INPUT_SEQUENCE_LENGTH, FEATURES_COUNT], name="Input__placeholder")
    lengths_placeholder = tf.placeholder(tf.int32, [None], name="Lengths_placeholder")
    output_placeholder = tf.placeholder(tf.int32, [None, MAX_OUTPUT_SEQUENCE_LENGTH], name="True_output_placeholder")

    #Model
    options = SimpleLSTMOptions(lstm_hidden_units = 256)
    model = SimpleLSTM(input_placeholder,lengths_placeholder, output_placeholder, options)

    train_op = model.train
    loss_op = model.loss
    
    summary = tf.summary.merge_all()
    
    init = tf.global_variables_initializer()

    saver = tf.train.Saver()
    
    session_config = tf.ConfigProto()
    session_config.gpu_options.allow_growth = True

    with tf.Session(config=session_config) as session:
      summary_writer = tf.summary.FileWriter('/tmp/custom/SimpleLSTM/logs/', session.graph)

      print("Initializing variables...")
      session.run(init)
      print("Variables initialized !")

      for i in tqdm(range(TRAINING_ITERATION_COUNT)):
        batch_inputs, batch_lengths, batch_outputs = data.get_preloaded_batch(BATCH_SIZE)
        data.preload_batch(BATCH_SIZE)

        feed_dict = {
          input_placeholder : batch_inputs,
          lengths_placeholder : batch_lengths,
          output_placeholder : batch_outputs
          }

        _, loss_value = session.run([train_op, loss_op], feed_dict = feed_dict)

        if i%100 == 0:
          summary_str = session.run(summary, feed_dict = feed_dict)
          summary_writer.add_summary(summary_str, i)
          summary_writer.flush()

        if i%1000 == 0 or (i + 1) == TRAINING_ITERATION_COUNT:
          checkpoint_file = '/tmp/custom/SimpleLSTM/logs/model.ckpt'
          saver.save(session, checkpoint_file, global_step = i)

         
if __name__ == '__main__':
  main()