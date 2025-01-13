#!/bin/bash
pip install poetry
poetry install --no-dev

streamlit run main.py
