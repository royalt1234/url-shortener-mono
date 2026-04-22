/**
 * api3 – Analytics Reporter Service (Node.js / Express)
 *
 * A lightweight microservice that queries the URL Shortener backend
 * (api1) and exposes a formatted analytics summary endpoint.
 * Demonstrates a third language/runtime in the monorepo.
 */

const express = require("express");
const axios   = require("axios");

const app  = express();
const PORT = process.env.PORT       || 4000;
const API1 = process.env.API1_URL   || "http://localhost:8000";

app.use(express.json());


// ── Health check ─────────────────────────────────────────────────
app.get("/health", (req, res) => {
  res.json({ status: "healthy", service: "analytics-reporter" });
});


// ── GET /report  ─────────────────────────────────────────────────
// Returns a plain-English summary of all shortened links + click stats
app.get("/report", async (req, res) => {
  try {
    const [linksRes, statsRes] = await Promise.all([
      axios.get(`${API1}/api/links`),
      axios.get(`${API1}/api/stats`),
    ]);

    const links = linksRes.data;
    const stats = statsRes.data;

    // Sort links by click count (most clicked first)
    const ranked = [...links].sort((a, b) => b.clicks - a.clicks);

    const report = {
      generated_at  : new Date().toISOString(),
      total_links    : stats.total_links,
      total_clicks   : stats.total_clicks,
      top_links      : ranked.slice(0, 5).map((l) => ({
        short_code : l.short_code,
        title      : l.title || "(no title)",
        original_url: l.original_url,
        clicks     : l.clicks,
        created_at : l.created_at,
      })),
      zero_click_links: links
        .filter((l) => l.clicks === 0)
        .map((l) => l.short_code),
    };

    res.json(report);
  } catch (err) {
    res.status(502).json({
      error  : "Could not reach api1",
      detail : err.message,
    });
  }
});


// ── GET /report/:short_code ───────────────────────────────────────
// Returns a detailed report for a single short code
app.get("/report/:short_code", async (req, res) => {
  const { short_code } = req.params;
  try {
    const response = await axios.get(`${API1}/api/analytics/${short_code}`);
    const data     = response.data;

    const report = {
      short_code    : data.short_code,
      original_url  : data.original_url,
      total_clicks  : data.total_clicks,
      created_at    : data.created_at,
      last_clicked  : data.last_clicked || "Never",
      browsers      : summarizeBrowsers(data.click_details),
    };

    res.json(report);
  } catch (err) {
    const status = err.response?.status || 502;
    res.status(status).json({ error: err.message });
  }
});


// ── Helper: rough browser summary from user-agent strings ─────────
function summarizeBrowsers(clicks) {
  const counts = {};
  for (const click of clicks) {
    const ua = click.user_agent || "Unknown";
    let browser = "Other";
    if (ua.includes("Chrome"))  browser = "Chrome";
    else if (ua.includes("Firefox")) browser = "Firefox";
    else if (ua.includes("Safari"))  browser = "Safari";
    else if (ua.includes("curl"))    browser = "curl/CLI";
    counts[browser] = (counts[browser] || 0) + 1;
  }
  return counts;
}


// ── Start server ──────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`api3 analytics reporter running on port ${PORT}`);
  console.log(`Pointing to api1 at: ${API1}`);
});
