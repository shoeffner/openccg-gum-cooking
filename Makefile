./english-cooking/english-cooking.ccg: ./ontologies/*.owl
	owl2types --output $@ \
		--format ccg \
		--exclude-owl-thing \
		--lookup ./ontologies \
		./ontologies/SLM-cooking.owl:slm \
		./ontologies/UIO.owl:uio
	@-rm $@.bak

./english-cooking/types.xml: ./ontologies/*.owl
	owl2types --output $@ \
		--exclude-owl-thing \
		--lookup ./ontologies \
		./ontologies/SLM-cooking.owl:slm \
		./ontologies/UIO.owl:uio

.PHONY: tests
tests: tools
	python -m unittest discover tools/tests
