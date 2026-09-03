const express = require("express");
const cors = require("cors");

const app = express();
const PORT = process.env.PORT || 3000;
const PYTHON_URL = process.env.PYTHON_URL || "http://127.0.0.1:8000";

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    name: "NORYN AI Backend",
    version: "3.0.0",
    status: "online",
    pythonService: PYTHON_URL
  });
});

app.get("/api/health", async (req, res) => {
  try {
    const response = await fetch(`${PYTHON_URL}/health`);
    const data = await response.json();

    res.json({
      node: true,
      python: data
    });
  } catch (error) {
    res.status(503).json({
      node: true,
      python: false,
      error: "Python service غير متصل."
    });
  }
});

app.post("/api/chat", async (req, res) => {
  const message = String(req.body?.message || "").trim();

  if (!message) {
    return res.status(400).json({error: "الرسالة فارغة."});
  }

  try {
    const response = await fetch(`${PYTHON_URL}/chat`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message})
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json({
      reply: data.reply,
      engine: "python"
    });
  } catch (error) {
    res.status(503).json({
      error: "تعذر الاتصال بخدمة Python. شغّل ai-service أولًا."
    });
  }
});

app.listen(PORT, () => {
  console.log(`NORYN AI Backend: http://localhost:${PORT}`);
  console.log(`Python AI Service: ${PYTHON_URL}`);
});
