import argparse
import re
import sys
import xml.etree.ElementTree as ET

from xml.dom import minidom
from pathlib import Path
from urllib.parse import unquote


import owlready2


def owl2types():
    """Converts owl files into OpenCCG grammar types.xml files.

    This is the entrypoint for the command line program owl2types.
    Please refer to

        owl2types --help

    to get all details of how the arguments work.

    The general idea, however, is to provide an output file and a list of owl
    files with optional prefixes:

        owl2types --outfile types.xml ontology1.owl ontology2.owl:ABC

    The ontologies' internal imports are loaded automatically. All ontologies
    are prefixed to distinguish them in OpenCCG. If you don't provide a prefix,
    the tool invents a prefix in a deterministic fashion, so it should stay the
    same (for as long as the ontology does not change its name, i.e. the last
    part of its IRI). In the example above, ontology1.owl would, assuming
    its IRI also ends in ontology1.owl, get the prefix ont, while ontology2
    would get the prefix ABC.

    It is possible to provide URLs for ontology files, even with prefixes.

    If you are working on multiple local ontologies and want to make sure that
    they are loaded instead of their online parts, you can use the --lookup
    flag to provide additional paths where owlready2 searches for ontologies
    first.
    """
    unique_prefix.prefixes = []
    arguments = parse_args()

    ontologies, ontology_prefix_map = load_ontologies(arguments.ontologies)
    classes = extract_classes(ontologies, ontology_prefix_map)
    if arguments.exclude_owl_thing:
        classes = exclude_owl_thing(classes)
    xml = classes2xml(classes, ontologies)

    print(xml, file=arguments.output)


class OntologyArgument:
    """Holds the URL and the prefix for the ontologies. It also provides
    the argument method to allow for an easy integration as an argparse type.
    """

    def __init__(self, filename, prefix=None):
        """Stores the URL and the prefix for the ontologies. If the filename
        starts with http, it is assumed to be a web URL."""
        if filename.startswith('http'):
            self.uri = unquote(filename)
        else:
            self.uri = unquote(Path(filename).absolute().as_uri())
            # Windows file URLs should only have two slashes for owlready2
            if self.uri[9] == ':':
                self.uri = self.uri.replace('///', '//')

        if prefix is not None:
            self.prefix = unique_prefix(prefix)
        else:
            self.prefix = generate_prefix(self.uri)

    def __str__(self):
        return f'Ontology: {self.prefix} -- {self.uri}'

    @staticmethod
    def argument(argument):
        """Parses an argument from the command line.

        Splits the argument at the last colon (:), unless it is a web URL (i.e.
        starts with "http" without a second colon.

        The first split part is considered the filepath or url, the second part
        the forced prefix.

        Examples:
            http://example.com/ontology.owl:ABC
            => http://example.com/ontology.owl and ABC
            http://example.com/ontology.owl
            => http://example.com/ontology.owl and no prefix
            ./ontologies/onto.owl
            => ./ontologies/onto.owl and no prefix
            ./ontologies/onto.owl:ABC
            => ./ontologies/onto.owl and ABC

        Issues:
            On Windows, absolute paths contain colons which can be interpreted
            wrongly. The best suggestion right  now is to supply relative paths
            wherever possible.

        Args:
            argument: A command line argument string.

        Returns:
            An OntologyArgument.
        """
        if argument.startswith('http') and argument.count(':') == 1:
            return OntologyArgument(argument)
        return OntologyArgument(*argument.rsplit(':', 1))


def load_ontologies(ontology_arguments):
    """Loads the ontologies provided as a list of OntologyArgument.

    Also loads all indirectly imported ontologies. Each ontology is prefixed
    with the specified prefix (OntologyArgument.prefix) or with a generated
    prefix (generate_prefix). The manually specified prefixes take precedence.

    Args:
        ontology_arguments: A list of OntologyArguments.

    Returns:
        A tuple, the first value is a list of loaded ontologies (owlready2
        objects), the second value is the map of ontology names to the
        prefix.
    """
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
    """Returns the prefixed classname as it is needed in OpenCCG.

    Args:
        cls: The ontology class (e.g. an entry of ontology.classes())
        ontology_prefix_map: A map as returned by load_ontologies, which maps
                             ontology names to prefixes.

    Returns:
        "prefix-ClassName", e.g. for the class "Cup" in the ontology "Semantic
        Lower Model" with the prefix "slm", the return value would be "slm-Cup".
    """
    return f'{ontology_prefix_map[cls.namespace.ontology.name]}-{cls.name}'


