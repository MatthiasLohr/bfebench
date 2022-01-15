
.PHONY: default diagrams plantuml

default:

diagrams: plantuml

plantuml:
	for i in `find ./ -iname "*.plantuml"` ; do \
	echo "Processing $$i ..." ; \
	curl --silent --fail --data-binary @$$i https://plantuml.k8s.mlohr.com/png/ > $${i%.plantuml}.png; \
	done
