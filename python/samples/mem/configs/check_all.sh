#!/bin/bash
python eval.py configs/check_demonstration.yaml
python eval.py configs/check_retrieval.yaml
python eval.py configs/check_self_teaching.yaml
python eval.py configs/check_teachability.yaml
