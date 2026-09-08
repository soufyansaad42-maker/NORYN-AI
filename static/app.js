const queryInput = document.getElementById("queryInput");
const sendButton = document.getElementById("sendButton");
const resultArea = document.getElementById("resultArea");
const modeButtons = document.querySelectorAll(".mode-button");

let currentMode = "search";

modeButtons.forEach(button => {
    button.addEventListener("click", () => {
        modeButtons.forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        currentMode = button.dataset.mode;
    });
});

sendButton.addEventListener("click", async () => {
    const query = queryInput.value.trim();

    if (!query) {
        queryInput.focus();
        return;
    }

    resultArea.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon">⏳</div>
            <h3>جاري تجهيز طلبك...</h3>
            <p>وضع <strong>${currentMode}</strong> جاهز للربط بمحرك الذكاء الاصطناعي.</p>
        </div>
    `;
});

queryInput.addEventListener("keydown", event => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        sendButton.click();
    }
});
