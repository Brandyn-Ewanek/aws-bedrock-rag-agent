import { fetch } from 'wix-fetch';

// This is the door to your AWS backend
const apiUrl = "https://h9nqr8d1zb.execute-api.ca-central-1.amazonaws.com/prod/chat";

// The memory tracker variable:
let currentSessionId = null;

$w.onReady(function () {

    // 1. Listen for the student clicking the main Send button
    $w("#sendButton").onClick(() => {
        let userQuestion = $w("#userInput").value;
        if (userQuestion.length > 0) {
            askBrandynAI(userQuestion);
        }
    });

    // 2. Button A: Start Test
    $w("#btnA").onClick(() => {
        askBrandynAI("Can you give me a standard text-based practice test question based on our curriculum?");
    });

    // 3. Button B: Learning Material
    $w("#btnB").onClick(() => {
        $w("#userInput").value = "Can you guide me to the learning materials for: ";
        $w("#userInput").focus();
    });

    // 4. Button C: Error Help
    $w("#btnC").onClick(() => {
        $w("#userInput").value = "I'm getting an error. Here is my code and the error message:\n\n";
        $w("#userInput").focus();
    });

});

// 5. The function that actually talks to AWS
async function askBrandynAI(questionText) {
    let currentChat = $w("#chatDisplay").value;

    // Safety check: If the box is empty or just has placeholder dots, clear it cleanly
    if (!currentChat || currentChat.includes("....")) {
        currentChat = "";
    }

    // Instantly update the screen to show "Thinking..." 
    $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: Thinking...";
    $w("#userInput").value = ""; // Clear the typing box

    try {
        // --- THE PERFECT QUIZ MEMORY TRICK ---
        let textToSendToAWS = questionText;

        if (questionText.trim().length <= 2) {
            // 1. Find the AI's last message
            let chatChunks = currentChat.split("Ai Teacher Brandyn:");
            let lastQuestion = "machine learning practice test";

            if (chatChunks.length > 1) {
                let aiLastMessage = chatChunks[chatChunks.length - 1];

                // 2. Split by the dashed line and grab the BOTTOM half
                let messageParts = aiLastMessage.split("---");
                // WE REMOVED THE 300 CHARACTER LIMIT HERE! 
                // Now it grabs the full question AND all the a,b,c,d options.
                lastQuestion = messageParts[messageParts.length - 1].trim();
            }

            // 3. Force the AI to grade against the EXACT options it previously generated
            textToSendToAWS = "Here is the exact multiple-choice question you just asked me:\n" + lastQuestion + "\n\nMy answer is: '" + questionText.trim() + "'. Please grade my answer against those exact options. Provide the explanation, and then draw a line (---) and ask ONE NEW practice test question.";
        }

        // Prepare the package 
        let payload = { question: textToSendToAWS };

        // If we have a memory tag, attach it
        if (currentSessionId) {
            payload.sessionId = currentSessionId;
        }

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();

            // Save the memory tag
            currentSessionId = data.sessionId;

            // Output the AI's response to the screen 
            $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: " + data.answer;
        } else {
            $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: Oops! Server error.";
        }
    } catch (error) {
        console.log("Error contacting AWS: ", error);
    }
}