// Luxe Wave chat proxy — DeepSeek via Netlify Function (serverless)
// Uses native fetch (Node 18+), no npm dependencies required.
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

const MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash';

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method Not Allowed' }) };
  }

  try {
    const { messages, temperature = 0.7, max_tokens = 2048 } = JSON.parse(event.body || '{}');

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Bad Request', message: 'messages array is required and must not be empty' }),
      };
    }

    const apiKey = process.env.DEEPSEEK_API_KEY;
    if (!apiKey) {
      return { statusCode: 500, body: JSON.stringify({ error: 'Missing DEEPSEEK_API_KEY' }) };
    }

    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: LUXE_WAVE_SYSTEM }, ...messages],
        temperature,
        max_tokens,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        statusCode: 502,
        body: JSON.stringify({ error: 'DeepSeek API error', message: data.error?.message || 'Upstream error' }),
      };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: data.choices[0].message,
        usage: data.usage,
      }),
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Chat function error', message: err.message }),
    };
  }
};
