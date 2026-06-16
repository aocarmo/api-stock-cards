"""Acesso aos singletons guardados em app.state."""
from fastapi import Request


def get_store(request: Request):
    return request.app.state.store


def get_manager(request: Request):
    return request.app.state.manager


def get_client(request: Request):
    return request.app.state.mypclient
