from __future__ import annotations
import winreg
from anthropic import Anthropic
def scope_smoke(request_text):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key: api_key=winreg.QueryValueEx(key,'ANTHROPIC_API_KEY')[0]
    client=Anthropic(api_key=api_key)
    return client.messages.create(model='claude-sonnet-5',max_tokens=64,messages=[{'role':'user','content':f'Identify only the withdrawn purpose in this request: {request_text}'}])
