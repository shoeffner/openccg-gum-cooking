import functools
import sys
import unittest

import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from xml.dom import minidom


from owl2types import owl2types


TESTDATA = Path(__file__).parent / 'data'


def argv(*owls):
    """Prepares the command line arguments for owl2types."""
    args = ['owl2types', '--exclude-owl-thing', '--lookup', str(TESTDATA)] + list(owls)
    return patch.object(sys, 'argv', args)


def owl(name, prefix='test'):
    """Allows to simply specify a single owl file inside the data directory."""
    return f'{TESTDATA}/{name}.owl:{prefix}'


class SysOut:
    """Wraps sysout so that the output of owl2types can be captured easily."""
    def __enter__(self):
        self.original_stdout = sys.stdout
        sys.stdout = StringIO()
        return sys.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout


def parse_types(file_contents):
    """Parses the string file_contents into an xml tree structure."""
    return ET.fromstring(file_contents)


def expected_types(name):
    """Returns the expected types.xml content."""
    return parse_types(Path(f'{TESTDATA}/{name}.xml').read_text())


def prettify(xml_tree):
    return minidom.parseString(ET.tostring(xml_tree)).toprettyxml(newl='')


def compare_types(actual, expected):
    """Compares to types file structures."""
    expected_types = sorted(expected.findall('type'), key=lambda x: x.get('name'))
    actual_types = sorted(actual.findall('type'), key=lambda x: x.get('name'))

    for exp, act in zip(expected_types, actual_types):
        if exp.get('parents') is None:
            if act.get('parents') is not None:
                return False
            else:
                continue
        if sorted(exp.get('parents').split(' ')) != sorted(act.get('parents').split(' ')):
            return False

    return True


def owl_test(expected_name, *owls):
    """Wraps a class method to create a default test procedure.

    A test consists of one or multiple owl file names inside the
    TESTDATA directory. Owl files should be specified using the `owl` function:

        @owl_test('single_entry', owl('empty', 'a'), owl('single_entry'))

    Here, the first single_entry refers to the expected output stored in
    single_entry.xml, while empty and single_entry inside the owl calls refer
    to the respective .owl files. The entities in `empty` should be prefixed
    with 'a' in the final types file.

    The test prepares command line arguments as if owl2types would be called
    from the command line and calls it, capturing sys.stdout:

        (pseudo code)
        with mocked command line args and sys.stdout:
            owl2types()
            compare actual output with expected output

    The output is parsed in the same way as the expected file is parsed, to
    ensure that even with different white space or formatting the content
    is correct.

    Note that the decorator discards the functionality of the method it
    decorates.

    Args:
        expected_name: The name part of the types.xml inside TESTDATA
        owls: `owl(...)` calls to refer to the owl files inside TESTDATA and
            provide prefixes.

    Raises:
        AssertionError: If the actual output does not match the expected
            output.
    """
    def decorator(func):
        @functools.wraps(func)
        def test(self):
            with argv(*owls), SysOut() as out:
                owl2types()
                actual = parse_types(out.getvalue())
                expected = expected_types(expected_name)
            assert compare_types(actual, expected), \
                f'\n\nExpected:\n\n{prettify(expected)}\n\nActual:\n\n{prettify(actual)}\n\n'
        return test
    return decorator


class TestExportTypes(unittest.TestCase):
    @owl_test('empty',
              owl('empty'))
    def test_empty(self):
        pass

    @owl_test('single_entry',
              owl('single_entry'))
    def test_single_entry(self):
        pass

    @owl_test('multi_entry',
              owl('multi_entry'))
    def test_multi_entry(self):
        pass

    @owl_test('single_branch',
              owl('single_branch'))
    def test_single_branch(self):
        pass

    @owl_test('multi_branch',
              owl('multi_branch'))
    def test_multi_branch(self):
        pass

    @owl_test('multi_inheritance',
              owl('multi_inheritance'))
    def test_multi_inheritance(self):
        pass

    @owl_test('complex_inheritance',
              owl('complex_inheritance'))
    def test_complex_inheritance(self):
        pass

    @owl_test('multi_onto',
              owl('multi_onto_A', 'A'),
              owl('multi_onto_B', 'B'))
    def test_multi_onto(self):
        pass

    @owl_test('simple_import',
              owl('simple_import_base', 'base'),
              owl('simple_import_ext', 'ext'))
    def test_simple_import(self):
        pass

    @owl_test('complex_import',
              owl('complex_import_a', 'a'),
              owl('complex_import_b', 'b'),
              owl('complex_import_c', 'c'),
              owl('complex_import_d', 'd'))
    def test_complex_import(self):
        pass


def load_ccg(name):
    """Returns the expected ccg content."""
    return Path(f'{TESTDATA}/{name}.ccg').read_text()


def compare_ccg(actual, expected):
    """Compares to ccg files."""
    return actual.strip() == expected.strip()


def ccg_test(expected_name, *owls, existing_ccg=False):
    """Wraps a class method to create a default test procedure.

    A test consists of one or multiple owl file names inside the
    TESTDATA directory. Owl files should be specified using the `owl` function:

        @ccg_test('single_entry', owl('empty', 'a'), owl('single_entry'))

    Here, the first single_entry refers to the expected output stored in
    single_entry.ccg, while empty and single_entry inside the owl calls refer
    to the respective .owl files. The entities in `empty` should be prefixed
    with 'a' in the final types file.

    The test prepares command line arguments as if owl2types would be called
    from the command line and calls it:

        (pseudo code)
        if existing_ccg is True, create output file with content from _in file
        with mocked command line args:
            owl2types()
        compare actual output with expected output
        remove output file

    The output is parsed in the same way as the expected file is parsed, to
    ensure that even with different white space or formatting the content
    is correct.

    Note that the decorator discards the functionality of the method it
    decorates.

    Args:
        expected_name: The name part of the ccg file inside TESTDATA. Will be
                       used for both: if existing_ccg is true,
                       expected_name_in.ccg is used as the import, while
                       expected_name.ccg is used as the expected output.
        owls: `owl(...)` calls to refer to the owl files inside TESTDATA and
              provide prefixes.
        existing_ccg: If this is true, the _out file will be created using the
                      data from the _in file before calling owl2types.

    Raises:
        AssertionError: If the actual output does not match the expected
            output.
    """
    def decorator(func):
        @functools.wraps(func)
        def test(self):
            outfile = Path(expected_name + '_out.ccg')
            if existing_ccg:
                outfile.write_text(load_ccg(expected_name + '_in'))

            with argv('--output', str(outfile), '--format', 'ccg', *owls):
                owl2types()
                expected = load_ccg(expected_name)
            actual = outfile.read_text()

            try:
                assert compare_ccg(actual, expected), \
                    f'\n\nExpected:\n\n{expected}\n\nActual:\n\n{actual}\n\n'
            finally:
                outfile.unlink()
                if existing_ccg:
                    Path(expected_name + '_out.ccg.bak').unlink()

        return test
    return decorator


class TestExportCCG(unittest.TestCase):
    @ccg_test('empty',
              owl('empty'))
    def test_empty(self):
        pass

    @ccg_test('single_entry',
              owl('single_entry', 's'))
    def test_prefix(self):
        pass

    @ccg_test('complex_inheritance',
              owl('complex_inheritance'))
    def test_complex_inheritance(self):
        pass

    @ccg_test('single_entry_insert',
              owl('single_entry'),
              existing_ccg=True)
    def test_insertion(self):
        pass

    @ccg_test('single_entry_overwrite',
              owl('single_entry'),
              existing_ccg=True)
    def test_overwriting_insertion(self):
        pass
