import torch
import torch.nn as nn


class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        # no activation and no softmax at the end
        return out


class NeuralNetSM(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, dropout_rate=0.5):
        super(NeuralNetSM, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size).to(torch.float32)
        self.l2 = nn.Linear(hidden_size, hidden_size).to(torch.float32)
        self.l3 = nn.Linear(hidden_size, output_size).to(torch.float32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(p=dropout_rate)  # Dropout Layer
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = x.to(torch.float32)  # Ensure input is float32
        out = self.l1(x)
        out = self.relu(out)
        out = self.dropout(out)  # Apply dropout after activation

        out = self.l2(out)
        out = self.relu(out)
        out = self.dropout(out)  # Apply dropout again

        out = self.l3(out)  # Output layer (no dropout here)
        return self.softmax(out)
