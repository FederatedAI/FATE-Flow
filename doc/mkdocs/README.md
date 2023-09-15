# Build

## use docker

At repo root, execute

```sh
docker run --rm -it -p 8000:8000 -v ${PWD}:/docs sagewei0/mkdocs  
```

to serve docs in http://localhost:8000

or

```sh
docker run --rm -it -p 8000:8000 -v ${PWD}:/docs sagewei0/mkdocs build
```

to build docs to `site` folder.

## manually

[`mkdocs-material`](https://pypi.org/project/mkdocs-material/) and servel plugins are needed to build this docs

Fisrt, create an python virtual environment

```sh
python3 -m venv "fatedocs"
source fatedocs/bin/activate
pip install -U pip
```
And then install requirements

```sh
pip install -r doc/mkdocs/requirements.txt
```

Now, use

```sh
mkdocs serve
```

at repo root to serve docs or

use 

```sh
mkdocs build
```

at repo root to build docs to folder `site`


# Develop guide

We use [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) to build our docs. 
Servel markdown extensions are really useful to write pretty documents such as 
[admonitions](https://squidfunk.github.io/mkdocs-material/reference/admonitions/) and 
[content-tabs](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/).

Servel plugins are introdused to makes mkdocs-material much powerful:


- [mkdocstrings](https://mkdocstrings.github.io/usage/) 
    automatic documentation from sources code. We mostly use this to automatic generate
    `params api` for `federatedml`.

- [awesome-pages](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin)
    for powerful nav rule

- [i18n](https://ultrabug.github.io/mkdocs-static-i18n/)
    for multi-languege support

- [mkdocs-jupyter](https://github.com/danielfrg/mkdocs-jupyter)
    for jupyter format support

- [mkdocs-simple-hooks](https://github.com/aklajnert/mkdocs-simple-hooks)
    for simple plugin-in