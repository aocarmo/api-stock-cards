"""
Lambda Proxy - Handler para API Gateway
"""
import json
import sys
import os

# Adicionar layer ao path
sys.path.insert(0, '/opt/python')

from mangum import Mangum
from main import app

# Criar handler para Lambda
handler = Mangum(app, lifespan="off")
