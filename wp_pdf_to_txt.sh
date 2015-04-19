#!/bin/bash
PAPERS_DIR="papers"
mkdir -p ${PAPERS_DIR}/txt
cd ${PAPERS_DIR}/pdf
for x in *.pdf
do
    pdftotext $x
done
mv *.txt ../txt
