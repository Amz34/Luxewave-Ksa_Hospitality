# 🌊 Luxe Wave KSA — Hospitality Supply Website

AI-powered website for **Luxe Wave Company** — a wholesale hospitality supply
company in Saudi Arabia (hotel amenities, bed & bath linen, room essentials,
and more) serving 4–5 star hotels, furnished apartments, and hospitals.

**Live demo:** [luxewave-ksa.netlify.app](https://luxewave-ksa.netlify.app)

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Stack](https://img.shields.io/badge/Stack-Express%20%2B%20Netlify%20Functions-teal.svg)
![AI](https://img.shields.io/badge/AI-DeepSeek%20LLM-purple.svg)
![Chat](https://img.shields.io/badge/Chat-Live%20AI%20Agent-brightgreen.svg)

## ✨ Features

- **🤖 AI live chat widget** — DeepSeek LLM answers customer questions 24/7
  (products, pricing, delivery, certifications) in English or Arabic
- **📝 Lead capture** — visitors share name + WhatsApp inside the chat; saved
  to `projects/leads/` on the Express server, with WhatsApp fallback on
  serverless hosting
- **👤 Human escalation** — "Talk to a Human" opens WhatsApp/Telegram with the
  visitor's last question pre-filled
- **💬 Floating WhatsApp + Telegram buttons**, contact form, LinkedIn link
- **🧠 Smart AI system prompt** — full business knowledge baked in
  (CR 7050248579, SFDA/ISO/SASO certs, pricing/MOQ/samples/delivery policy)

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript (no frameworks) |
| Backend | Node.js, Express |
| AI | DeepSeek API (OpenAI-compatible), `deepseek-v4-flash` |
| Serverless | Netlify Functions (`netlify/functions/chat.js`) |
| Hosting | Netlify + optional self-hosted Express (port 3001) |

## 🚀 Run Locally

```bash
npm install
cp .env.example .env      # add your DEEPSEEK_API_KEY
npm start                 # → http://localhost:3001
```

Health check: `curl http://localhost:3001/api/health`

## ☁️ Deploy to Netlify

```bash
netlify deploy --prod --dir . --site <your-site-id>
```

The chat widget automatically tries `/api/chat` first, then falls back to
`/.netlify/functions/chat` (the serverless DeepSeek proxy). On Netlify, set
`DEEPSEEK_API_KEY` in Site settings → Environment variables.

## 🔒 Security

- `.env` is git-ignored — **never commit real API keys**
- Serverless function reads the key from environment variables only
- Forms/leads fall back to WhatsApp when no backend storage is available

## 📄 License

MIT — free to use, fork, and learn from.
