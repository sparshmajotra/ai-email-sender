document.getElementById("generateForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const prompt = document.getElementById("prompt").value;

    const response = await fetch("/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({ prompt })
    });

    const data = await response.json();
    
    if (data.email) {
        document.getElementById("emailSection").style.display = "block";
        document.getElementById("emailBody").value = data.email;
    } else {
        alert(data.error || "Failed to generate email");
    }
});

async function sendEmail() {
    const recipient = document.getElementById("recipient").value;
    const subject = document.getElementById("subject").value;
    const body = document.getElementById("emailBody").value;

    const response = await fetch("/send", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({ recipient, subject, body })
    });

    const result = await response.json();
    document.getElementById("status").innerText = result.message || result.error;
}
