import { fetch } from 'wix-fetch';

const apiUrl = "https://h9nqr8d1zb.execute-api.ca-central-1.amazonaws.com/prod/chat";

let currentSessionId = null;

$w.onReady(function () {

    // Listen for the student clicking the main Send button
    $w("#sendButton").onClick(() => {
        let userQuestion = $w("#userInput").value;
        if (userQuestion.length > 0) {
            askBrandynAI(userQuestion);
        }
    });

    // Button A: Start Test (NOW ENABLED!)
    $w("#btnA").onClick(() => {
        // Send a direct trigger phrase to wake up the Test Agent
        askBrandynAI("I would like to take a practice test.");
    });

    // Button B: What to Learn
    $w("#btnB").onClick(() => {
        $w("#userInput").value = "What should I learn next regarding: ";
        $w("#userInput").focus();
    });

    // Button C: Error Help (Still in Phase 3)
    $w("#btnC").onClick(() => {
        showComingSoon("Code Debugger");
    });

    // Button D: Student Suggestion (Still in Phase 4)
    $w("#btnD").onClick(() => {
        showComingSoon("Student Suggestions");
    });

});

// show the "Coming Soon" messages without hitting AWS
function showComingSoon(featureName) {
    let currentChat = $w("#chatDisplay").value;

    // Safety check: If the box is empty or just has placeholder dots, clear it cleanly
    if (!currentChat || currentChat.includes("....")) {
        currentChat = "";
    }

    $w("#chatDisplay").value = currentChat + "\n\nAi Teacher Brandyn: The " + featureName + " feature is coming soon in our next Multi-Agent update! For now, try clicking the 'What to Learn' button to explore the curriculum.";
}

// main chat function
async function askBrandynAI(questionText) {
    let currentChat = $w("#chatDisplay").value;

    if (!currentChat || currentChat.includes("....")) {
        currentChat = "";
    }

    // Update the screen to show "Thinking..." 
    $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: Thinking...";
    $w("#userInput").value = ""; // Clear the typing box

    try {
        let payload = { question: questionText };

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

            // Save the memory tag from AWS
            currentSessionId = data.sessionId;

            // 1. Strip out Markdown asterisks
            let cleanAnswer = data.answer.replace(/\*\*/g, "");
            // 2. Strip out any raw XML tags (like <answer_part>) that Bedrock might pass through
            cleanAnswer = cleanAnswer.replace(/<[^>]*>/g, '').trim();

            // Output the AI's response to the screen 
            $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: " + cleanAnswer;
        } else {
            $w("#chatDisplay").value = currentChat + "\n\nYou: " + questionText + "\nAi Teacher Brandyn: Oops! Server error.";
        }
    } catch (error) {
        console.log("Error contacting AWS: ", error);
    }
}