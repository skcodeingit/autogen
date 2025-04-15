#!/bin/bash

while true; do

python plan_retrieval/increment_index.py

python eval.py configs/gaia/1111_19.yaml
python eval.py configs/gaia/1111_17.yaml
python eval.py configs/gaia/1110_19.yaml
python eval.py configs/gaia/1110_17.yaml
python eval.py configs/gaia/1101_19.yaml
python eval.py configs/gaia/1101_17.yaml
python eval.py configs/gaia/1100_19.yaml
python eval.py configs/gaia/1100_17.yaml

python eval.py configs/gaia/1011_19.yaml
python eval.py configs/gaia/1011_17.yaml
python eval.py configs/gaia/1010_19.yaml
python eval.py configs/gaia/1010_17.yaml
python eval.py configs/gaia/1001_19.yaml
python eval.py configs/gaia/1001_17.yaml
python eval.py configs/gaia/1000_19.yaml
python eval.py configs/gaia/1000_17.yaml

python eval.py configs/gaia/0011_19.yaml
python eval.py configs/gaia/0011_17.yaml
python eval.py configs/gaia/0010_19.yaml
python eval.py configs/gaia/0010_17.yaml
python eval.py configs/gaia/0001_19.yaml
python eval.py configs/gaia/0001_17.yaml
python eval.py configs/gaia/0000_19.yaml
python eval.py configs/gaia/0000_17.yaml

done
