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

### Install PyTorch and dependencies

For Installation of PyTorch see [official website](https://pytorch.org/).

Or install torch using the command below: `will use CPU only`:

```console
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

You also need `nltk`:

```console
pip install nltk
```

If you get an error during the first run, you also need to install `nltk.tokenize.punkt`:
Run this once in your terminal:

```console
$ python
>>> import nltk
>>> nltk.download('punkt')
```

Or have other errors such as `punkt_tab`:

```console
python -c "import nltk; nltk.download('punkt_tab')"
```

Run this to use fastAPI endpoint

```console
pip install fastapi uvicorn
```

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

Run

```console
python run.py
```

This will dump `training_data.pth` file and setup the database.

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
