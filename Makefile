./english-cooking/types.xml: ./ontologies/*.owl
	owl2types --output $@ \
		--exclude-owl-thing \
		--lookup ./ontologies \
		./ontologies/SLM-cooking.owl:slm

.PHONY: tests
tests: tools
	python -m unittest discover tools/tests
