#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install Pillow with pre-built wheels
pip install --only-binary=:all: Pillow==10.0.0

# Install all other dependencies
pip install -r requirements.txt