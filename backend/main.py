#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端应用启动文件
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=False)