def extract_classes(ontologies, ontology_prefix_map):
    """Extracts all classes of a given ontology.

    Each class is prefixed with the proper prefix as given by classname. For
    each class, the list of immediate parents is created and filled with all
    immediate parent classes.

    Args:
        ontologies: A list of ontologies
        ontology_prefix_map: A prefix map

        Both arguments are returned by load_ontologies.

    Returns:
        A dictionary of classnames to a list of parent classnames:
        {
            'slm-Cup': ['gum-Container', 'gum-Thing']
        }
        etc.
    """
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
    """This removes the owl-Thing entry and all parent entries from a class
    dictionary as given by extract_classes.

    In general, owl assumes owl-Thing as the top level entity, but for some
    applications it makes sense to remove this entity.

    Args:
        classes: A class dictionary of a classname mapping to a list of parent
                 classnames.
    Returns:
        The input without the owl-Thing entry.

    Caveat:
        Side-effect: The original object is also changed.
    """
    thing = 'owl-Thing'
    try:
        del classes[thing]
    except KeyError:
        pass
    for cls, parents in classes.items():
        classes[cls] -= set([thing])
    return classes


def classes2xml(classes, ontologies):
    """Generates the XML string from the classes and ontologies.

    Args:
        classes: A class dictionary of a classname mapping to a list of parent
                 classnames.
        ontologies: The list of used ontologies.

    Returns:
        A string which can be parsed as valid xml, in the format of the types.xml
        needed for OpenCCG.
    """
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
    """Defines and parses the command line arguments for the command line tool.

    Returns:
        The parsed command line arguments, see argparse.parse_args for more details.
    """
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
    """Ensures unique prefixes.

    If two ontologies would get the same prefix via generate_prefix, this
    method ensures that an increasing number is added to it.
    So for example, if the prefix slm already exists but is passed to this
    function, the returned prefix would be slm0. If another prefix slm is
    needed, slm and slm0 already exist and thus this function would return
    slm1.

    Args:
        prefix: The prefix to check and modify

    Returns:
        A string denoting the prefix or, if needed, the prefix with an
        additional number.
    """
    candidate = prefix
    counter = 0
    while candidate in unique_prefix.prefixes:
        candidate = prefix + str(counter)
        counter += 1
    unique_prefix.prefixes.append(candidate)
    return candidate
unique_prefix.prefixes = []  # noqa


def generate_prefix(filename):
    """Generates a prefix from a given owl filename.

    First, the filename is sanitized, thus all symbols but letters, dashes, and
    underscores are removed. The extension and the path are also removed.
    Then, trailing and preceding dashes are removed, and potential double
    dashes are trimmed down to a single dash. (Caveat: n dashes become
    ceil(n/2) dashes).

    If there are still dashes left, they are assumed to denote separators
    between name parts, so the first letter and each letter preceded by a dash
    are used as the prefix.
    The same applies for underscores, if no dashes are present.
    Else, if there are less than four uppercase letters inside the filename,
    these uppercase letters are taken as the prefix.
    If none of the above works, the first three letters are used as a prefix.

    If a prefix already exists, a unique version is returned, generated using
    unique_prefix.
    All prefixes are converted to lowercase.

    Args:
        filename: The owl filanem.

    Returns:
        A prefix for the ontology, following the rules written above.
    """
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
    """Wraps owlready2.onto_path.append such that a call also returns the path.

    This is needed so that the argparser can properly handle the paths.
    Each path passed to this function is added to the onto_path and returned.

    Args:
        path: A filepath.

    Returns:
        path
    """
    owlready2.onto_path.append(path)
    return path


if __name__ == '__main__':
    owl2types()
