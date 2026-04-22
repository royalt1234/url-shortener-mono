/**
 * Tests for api3 – Analytics Reporter
 * Uses supertest to make HTTP calls against the Express app.
 * api1 calls are mocked so these tests run standalone.
 */

const request = require("supertest");
const axios   = require("axios");
const app     = require("./index"); // we need to export app — see note below

jest.mock("axios");

describe("GET /health", () => {
  it("returns 200 and healthy status", async () => {
    const res = await request(app).get("/health");
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe("healthy");
    expect(res.body.service).toBe("analytics-reporter");
  });
});

describe("GET /report", () => {
  it("returns a formatted report when api1 is reachable", async () => {
    axios.get
      .mockResolvedValueOnce({ data: [
        { short_code: "abc123", clicks: 10, title: "Test", original_url: "https://example.com", created_at: new Date().toISOString() },
        { short_code: "xyz999", clicks: 0,  title: null,   original_url: "https://google.com",  created_at: new Date().toISOString() },
      ]})
      .mockResolvedValueOnce({ data: { total_links: 2, total_clicks: 10 } });

    const res = await request(app).get("/report");
    expect(res.statusCode).toBe(200);
    expect(res.body.total_links).toBe(2);
    expect(res.body.top_links[0].short_code).toBe("abc123");
    expect(res.body.zero_click_links).toContain("xyz999");
  });

  it("returns 502 when api1 is unreachable", async () => {
    axios.get.mockRejectedValue(new Error("Connection refused"));
    const res = await request(app).get("/report");
    expect(res.statusCode).toBe(502);
  });
});
