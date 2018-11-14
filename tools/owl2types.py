import argparse
import re
import sys

import xml.etree.ElementTree as ET
from xml.dom import minidom

from pathlib import Path
from urllib.parse import unquote


import owlready2


def owl2types():
    unique_prefix.prefixes = []
    arguments = parse_args()

    ontologies, ontology_prefix_map = load_ontologies(arguments.ontologies)
    classes = extract_classes(ontologies, ontology_prefix_map)
    if arguments.exclude_owl_thing:
        classes = exclude_owl_thing(classes)
    xml = classes2xml(classes, ontologies)

    print(xml, file=arguments.output)


class OntologyArgument:
    def __init__(self, filename, prefix=None):
        """Stores the URL (i.e. the "local" IRI) and the prefix for the
        ontologies. If the filename starts with http, it is assumed to be a
        url."""
        if filename.startswith('http'):
            self.uri = unquote(filename)
        else:
            self.uri = Path(filename).absolute().as_uri()

        if prefix is not None:
            self.prefix = unique_prefix(prefix)
        else:
            self.prefix = generate_prefix(self.uri)

    def __str__(self):
        return f'Ontology: {self.prefix} -- {self.uri}'

    @staticmethod
    def argument(argument):
        if argument.startswith('http') and argument.count(':') == 1:
            return OntologyArgument(argument)
        return OntologyArgument(*argument.rsplit(':', 1))


def load_ontologies(ontology_arguments):
    ontology_prefix_map = {'owl': 'owl'}
    ontologies = []
    for ontology in ontology_arguments:
        onto = owlready2.get_ontology(ontology.uri).load(reload=True)
        ontologies.append(onto)
        ontology_prefix_map[onto.ontology.name] = ontology.prefix

    for ontology in ontologies:
        for imported_ontology in ontology.indirectly_imported_ontologies():
            onto_name = imported_ontology.ontology.name
            if onto_name not in ontology_prefix_map:
                ontologies.append(imported_ontology)
                ontology_prefix_map[onto_name] = generate_prefix(onto_name)
    return ontologies, ontology_prefix_map


def classname(cls, ontology_prefix_map):
    return f'{ontology_prefix_map[cls.namespace.ontology.name]}-{cls.name}'


def extract_classes(ontologies, ontology_prefix_map):
    classes = {}
    parent_classes = (owlready2.entity.ThingClass, )
    for onto in ontologies:
        for cls in onto.classes():
            parents = set(classname(parent, ontology_prefix_map)
                          for parent in cls.is_a
                          if isinstance(parent, parent_classes))
            key = classname(cls, ontology_prefix_map)
            if key not in classes:
                classes[key] = parents
            else:
                classes[key].union(parents)
    return classes


def exclude_owl_thing(classes):
    thing = 'owl-Thing'
    try:
        del classes[thing]
    except KeyError:
        pass
    for cls, parents in classes.items():
        classes[cls] -= set([thing])
    return classes



def classes2xml(classes, ontologies):
    # Create XML
    root = ET.Element('types', name='core')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:noNamespaceSchemaLocation', 'https://raw.githubusercontent.com/OpenCCG/openccg/master/grammars/types.xsd')
    for cls, parents in classes.items():
        elem = ET.SubElement(root, 'type', name=cls)
        if len(parents):
            elem.set('parents', ' '.join(parents))

    # Prettify text output
    pretty = minidom.parseString(ET.tostring(root)).toprettyxml(indent=' ' * 4, encoding='UTF-8').decode('utf-8')
    pretty = pretty.replace('"/>', '" />')
    comment = '<!-- This file was generated automatically. Do not modify it manually. -->'
    comment_ontologies = '<!-- Ontologies used:\n    ' + '\n    '.join(o.base_iri for o in ontologies) + '\n-->'
    lines = pretty.splitlines()
    lines.insert(1, comment_ontologies)
    lines.insert(1, comment)
    return '\n'.join(lines)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', nargs='?',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='The output file, defaults to STDOUT')
    parser.add_argument('ontologies', nargs='+',
                        type=OntologyArgument.argument,
                        help='The list of ontologies and their mappings. '
                             'Should follow the format path/to/ontology:prefix, '
                             'e.g. ./ontologies/GUM-3.owl:gum . If no prefix is '
                             'specified, the program tries to invent one.')
    parser.add_argument('-l', '--lookup', nargs=1,
                        type=extend_lookup_path,
                        help='Additional lookup directory for ontology '
                             'files. Can be specified multiple times.')
    parser.add_argument('-x', '--exclude-owl-thing', action='store_true',
                        help='Exclude owl:Thing as the top level element. '
                             'By default, it will be included.')
    return parser.parse_args()


def unique_prefix(prefix):
    candidate = prefix
    counter = 0
    while candidate in unique_prefix.prefixes:
        candidate = prefix + str(counter)
        counter += 1
    unique_prefix.prefixes.append(candidate)
    return candidate
unique_prefix.prefixes = []  # noqa


def generate_prefix(filename):
    shortname = filename[filename.rfind('/')+1:filename.rfind('.')]
    shortname = re.sub('[^a-zA-Z-_]', '', shortname)
    shortname = re.sub('^-?(.*)-$', r'\1', shortname)
    shortname = shortname.replace('--', '-')
    uppercases = re.sub('[^A-Z]', '', shortname)
    if '-' in shortname:
        candidate = ''.join(part[0] for part in shortname.split('-')).lower()
    elif '_' in shortname:
        candidate = ''.join(part[0] for part in shortname.split('_')).lower()
    elif len(uppercases) <= 3:
        candidate = uppercases.lower()
    else:
        candidate = shortname[:3].lower()
    return unique_prefix(candidate)


def extend_lookup_path(path):
    owlready2.onto_path.append(path)
    return path


if __name__ == '__main__':
    owl2types()
