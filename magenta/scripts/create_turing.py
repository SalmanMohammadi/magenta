# -*- coding: utf-8 -*-

import tensorflow as tf
import pandas as pd
from shutil import copyfile
import magenta as mg
import numpy as np
import os
import csv
import random

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_string('input_dir', None,
        'Root directory for midi files.')
tf.app.flags.DEFINE_string('output_dir', None,
        'Output directory')
tf.app.flags.DEFINE_string('cond_dir', None,
        'CondRNN output directory')
tf.app.flags.DEFINE_string('base_dir', None,
        'Base output directory')
tf.app.flags.DEFINE_string('csv', None,
        'CSV metadata file.')
tf.app.flags.DEFINE_integer('length', 30,
        'Length of each sample')
tf.app.flags.DEFINE_integer('participants', 6,
        'Num experiments')
tf.app.flags.DEFINE_integer('tests', 4,
        'Number of comparisons to make')

def main(unused_argv):
    tf.logging.set_verbosity(tf.logging.INFO)
    if None in [FLAGS.input_dir, FLAGS.output_dir, FLAGS.csv, FLAGS.base_dir, FLAGS.cond_dir]:
        tf.logging.fatal('--input_dir --output_dir --csv --files --base_dir --cond_dir required.')
        return

    composers = ['Frédéric Chopin',
        'Johann Sebastian Bach', 
        'Claude Debussy', 
        'Ludwig van Beethoven'
        ]
    
    os.mkdir(FLAGS.base_dir)
    os.mkdir(FLAGS.cond_dir)

    split = ['test', 'validation']
    output_dir = os.path.expanduser(FLAGS.output_dir)
    input_dir = os.path.expanduser(FLAGS.input_dir)

    df_csv = os.path.expanduser(FLAGS.csv)
    df = pd.read_csv(df_csv)
    df = df[df.split.isin(split)]

    start_times = [x for x in range(5, 600, 50)]
    df = df[df.canonical_composer.isin(composers)] 
    filenames = df.midi_filename.values
    
    output_dict = {'A': FLAGS.output_dir, 'X': FLAGS.cond_dir, 'Y': FLAGS.base_dir}
    orderings = np.tile(['AXY', 'AYX', 'YAX', 'YXA', 'XYA', 'XAY'], int(FLAGS.participants / 6))
    orderings = np.tile(orderings, (FLAGS.tests, 1))
    for x in orderings:
      random.shuffle(x)
    print(orderings)

    with open(os.path.join(output_dir, "orderings.csv"),"w+") as f:
      csvWriter = csv.writer(f,delimiter=',')
      csvWriter.writerows(orderings)

    output_filename = "participant"
    for i in range(FLAGS.participants):
      num_performances = FLAGS.tests
      cur_filenames = np.random.choice(filenames, size=num_performances)
      for j, fname in enumerate(cur_filenames):
        cname = "{}_{}_test_{}".format(output_filename, i, j)
        start_time = random.choice(start_times)
        sequence = mg.music.midi_file_to_sequence_proto(input_dir+fname)

        while not start_time + 5 + (FLAGS.length*2) < sequence.total_time:
          start_time = random.choice(start_times)

        sequence = mg.music.extract_subsequence(sequence, start_time, start_time+(FLAGS.length*2))
        subseqs = mg.music.split_note_sequence(sequence, FLAGS.length)

        primer, output = subseqs[0], subseqs[1]
        file_dict = {'A': output, 'X': primer, 'Y': primer}
        for x, order in enumerate(orderings[j, i]):
          cur_dir = output_dict[order]
          midi_filename = "{}_{}.midi".format(cname, order)
          print("{}/{}".format(cur_dir, midi_filename))
          sequence = file_dict[order]
          mg.music.sequence_proto_to_midi_file(sequence, cur_dir+'/'+midi_filename)


    # files_per_composer = int(num_files/len(composers))
    # filenames = []
    # composers_out = []
    # for composer in composers:
    #     curnames = list(df[df.canonical_composer.str.contains(composer)].sort_values('year')[-files_per_composer:].midi_filename.values)
    #     tf.logging.info(composer + ": " + str(len(curnames)))
    #     filenames += curnames
    #     composers_out += [composer for x in range(len(curnames))] 

    # file_slice = FLAGS.file_slice
    # total_files = len(composers_out)
    # if file_slice:
    #     total_files *= file_slice

    # tf.logging.info("Total files: " + str(total_files))

    # for filename, composer in zip(filenames, composers_out):
    #     output_filename = os.path.basename(filename)
    #     cur_dir = output_dir
    #     if FLAGS.eval or FLAGS.test:
    #         composer_dir = composers_paths[composer] + '/'
    #         if not os.path.exists(os.path.join(cur_dir, composer_dir)):
    #             os.mkdir(os.path.join(cur_dir, composer_dir))
    #         cur_dir = os.path.join(cur_dir, composer_dir)
    #         tf.logging.info('Copying ' + output_filename + " composer: " + composer)
    #     else:
    #         tf.logging.info('Copying ' + output_filename)

    #     sequence = mg.music.midi_file_to_sequence_proto(input_dir+filename)
    #     # copyfile(input_dir+filename, output_dir + '/' + output_filename)
    #     if file_slice:
    #         subseqs = mg.music.split_note_sequence(sequence, FLAGS.length)
    #         for i in range(file_slice):
    #             subseq = random.choice(subseqs)
    #             tf.logging.info("Copied slice " + str(i) + '_' + output_filename)
    #             mg.music.sequence_proto_to_midi_file(subseq, cur_dir +'/'+ str(i) + '_' + output_filename)
    #     else:
    #         sequence = mg.music.extract_subsequence(sequence, 0, FLAGS.length)
    #         mg.music.sequence_proto_to_midi_file(sequence, cur_dir+'/'+output_filename)


def console_entry_point():
    tf.app.run(main)

if __name__ == '__main__':
    console_entry_point()
