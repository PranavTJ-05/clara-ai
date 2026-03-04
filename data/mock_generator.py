import os

# Create 5 mock demo transcripts
demo_transcripts = {
    "demo_1": """
Agent: Hi this is Clara from Apex Fire Protection, how can I help you?
Caller: Hi, I'm calling from Main Street Apartments. We are looking for a new fire protection company.
Agent: Great! What kind of services do you offer?
Caller: Well, we have sprinklers and fire alarms. I understand you guys do both?
Agent: Yes, we do.
Caller: We also have emergencies sometimes, like if a sprinkler head gets knocked off. Do you guys handle those 24/7?
Agent: Yes, we have 24/7 dispatch for emergencies.
Caller: Perfect. I think our business hours are roughly 8 to 5 on weekdays. Do I need to integrate with anything?
Agent: We use ServiceTrade for our backend.
Caller: Ah, right, we're not familiar with that yet, maybe we can figure it out later.
Agent: Sounds good, we will send over some pricing.
    """,
    "demo_2": """
Agent: Hello, Clara Answers here for Cool Breeze HVAC.
Caller: Hi, I'm trying to get someone out here to fix our AC at the restaurant. It's totally broken.
Agent: I'm sorry to hear that. I can get someone out. Are you looking to set up an account too?
Caller: Yeah, maybe. I just need this fixed first, it's 90 degrees in here. Is this an emergency? I guess so.
Agent: Yes we can treat AC out in a restaurant as an emergency.
Caller: Cool. What are your hours?
Agent: We usually work from 7 AM to 4 PM Monday through Friday.
Caller: Okay. Can you guys just call my manager if you show up? His name is Bob.
Agent: Yes we will add Bob to the routing rules.
    """,
    "demo_3": """
Agent: Welcome to Secure Alarm Systems demo voice agent.
Caller: Hey. I want to replace my current alarm provider. Our panels keep beeping.
Agent: We can definitely help with panel beeping. That's a common issue.
Caller: If the panel is beeping, is that an emergency? 
Agent: Usually we only consider it an emergency if the alarm is actually going off or if there is a fire. Beeping is a normal service call.
Caller: I see. Our building office is open 9 to 6. If it's a real emergency, my cell phone is the number to call. 
Agent: Okay, we'll route emergency calls to your cell phone.
Caller: Thanks. What else do you need?
Agent: We will follow up with an email later!
    """,
    "demo_4": """
Agent: This is Clara for Spark Electrical.
Caller: Hi, we manage a few properties in the downtown area. Looking into your services.
Agent: Excellent. We handle all electrical maintenance.
Caller: Sometimes we have power outages at the strip mall, which is a big deal. We consider that an emergency.
Agent: Power outage is definitely an emergency. We dispatch immediately for those.
Caller: If it's just a broken lightbulb outside, can we just leave a message?
Agent: Yes, non-emergencies can just leave a voicemail after hours.
Caller: Great. I don't know my exact office hours right now, maybe 8:30 to 4:30? Let me check on that later.
Agent: No problem.
    """,
    "demo_5": """
Agent: Delta Sprinkler Systems, how can I assist?
Caller: Hey, I want to learn more about your services. Do you guys do inspections?
Agent: Yes, we do annual and quarterly sprinkler inspections.
Caller: If a pipe bursts in the winter, that happens sometimes here, do you have someone on call?
Agent: Yes, burst pipes are top priority emergencies. We have a technician on call 24/7.
Caller: Great. We use a software called Housecall Pro, can you connect to that?
Agent: We might be able to, we can discuss integration later.
Caller: Okay, talk later.
    """
}

# Create 5 mock onboarding transcripts (matching the demos)
onboarding_transcripts = {
    "onboarding_1": """
Agent: Hi, welcome to your onboarding for Apex Fire Protection. Let's finalize your setup.
Caller: Great. So my actual business hours are 8:00 AM to 5:00 PM EST, Monday through Friday. 
Agent: Got it. And for emergencies?
Caller: Emergencies are ONLY active sprinkler leaks or fire alarms triggered. Everything else is non-emergency.
Agent: Understood. Who do we call for emergencies?
Caller: Call dispatch first at 555-0199. If they don't answer within 30 seconds, fallback and call my cell at 555-0100.
Agent: Okay, and any integration rules?
Caller: Yes, please NEVER create sprinkler jobs in ServiceTrade automatically. Only log notes.
    """,
    "onboarding_2": """
Agent: Hello, this is your onboarding for Cool Breeze HVAC.
Caller: Hey. Let's get this done. My hours are strictly 7:00 AM to 5:00 PM Central Time, Monday to Friday.
Agent: Perfect. We discussed AC out in a restaurant as an emergency. Anything else?
Caller: Yes, walk-in freezer failure is also an emergency. 
Agent: And routing?
Caller: Try transferring to our main line. If it fails, let them know we will call them back in 15 minutes. No fallback number needed.
Agent: Can we book appointments directly in your calendar?
Caller: Yes, for non-emergencies during business hours you can book them.
    """,
    "onboarding_3": """
Agent: Onboarding for Secure Alarm Systems.
Caller: Hi. Okay, our hours are 9:00 AM to 6:00 PM Pacific Time, Mon-Fri.
Agent: We previously said emergencies are only active alarms going off. 
Caller: Correct. If it's just a panel beep, tell them to wait until morning. For active alarms, call my cell directly at 555-0222.
Agent: What if you don't answer?
Caller: Keep trying every 5 minutes for up to 3 tries. If still no answer, tell the caller to call 911.
    """,
    "onboarding_4": """
Agent: Spark Electrical onboarding.
Caller: Let's finalize. Office hours are confirmed: 8:30 AM to 4:30 PM Mountain Time, Monday-Friday.
Agent: We noted power outages as emergencies.
Caller: Yes, and also exposed live wires. Those are emergencies.
Agent: For after hours emergencies?
Caller: Route to the on-call tech at 555-0444. If they don't answer, just apologize and say we'll reach out ASAP.
Agent: And non-emergencies?
Caller: Tell them to leave a message.
    """,
    "onboarding_5": """
Agent: Delta Sprinklers onboarding.
Caller: Hello. We are ready. Hours are 7:30 AM to 4:00 PM Eastern Time.
Agent: Burst pipes are your emergencies.
Caller: Yes. If a pipe bursts, immediately transfer to the 24/7 hotline at 555-0555. 
Agent: What if the transfer fails?
Caller: If it fails, wait 60 seconds and try again. 
Agent: Regarding Housecall Pro?
Caller: We decided not to integrate right now. Keep it out of the system. Let the voice agent just send us an email summary of the call.
    """
}


def main():
    inbox_dir = os.path.join(os.path.dirname(__file__), "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    
    for filename, content in demo_transcripts.items():
        filepath = os.path.join(inbox_dir, f"{filename}.txt")
        with open(filepath, "w") as f:
            f.write(content.strip())
        print(f"Created {filepath}")

    for filename, content in onboarding_transcripts.items():
        filepath = os.path.join(inbox_dir, f"{filename}.txt")
        with open(filepath, "w") as f:
            f.write(content.strip())
        print(f"Created {filepath}")


if __name__ == "__main__":
    main()
