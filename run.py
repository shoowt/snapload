#!/usr/bin/env python3
"""
SnapLoad - Local Development Runner
"""
import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando SnapLoad - Downloader Sem Marca d'Água")
    print("📱 Interface Mobile: http://localhost:8000")
    print("📖 Documentação da API: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
