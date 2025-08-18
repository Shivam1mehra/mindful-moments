let userId = null;
let lastCheckinId = null;
let currentExerciseStep = 0;

document.getElementById("saveName").onclick = () => {
  const name = document.getElementById("nameInput").value.trim() || "guest";
  userId = name.toLowerCase();
  document.getElementById("onboard").style.display = "none";
  document.getElementById("app").style.display = "block";
  addBot("Hi " + name + "! I'm Mindful Moments. How are you feeling today?");
};

document.getElementById("send").onclick = sendMessage;
document.getElementById("message").addEventListener("keypress", (e) => { if(e.key==='Enter') sendMessage(); });

function addBot(text){
  const div = document.createElement("div"); div.className="bot"; div.innerText = text; document.getElementById("chat").appendChild(div);
}
function addUser(text){
  const div = document.createElement("div"); div.className="user"; div.innerText = text; document.getElementById("chat").appendChild(div);
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  try {
    const response = await fetch("https://mindful-moments-1-glip.onrender.com//checkin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "guest", message: text })
    });

    const data = await response.json();
    addMessage("Bot: " + data.reply, "bot");

    // If there’s a breathing exercise, show it step-by-step
    if (data.exercise && data.exercise.length > 0) {
      for (let step of data.exercise) {
        await new Promise(r => setTimeout(r, 2000)); // wait 2s between steps
        addMessage("🌬️ " + step, "bot");
      }
    }
  } catch (err) {
    addMessage("Bot: (error connecting to server)", "bot");
    console.error(err);
  }
}

async function startExercise(){
  currentExerciseStep = 0;
  await showExerciseStep();
}

async function showExerciseStep(){
  const res = await fetch("/exercise", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({step: currentExerciseStep, checkin_id: lastCheckinId})
  });
  const data = await res.json();
  addBot(data.reply);
  if(data.done){
    currentExerciseStep = 0;
    document.getElementById("exerciseControls").style.display = "none";
  } else {
    currentExerciseStep = data.next_step;
    const nextBtn = document.createElement("button");
    nextBtn.innerText = "Next";
    nextBtn.onclick = async () => {
      nextBtn.remove();
      await showExerciseStep();
    };
    document.getElementById("chat").appendChild(nextBtn);
  }
}

document.getElementById("showHistory").onclick = async () => {
  const res = await fetch("/history/" + encodeURIComponent(userId));
  const data = await res.json();
  addBot("Past check-ins:");
  data.history.forEach(h => addBot(`${h.date.split('T')[0]} — ${h.feeling} — ${h.exercise_done ? "did exercise":"no exercise"}`));
};

document.getElementById("showInsights").onclick = async () => {
  const res = await fetch("/insights/" + encodeURIComponent(userId));
  const data = await res.json();
  document.getElementById("insightsArea").innerText = data.insight;
};
