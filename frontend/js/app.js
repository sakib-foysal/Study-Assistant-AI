let currentData = { topic: '', summary: '', mcqs: [] };

document.getElementById('generateBtn').addEventListener('click', generateContent);
document.getElementById('pdfBtn').addEventListener('click', generatePDF);
document.getElementById('topicInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') generateContent();
});

const historyBtn = document.getElementById('historyBtn');
if (historyBtn) {
  historyBtn.addEventListener('click', loadHistory);
}

async function generateContent() {
  const topic = document.getElementById('topicInput').value.trim();
  if (!topic) {
    alert('Please enter a study topic');
    return;
  }

  const user = JSON.parse(sessionStorage.getItem('user') || 'null');

  currentData.topic = topic;

  const generateBtn = document.getElementById('generateBtn');
  generateBtn.disabled = true;
  generateBtn.textContent = 'Generating...';

  showLoading('summaryContent');
  showLoading('mcqContent');

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        difficulty: 'easy',
        number_of_questions: 4,
        user_id: user ? user.id : null
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Server error');
    }

    const data = await response.json();

    currentData.summary = data.summary || '';
    currentData.mcqs = (data.mcqs || []).map((m) => {
      const letters = ['A', 'B', 'C', 'D'];
      const options = Array.isArray(m.options) ? m.options : [];

      return {
        question: m.question || '',
        options: {
          A: options[0] || '',
          B: options[1] || '',
          C: options[2] || '',
          D: options[3] || ''
        },
        correct: letters[m.answer] || 'A'
      };
    });

    displaySummary(currentData.summary);
    displayMCQs(currentData.mcqs);
    document.getElementById('pdfBtn').disabled = currentData.mcqs.length === 0;

  } catch (error) {
    console.error('Error:', error);
    document.getElementById('summaryContent').innerHTML = `
      <div style="color:#ef4444;text-align:center;padding:20px">
        <p>❌ FRONTEND ERROR: ${error.message}</p>
      </div>`;
    document.getElementById('mcqContent').innerHTML = '';
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate';
  }
}

async function loadHistory(e) {
  e.preventDefault();

  const user = JSON.parse(sessionStorage.getItem('user') || 'null');

  if (!user) {
    alert('Please login first to view history.');
    window.location.href = '/login.html';
    return;
  }

  try {
    showLoading('summaryContent');
    document.getElementById('mcqContent').innerHTML = '';

    const response = await fetch(`/history/${user.id}`);

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to load history');
    }

    const history = await response.json();

    if (!history.length) {
      document.getElementById('summaryContent').innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📚</div>
          <p>No history found</p>
        </div>`;
      return;
    }

    const html = history.map((item) => `
      <div class="mcq-item">
        <h3>${item.topic}</h3>
        <p>${item.summary}</p>
        <small>${item.created_at}</small>
      </div>
    `).join('');

    document.getElementById('summaryContent').innerHTML = html;
    document.getElementById('mcqContent').innerHTML = '';

  } catch (error) {
    console.error('History Error:', error);
    document.getElementById('summaryContent').innerHTML = `
      <div style="color:#ef4444;text-align:center;padding:20px">
        <p>❌ HISTORY ERROR: ${error.message}</p>
      </div>`;
  }
}

function showLoading(id) {
  document.getElementById(id).innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <span>Generating content...</span>
    </div>`;
}

function displaySummary(summary) {
  document.getElementById('summaryContent').innerHTML = `
    <div class="summary-content">${summary}</div>
    <div class="bot-message">
      <div class="bot-avatar">🤖</div>
      <div class="bot-bubble">Here is the summary on your topic!</div>
    </div>`;
}

function displayMCQs(mcqs) {
  const mcqHTML = mcqs.map((mcq, idx) => `
    <div class="mcq-item">
      <div class="mcq-question">${idx + 1}. ${mcq.question}</div>
      <div class="mcq-options">
        <div class="mcq-option">(A) ${mcq.options.A}</div>
        <div class="mcq-option">(B) ${mcq.options.B}</div>
        <div class="mcq-option">(C) ${mcq.options.C}</div>
        <div class="mcq-option">(D) ${mcq.options.D}</div>
      </div>
      <div class="correct-answer">Correct Answer: ${mcq.correct}</div>
    </div>`).join('');

  document.getElementById('mcqContent').innerHTML = `<div class="mcq-list">${mcqHTML}</div>`;
}

function generatePDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setFontSize(20);
  doc.text('AI Study Assistant', 105, 20, { align: 'center' });

  doc.setFontSize(16);
  doc.text(`Topic: ${currentData.topic}`, 20, 35);

  doc.setFontSize(14);
  doc.text('Summary:', 20, 50);

  doc.setFontSize(11);
  const summaryLines = doc.splitTextToSize(currentData.summary, 170);
  doc.text(summaryLines, 20, 60);

  let yPos = 60 + (summaryLines.length * 7) + 15;

  doc.setFontSize(14);
  doc.text('Multiple Choice Questions:', 20, yPos);
  yPos += 10;

  currentData.mcqs.forEach((mcq, idx) => {
    if (yPos > 250) {
      doc.addPage();
      yPos = 20;
    }

    doc.setFontSize(12);
    doc.text(`${idx + 1}. ${mcq.question}`, 20, yPos);
    yPos += 8;

    doc.setFontSize(10);
    Object.entries(mcq.options).forEach(([key, val]) => {
      doc.text(`(${key}) ${val}`, 25, yPos);
      yPos += 6;
    });

    doc.text(`Correct Answer: ${mcq.correct}`, 25, yPos);
    yPos += 12;
  });

  doc.save(`${currentData.topic.replace(/\s+/g, '_')}_study_guide.pdf`);
}