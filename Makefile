GRAMMAR_DIR=./english-cooking
ONTOLOGY_DIR=./ontologies
XML_FILES=$(addprefix ${GRAMMAR_DIR}/,$(addsuffix .xml,grammar lexicon morph testbed types))

${XML_FILES}: ${GRAMMAR_DIR}/english-cooking.ccg
	ccg2xml --prefix='' --dir=$(dir $<) $<
	@rm -f $(addsuffix .bak,$<)

${GRAMMAR_DIR}/english-cooking.ccg: ${ONTOLOGY_DIR}/*.owl
	owl2types --output $@ \
		--format ccg \
		--exclude-owl-thing \
		--lookup ${ONTOLOGY_DIR} \
		${ONTOLOGY_DIR}/SLM-cooking.owl:slm \
		${ONTOLOGY_DIR}/UIO.owl:uio

.PHONY: tests
tests: tools
	python -m unittest discover tools/tests
