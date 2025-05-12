#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Apr 9, 2024
# About: Implementation of Machine 
# License: MIT License

#   Permission is hereby granted, free of charge, to any person obtaining
#   a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject
#   to the following conditions:

#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
#   ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
#   TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
#   SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#   AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#   OR OTHER DEALINGS IN THE SOFTWARE.


import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd

class AutoEncoder(nn.Module):
    def __init__(self):
        """
        Implement AutoEncoder in PyTorch


        """
        super(AutoEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(1, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

class AutoEncoderTrainerTS:
    def __init__(self, model = AutoEncoder, lr = 0.001, **kwargs):
        """
        Trainer class to train an AutoEncoder module to fit a timeseries dataset for the purpose of denoising it.

        Parameters
        ----------------
        model: `nn.Module`
            Model to train

        lr: `float`
            Learning rate
            

        """

        # Check if CUDA is available and if not, use CPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(self.device)
        self.model = model.to(self.device)
        self.lr = lr
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()

    def train(self, time, message, epochs=1000, verbose=True):
        """
        Training for Neural Network
        """

        time = torch.tensor(time, dtype=torch.float32).to(self.device)
        message = torch.tensor(message, dtype=torch.float32).to(self.device)

        # reshape to have len() samples of 1 features
        time = torch.tensor(time, dtype=torch.float32).view(-1, 1)
        message = torch.tensor(message, dtype=torch.float32).view(-1, 1)

        self.model.train() # set the model to training mode

        for epoch in range(epochs):
            # Forward pass
            outputs = self.model(time)
            loss = self.criterion(outputs, message)
            # Backward and optimize
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            if ((epoch+1) % 100 == 0) & verbose:
                print ('Epoch [{}/{}], Loss: {:.4f}'.format(epoch+1, epochs, loss.item()))

    def predict(self, new_time, unscaled_time, msg_min, msg_max, dense_time_points = False):
        """
        Make prediction on new time points

        Parameters
        -----------------------

        new_time: `np.array`, `pd.DataFrame`
        """

        self.model.eval()

        if dense_time_points:
            new_time = np.linspace(new_time[0],new_time[-1], len(new_time)*50)

        new_time = torch.tensor(new_time, dtype=torch.float32).to(self.device).view(-1, 1)

        # Make predictions
        with torch.no_grad():
            predictions_scaled = self.model(new_time)

        predictions_scaled_np = predictions_scaled.cpu().detach().numpy()
        predictions = predictions_scaled_np*(msg_max - msg_min) + msg_min

        new_time = new_time.cpu().detach().numpy()
        newtimepoints = new_time*(unscaled_time[-1] - unscaled_time[0]) + unscaled_time[0]
        

        return newtimepoints.flatten(), predictions.flatten()