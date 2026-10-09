# Implementation of a Contextual Chatbot in PyTorch

Simple chatbot implementation with PyTorch.

- The implementation should be easy to follow for beginners and provide a basic understanding of chatbots.
- The implementation is straightforward with a Feed Forward Neural net with 2 hidden layers.
- Customization for your own use case is super easy. Just modify `intents.json` with possible patterns and responses and re-run the training (see below for more info).

The approach is inspired by this article and ported to PyTorch: [https://chatbotsmagazine.com/contextual-chat-bots-with-tensorflow-4391749d0077](https://chatbotsmagazine.com/contextual-chat-bots-with-tensorflow-4391749d0077).

## Installation

### Create an environment

Whatever you prefer (e.g. `conda` or `venv`)

```console
mkdir myproject
$ cd myproject
$ python3 -m venv venv
```

### Activate it

Mac / Linux:

```console
. venv/bin/activate
```

Windows:

```console
venv\Scripts\activate
```

### Install PyTorch (CPU build) and dependencies

Install only what the chatbot uses. The CPU build of PyTorch avoids downloading several gigabytes of CUDA packages:

```console
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

`torchvision` and `torchaudio` are not needed. NLTK is only needed for tokenising in `nltk_utils.py`; see the
note below if you want to drop it.


## Usage

Configure SQL database connection details in the config.py file

```console
DB_CONFIG  = {
    "host"="",     # Change if using a remote MySQL server
    "user"="",     # Your MySQL username
    "password"="", # Your MySQL password
    "database"=""  # The MySQL database you created
}
```

Run this first

```console
python run.py
```

This will dump `training_data.pth` file and setup the database.

to use the chatbot on terminal

```console
python chat.py
```

## Customize

Have a look at [intents.json](intents.json). You can customize it according to your own use case. Just define a new `tag`, possible `patterns`, and possible `responses` for the chat bot. You have to re-run the training whenever this file is modified.

```console
{
  "intents": [
    {
      "tag": "greeting",
      "patterns": [
        "Hi",
        "Hey",
        "How are you",
        "Is anyone there?",
        "Hello",
        "Good day"
      ],
      "responses": [
        "Hey :-)",
        "Hello, thanks for visiting",
        "Hi there, what can I do for you?",
        "Hi there, how can I help?"
      ]
    },
    ...
  ]
}
```

## Watch the Tutorial

[![Alt text](https://img.youtube.com/vi/RpWeNzfSUHw/hqdefault.jpg)](https://www.youtube.com/watch?v=RpWeNzfSUHw&list=PLqnslRFeH2UrFW4AUgn-eY37qOAWQpJyg)

