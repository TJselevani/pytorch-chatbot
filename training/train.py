"""
Script to train the PyTorch intent classification model.
"""

import numpy as np
import json
from app.chatbot import NeuralNet
import logging
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from utils.nltk_utils import bag_of_words, tokenize, stem


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatDataset(Dataset):
    """Custom dataset for chat training."""

    def __init__(self, X_train, y_train):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples


def train_model(
    intents_path="data/intents.json", output_path="models/intent_model.pth"
):
    """Train the intent classification model."""

    # Load intents
    with open(intents_path, "r") as f:
        intents = json.load(f)

    all_words = []
    tags = []
    xy = []

    # Process each intent
    for intent in intents["intents"]:
        tag = intent["tag"]
        tags.append(tag)

        for pattern in intent["patterns"]:
            # Tokenize each word
            w = tokenize(pattern)
            all_words.extend(w)
            xy.append((w, tag))

    # Stem and lowercase each word
    ignore_words = ["?", ".", "!", ","]
    all_words = [stem(w) for w in all_words if w not in ignore_words]
    all_words = sorted(set(all_words))
    tags = sorted(set(tags))

    logger.info(f"{len(xy)} patterns")
    logger.info(f"{len(tags)} tags: {tags}")
    logger.info(f"{len(all_words)} unique stemmed words: {all_words}")

    # Create training data
    X_train = []
    y_train = []

    for pattern_sentence, tag in xy:
        bag = bag_of_words(pattern_sentence, all_words)
        X_train.append(bag)

        label = tags.index(tag)
        y_train.append(label)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    # Hyperparameters
    num_epochs = 1000
    batch_size = 8
    learning_rate = 0.001
    input_size = len(X_train[0])
    hidden_size = 8
    output_size = len(tags)

    logger.info(f"Training with {num_epochs} epochs, batch size {batch_size}")

    # Dataset and DataLoader
    dataset = ChatDataset(X_train, y_train)
    train_loader = DataLoader(
        dataset=dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Model, loss, optimizer
    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    for epoch in range(num_epochs):
        for words, labels in train_loader:
            words = words.to(device)
            labels = labels.to(dtype=torch.long).to(device)

            # Forward pass
            outputs = model(words)
            loss = criterion(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if (epoch + 1) % 100 == 0:
            logger.info(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}")

    logger.info(f"Final loss: {loss.item():.4f}")

    # Save model
    data = {
        "model_state": model.state_dict(),
        "input_size": input_size,
        "hidden_size": hidden_size,
        "output_size": output_size,
        "all_words": all_words,
        "tags": tags,
    }

    torch.save(data, output_path)
    logger.info(f"Training complete. Model saved to {output_path}")


if __name__ == "__main__":
    train_model()
