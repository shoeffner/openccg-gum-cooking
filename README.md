# OpenCCG GUM cooking

This repository contains the english-cooking grammar for [OpenCCG](https://github.com/OpenCCG/openccg), as well as the related ontologies.
It is based on [GUM 3 space](https://www.ontospace.uni-bremen.de/ontology/gum.html) and the [english-diaspace](http://www.diaspace.uni-bremen.de/cgi-bin/twiki/view/DiaSpace/ReSources.html) grammar, but contains a cooking specific domain and is extended by many rules to parse sentences from the cooking domain.


## Usage

If you are just looking to integrate the grammar or the owl files into your application, just download them and put them where you need them to be.
No further setup required.

If you are developing the grammars and changing the ontologies, you can use the owl2types tool to update the [types.xml](english-cooking/types.xml).

### Install

To install owl2types, we recommend using pip (best inside a virtual environment, e.g. using pipenv):

    pip install git+https://github.com/shoeffner/openccg-gum-cooking

On Windows, we had troubles getting owlready2 directly from the setup.py, this you can use the following command to install it:

    pip install -r requirements.txt


### Converting owls

To convert our ontologies to the types.xml, either run `make`, if you have make available (on UNIXes), or run:

    owl2types --output english-cooking/types.xml \
              --exclude-owl-thing \
              --lookup ./ontologies \
              ./ontologies/SLM-cooking.owl:slm

On Windows, the command should look like this:

    owl2types --output english-cooking\types.xml --exclude-owl-thing --lookup ontologies ontologies\SLM-cooking.owl:slm


### Testing owl2types

To test the owl2types tool, run `make tests` or `python -m unittest discover tools/tests`.


## References

> **Lamy JB.** [Owlready: Ontology-oriented programming in Python with automatic classification and high level constructs for biomedical ontologies](http://www.lesfleursdunormal.fr/_downloads/article_owlready_aim_2017.pdf). **Artificial Intelligence In Medicine 2017**;80:11-28
