const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '1mb' }));

// Serve static files (the existing Luxe Wave website)
app.use(express.static(__dirname));

// OpenAI-compatible client initialization (supports DeepSeek via baseURL)
const openai = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY || process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL || 'https://api.deepseek.com',
});

const MODEL = process.env.DEEPSEEK_MODEL || process.env.OPENAI_MODEL || 'deepseek-v4-flash';

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    model: MODEL,
    timestamp: new Date().toISOString(),
  });
});

// Contact form submission endpoint
const fs = require('fs');
const path = require('path');

app.post('/api/contact', (req, res) => {
  const { name, phone, email = '', message = '' } = req.body || {};

  if (!name || !phone) {
    return res.status(400).json({ error: 'Name and phone are required' });
  }

  const entry = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    name,
    phone,
    email,
    message,
    receivedAt: new Date().toISOString(),
  };

  const dir = path.join(__dirname, 'projects', 'submissions');
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${entry.id}.json`);
  fs.writeFileSync(file, JSON.stringify(entry, null, 2), 'utf8');

  console.log(`📩 New contact submission from ${name} (${phone})`);
  res.json({ success: true, id: entry.id });
});

// Lead capture endpoint (chat widget)
app.post('/api/lead', (req, res) => {
  const { name, whatsapp, email = '', message = '', source = 'chat-widget' } = req.body || {};

  if (!name || !whatsapp) {
    return res.status(400).json({ error: 'Name and WhatsApp are required' });
  }

  const entry = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
    name,
    whatsapp,
    email,
    message,
    source,
    receivedAt: new Date().toISOString(),
  };

  const dir = path.join(__dirname, 'projects', 'leads');
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${entry.id}.json`);
  fs.writeFileSync(file, JSON.stringify(entry, null, 2), 'utf8');

  console.log(`💼 New lead from ${name} (${whatsapp}) — source: ${source}`);
  res.json({ success: true, id: entry.id });
});

// General chat completion endpoint
const LUXE_WAVE_SYSTEM = `You are the Luxe Wave live assistant — a friendly, professional customer support agent for Luxe Wave Company, a wholesale hospitality supply company in Saudi Arabia.

BUSINESS FACTS (use these, never invent others):
- Name: Luxe Wave Company
- Country: Kingdom of Saudi Arabia (KSA)
- Commercial Registration (CR): 7050248579
- Certifications: SFDA, ISO 9001, SASO
- Phone/WhatsApp: +966 582 104 381
- Email: azengineeringapp@gmail.com
- Products: hotel amenities, bed & bath linen, mattresses, room essentials, prayer rugs, Qurans, Qibla signs, electronic safes, door hardware, luggage trolleys, laundry trolleys, bathroom mirrors, LED fixtures, kettles, cups, room service sets, honour barriers, lobby signage
- Serves: 4-star and 5-star hotels, furnished apartments, hospitals
- Coverage: all KSA
- Stats: 135+ hotels served, 200+ product lines, 4-5 star grade clients
- Pricing: quotation-based; depends on product type and order volume (volume discounts available for bulk hotel orders)
- MOQ: varies by product — the sales team confirms the minimum on the quotation
- Samples: free sample presentation available on request — the team arranges it
- Delivery: across all KSA; stock items typically 24-72 hours, bulk/factory orders scheduled with the team
- Working hours: AI assistant is 24/7; the sales team replies during business hours (KSA time)

BEHAVIOR:
- Answer in the same language the customer uses (Arabic or English)
- Be concise, warm, and helpful — like a 5-star hotel concierge
- If asked about pricing, MOQ, quotation, or samples: say the team will send a detailed quotation — ask them to click the "Talk to a Human" button (opens WhatsApp/Telegram pre-filled) or share their WhatsApp number
- If the customer wants a human agent: tell them to click the "Talk to a Human" button — it opens WhatsApp/Telegram with their message pre-filled
- Never invent prices, addresses, or certifications beyond what is listed above
- If you don't know something, be honest and offer to connect them with the team
- End replies with a friendly tone`;

app.post('/api/chat', async (req, res) => {
  try {
    const { messages, temperature = 0.7, max_tokens = 2048 } = req.body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'messages array is required and must not be empty',
      });
    }

    const completion = await openai.chat.completions.create({
      model: MODEL,
      messages: [
        { role: 'system', content: LUXE_WAVE_SYSTEM },
        ...messages,
      ],
      temperature,
      max_tokens,
    });

    res.json({
      success: true,
      data: completion.choices[0].message,
      usage: completion.usage,
    });
  } catch (error) {
    console.error('OpenAI API Error:', error);
    res.status(500).json({
      error: 'OpenAI API Error',
      message: error.message,
    });
  }
});

// Stream chat completion endpoint
app.post('/api/chat/stream', async (req, res) => {
  try {
    const { messages, temperature = 0.7, max_tokens = 2048 } = req.body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'messages array is required and must not be empty',
      });
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const stream = await openai.chat.completions.create({
      model: MODEL,
      messages,
      temperature,
      max_tokens,
      stream: true,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || '';
      if (content) {
        res.write(`data: ${JSON.stringify({ content })}\n\n`);
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();
  } catch (error) {
    console.error('OpenAI Stream Error:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: 'OpenAI Stream Error', message: error.message });
    }
    res.end();
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Luxe Wave server running at http://localhost:${PORT}`);
  console.log(`🤖 OpenAI model: ${MODEL}`);
  console.log(`📁 Serving static files from: ${__dirname}`);
});
