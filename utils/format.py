import os
import json
import torch
import numpy
import re

import utils

def get_vocab_path(model_name):
    return os.path.join(utils.storage_dir(), "models", model_name, "vocab.json")

class Vocabulary:
    def __init__(self, model_name):
        self.path = get_vocab_path(model_name)
        utils.create_folders_if_necessary(self.path)
        self.max_size = 100
        self.vocab = json.load(open(self.path)) if os.path.exists(self.path) else {}

    def __getitem__(self, token):
        if not(token in self.vocab.keys()):
            if len(self.vocab) >= self.max_size:
                raise ValueError("Maximum vocabulary capacity reached")
            self.vocab[token] = len(self.vocab) + 1
            self.save()
        
        return self.vocab[token]

    def save(self):
        json.dump(self.vocab, open(self.path, "w"))

class ObssPreprocessor:
    def __init__(self, model_name, obs_space):
        self.vocab = Vocabulary(model_name)
        self.obs_space = {
            "image": 147,
            "instr": self.vocab.max_size
        }

    def __call__(self, obss, use_gpu=False):
        obs = {}

        if "image" in self.obs_space.keys():
            images = numpy.array([obs["image"] for obs in obss])
            images = images.reshape(images.shape[0], -1)

            images = torch.tensor(images).float()
            if use_gpu:
                images = images.cuda()

            obs["image"] = images

        if "instr" in self.obs_space.keys():
            instrs = []
            max_instr_len = 0
            
            for obs in obss:
                tokens = re.findall("([a-z]+)", obs["mission"].lower())
                instr = [self.vocab[token] for token in tokens]
                instrs.append(instr)
                max_instr_len = max(len(instr), max_instr_len)
            
            np_instrs = numpy.zeros((max_instr_len, len(obss), self.vocab.max_size))

            for i, instr in enumerate(instrs):
                hot_instr = numpy.zeros((len(instr), self.vocab.max_size))
                hot_instr[numpy.arange(len(instr)), instr] = 1
                np_instrs[:len(instr), i, :] = hot_instr
            
            instrs = torch.tensor(np_instrs).float()
            if use_gpu:
                instrs = instrs.cuda()
            
            obs["instr"] = instrs

        return obs