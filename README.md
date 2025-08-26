# 🧬 Genesis AI Chat

Chat real-time dengan AI bernama **Genesis**, menggunakan Hugging Face Inference API dan FastAPI.

## 🔧 Fitur
- 💬 Chat antar pengguna (real-time)
- 🤖 AI Assistant bernama Genesis
- 🌐 Web interface sederhana
- 🚀 Deploy mudah ke Railway

## 🚀 Cara Deploy ke Railway

1. Fork atau clone repo ini
2. Buka [Railway.app](https://railway.app) → "New Project" → "Deploy from GitHub"
3. Pilih repo ini
4. Tambahkan environment variable:
   - `HF_API_TOKEN` → ambil dari [Hugging Face Settings](https://huggingface.co/settings/tokens)
5. Deploy!

## 🤗 Model yang Digunakan
- `HuggingFaceH4/zephyr-7b-beta` (bisa diganti di `main.py`)

## 💡 Cara Pakai
- Buka web app
- Ketik pesan
- Untuk panggil AI: ketik `genesis halo` → Genesis akan merespons

---

Dibuat dengan ❤️ oleh [Namamu]