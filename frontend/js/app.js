 let currentData = { topic: '', summary: '', mcqs: [] };

        document.getElementById('generateBtn').addEventListener('click', generateContent);
        document.getElementById('pdfBtn').addEventListener('click', generatePDF);
        document.getElementById('topicInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') generateContent();
        });

        async function generateContent() {
            const topic = document.getElementById('topicInput').value.trim();
            if (!topic) { alert('Please enter a study topic'); return; }

            currentData.topic = topic;
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';

            showLoading('summaryContent');
            showLoading('mcqContent');

            try {
                const response = await fetch('https://api.anthropic.com/v1/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'claude-sonnet-4-20250514',
                        max_tokens: 1000,
                        messages: [{
                            role: 'user',
                            content: `Generate educational content for the topic: "${topic}"

Please provide:
1. A clear, concise summary (3-4 sentences)
2. Exactly 4 multiple choice questions with 4 options each (A, B, C, D)

Format your response as JSON:
{
  "summary": "Your summary here",
  "mcqs": [
    {
      "question": "Question text?",
      "options": {
        "A": "Option A",
        "B": "Option B", 
        "C": "Option C",
        "D": "Option D"
      },
      "correct": "B"
    }
  ]
}

Make the questions educational and relevant to the topic.`
                        }]
                    })
                });

                const data = await response.json();
                const content = data.content[0].text;
                const jsonMatch = content.match(/\{[\s\S]*\}/);
                
                if (jsonMatch) {
                    const parsedData = JSON.parse(jsonMatch[0]);
                    currentData.summary = parsedData.summary;
                    currentData.mcqs = parsedData.mcqs;
                    displaySummary(parsedData.summary);
                    displayMCQs(parsedData.mcqs);
                    document.getElementById('pdfBtn').disabled = false;
                } else {
                    throw new Error('Failed to parse AI response');
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('summaryContent').innerHTML = `
                    <div style="color:#ef4444;text-align:center;padding:20px">
                        <p>❌ Error generating content. Please try again.</p>
                    </div>`;
                document.getElementById('mcqContent').innerHTML = '';
            } finally {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate';
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
                    <div class="mcq-question">${idx+1}. ${mcq.question}</div>
                    <div class="mcq-options">
                        <div class="mcq-option">(A) ${mcq.options.A}</div>
                        <div class="mcq-option">(C) ${mcq.options.C}</div>
                        <div class="mcq-option">(B) ${mcq.options.B}</div>
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
            doc.setTextColor(37,99,235);
            doc.text('AI Study Assistant', 105, 20, {align:'center'});

            doc.setFontSize(16);
            doc.setTextColor(0,0,0);
            doc.text(`Topic: ${currentData.topic}`, 20, 35);

            doc.setFontSize(14);
            doc.setTextColor(37,99,235);
            doc.text('Summary:', 20, 50);
            
            doc.setFontSize(11);
            doc.setTextColor(0,0,0);
            const summaryLines = doc.splitTextToSize(currentData.summary, 170);
            doc.text(summaryLines, 20, 60);

            let yPos = 60 + (summaryLines.length * 7) + 15;
            doc.setFontSize(14);
            doc.setTextColor(37,99,235);
            doc.text('Multiple Choice Questions:', 20, yPos);
            yPos += 10;

            currentData.mcqs.forEach((mcq, idx) => {
                if (yPos > 250) { doc.addPage(); yPos = 20; }
                doc.setFontSize(12);
                doc.setTextColor(0,0,0);
                doc.text(`${idx+1}. ${mcq.question}`, 20, yPos);
                yPos += 8;
                doc.setFontSize(10);
                Object.entries(mcq.options).forEach(([key, val]) => {
                    doc.text(`   (${key}) ${val}`, 25, yPos);
                    yPos += 6;
                });
                doc.setTextColor(37,99,235);
                doc.text(`   Correct Answer: ${mcq.correct}`, 25, yPos);
                doc.setTextColor(0,0,0);
                yPos += 12;
            });

            doc.save(`${currentData.topic.replace(/\s+/g, '_')}_study_guide.pdf`);
        }