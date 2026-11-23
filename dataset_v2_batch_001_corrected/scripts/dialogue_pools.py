"""Surface-text pools for dialogue realisation (no clinical facts live here)."""

GREET_D = [
    "Good morning. Come in, have a seat.", "Hello, please sit down.", "Good afternoon. Take a seat, please.",
    "Hi there, come on in.", "Morning! Make yourself comfortable.", "Good evening. Sorry to keep you waiting.",
    "Hello. Right, let's get started.", "Come in, come in. Pull the door closed behind you, please.",
    "Hi. Thanks for coming in today.", "Good morning, how are you doing today?", "Hello there. Please, sit.",
    "Afternoon. Take the chair by the desk.", "Hi, nice to see you. Sit down, please.",
    "Okay, welcome. Let's see what's going on.", "Good morning. I hope the wait wasn't too long.",
    "Hello, come through.", "Hi, I'm glad you could make it.", "Right, come in and get settled.",
    "Good afternoon. Have a seat and we'll begin.", "Hello again. Come on in.",
    "Morning. Just put your bag down anywhere.", "Evening. Long day, I imagine. Sit down.",
]
ASK_D = [
    "What brings you in today?", "So, what's been going on?", "How can I help you today?",
    "Tell me what's been troubling you.", "What seems to be the problem?",
    "What was the main thing you wanted to talk about?", "Right, what's the trouble?",
    "Go ahead, tell me what's happening.", "What's been bothering you?",
    "In your own words, what's happened?", "So, how have things been?", "Okay. Start wherever you like.",
    "What made you decide to come in?", "Tell me from the beginning, what's been happening?",
]
GREET_P = [
    "Good morning, doctor.", "Hello.", "Hi, doctor.", "Thank you.", "Morning.",
    "Hello, doctor. Thanks for seeing me.", "Thanks. Sorry, I'm a little early.", "Hi.",
    "Good afternoon.", "Hello, doctor, thank you.", "Hi. Thanks.", "Evening, doctor.",
    "Thanks, doctor. It's been a long few days.", "Hello. Is it okay if I sit here?",
]
P_FIRST = ["Good morning, doctor. Can I come in?", "Hello doctor, sorry, am I early?", "Hi, doctor. Is this the right room?",
           "Afternoon, doctor.", "Excuse me, doctor, should I sit here?"]
D_AFTER_PFIRST = ["Yes, come in, take a seat. What can I do for you today?", "You're fine, sit down. So, what brings you in?",
                  "Right on time. Sit, please. How can I help?", "Yes, do sit. Tell me what's been happening."]
NURSE_HANDOVER = [
    "Doctor, your next patient is here. I've done the basics, I'll read them out in a moment.",
    "Okay, doctor, we're all set in here. I'll give you the numbers when you want them.",
    "Doctor, this one's ready for you. Everything's on the chart, but I'll go through it.",
    "Morning, doctor. I've settled them in, ready when you are.",
]
D_AFTER_NURSE = ["Thanks. Hello, come in, sit down. What brings you in today?", "Thank you. Good morning, tell me what's been going on.",
                 "Perfect, thanks. Hello there, so what's the trouble?", "Okay, thanks. Hi, how can I help today?"]
CARE_ENTER = ["Doctor, thank you for seeing us.", "Good morning, doctor. I came along to help out.",
              "Hello, doctor. I hope it's alright if I stay in for this.", "Doctor, I'm just here to help with the details."]
D_TO_CARE = ["Of course, please stay. It's helpful to have you here.", "That's fine, sit down. We'll go through it together.",
             "Yes, that's no problem at all. Please sit."]

CC_T = [
    "It's {cc}, mostly.", "Well, I've been having {cc}.", "Um, so... {cc}. That's why I came.",
    "Doctor, it's {cc}. It's getting on my nerves now.", "I wanted to get {cc} looked at.",
    "Honestly, it's {cc}, and my family pushed me to come.", "It's {cc}. I thought I'd wait, but it hasn't gone.",
    "So the thing is, I've got {cc}.", "Mainly {cc}. There's a couple of other things, but that's the main one.",
    "I've been dealing with {cc}.", "I'm here because of {cc}.", "Yeah, it's {cc}. I don't know what's causing it.",
]
CC_THIRD = [
    "{He}'s been having {cc}, doctor.", "Doctor, it's {cc}. That's what we're worried about.",
    "It's {cc}, doctor. {He} didn't want to come, but I insisted.", "We came because of {cc}.",
]

DUR_T = ["It's been {d} now.", "I've had it for {d}.", "For {d}, I'd say.", "About... well, {d}.",
         "It's been {d}, I'm fairly sure.", "Probably {d}. Yeah.", "It's been going on for {d}."]
ONSET_T = ["I've had it {o}.", "It's been like this {o}.", "Ever since... {o}, really.", "{O}, that's when it began."]
ONSET_Y = ["It started yesterday.", "Yesterday, it came on out of nowhere.", "Just since yesterday."]
D_HOWLONG = ["How long has this been going on?", "And when did that start?", "How long have you had it?",
             "When did you first notice it?", "Is this recent, or has it been a while?"]
D_SEV = ["How bad is it, would you say?", "And how severe is it?", "How would you describe it, mild, moderate, severe?",
         "How much is it bothering you?", "On a normal day, how strong is it?"]
SEV_T = ["It's {s}, honestly.", "I'd say {s}.", "Pretty {s}, if I'm being honest.", "{S}, I'd say."]
SEV_NUM_T = ["About a {n} out of ten.", "I'd give it a {n}, out of ten.", "Maybe a {n} out of ten on a bad day.", "A {n} out of ten, I suppose."]
D_FREQ = ["Is it constant, or does it come and go?", "How often does it happen?", "Does it happen all the time or in spells?",
          "What's the pattern, is it there all day?"]
FREQ_T = ["It's {f}.", "It happens {f}.", "I'd say {f}.", "Honestly, {f}."]
FREQ_V = ["It {f}.", "It just {f}.", "It sort of {f}."]
D_AGGR = ["Does anything bring it on or make it worse?", "Is there anything that triggers it?", "What makes it worse, if anything?",
          "Do you notice anything setting it off?"]
AGGR_T = ["It's worse with {a}.", "I notice it more with {a}.", "{A} definitely sets it off.", "Yes, {a}. That makes it worse."]
D_RELIEF = ["Anything that helps?", "Does anything make it better?", "Have you found anything that eases it?",
            "And what do you do to cope with it?"]
RELIEF_T = ["I get some relief from {r}.", "It settles a little with {r}.", "{R} helps a bit.", "Only {r}, and it's not much."]
D_ALSO = ["Have you had {p}?", "Any {p} as well?", "What about {p}, have you noticed that?", "Has there been {p} too?"]
P_YES = ["Yes, I have.", "Yeah, that too.", "Yes, actually.", "Mm, yes."]
P_ALSO = ["I've also had {p}, for {d}.", "And there's {p} as well, {d} now.", "Oh, and {p}. That's been about the same, {d}.",
          "I've had {p} too, for {d}."]
P_ALSO_ON = ["I've also had {p}, {o}.", "And {p} as well, {o}.", "Oh, and {p}. Had that {o}."]
P_ALSO_BARE = ["I've also had {p}.", "There's {p} as well.", "And {p}, too.", "Oh, and {p}."]
ASSOC_T = ["It usually comes with {q}.", "When it starts I tend to get {q} as well.", "{Q} goes along with it, most of the time."]
D_ASSOC = ["Does it come along with anything else?", "Anything that tends to go along with it?"]
D_BACKCH = ["Mm-hm.", "Okay.", "I see.", "Right.", "Go on.", "Okay, I'm following.", "Alright.", "Mm."]
P_RESOLVED = ["I did have {p} at one point, but that's gone now.", "There was {p}, yes, but that went away.",
              "I had {p} before. That's settled now, though.", "{P} was there, but it's gone away on its own."]
P_PREV = ["Yes, something like this happened {w}, and it went away on its own.", "A bit, {w}. It settled by itself back then.",
          "I had a similar thing {w}. It went away."]
D_PREV = ["Has this happened before?", "Have you had anything like this in the past?", "Is this the first time, or has it come before?"]
P_DATE_UNC = ["Honestly I can't say exactly when it started. It might have been last month or the month before, I really can't pin it down.",
              "Hm. It was either the end of last month or earlier than that. I couldn't tell you the date.",
              "I'm not sure when it began, to be honest. Some weeks ago, but I can't say how many."]

NEG_Q1 = ["Any {a}?", "Have you had any {a}?", "What about {a}?", "Has there been any {a}?", "And {a}, any of that?"]
NEG_QN = ["Any {l}?", "Have you had any {l}?", "Let me check a few things. Any {l}?", "Any {l} at all?"]
NEG_A1 = ["No, no {a}.", "No, I haven't had any {a}.", "No {a}, thank goodness.", "No. No {a}.", "Not at all, no {a}."]
NEG_AN = ["No, none of those.", "No, none of that at all.", "No. None of those, no.", "Nothing like that, no."]
NEG_ANS = ["No, no {l}.", "No {l}, none of it.", "I haven't had {l}, no."]

ROS_POOL = [  # (system, category key, question, answers)
    ("gastrointestinal", "gastrointestinal", "What about your tummy and bowels, anything unusual there?", ["No, all normal there.", "Nothing unusual, no."]),
    ("genitourinary", "genitourinary", "Anything unusual with passing urine?", ["No, that's all fine.", "Nothing there, no."]),
    ("cardiovascular", "cardiovascular", "How about your heart, any problems like that?", ["No, nothing with my heart.", "No, that's been fine."]),
    ("respiratory", "respiratory", "Your breathing, any trouble there?", ["No, my breathing's been fine.", "No problems with breathing."]),
    ("neurological", "neurological", "Anything with your nerves, like weakness or numbness?", ["No, nothing like that.", "No, that's all normal."]),
    ("skin", "dermatological", "And your skin, any changes there?", ["No, skin's been fine.", "Nothing on the skin, no."]),
    ("musculoskeletal", "musculoskeletal", "Any problems with your joints or muscles?", ["No, nothing there.", "No, joints are fine."]),
]

D_PMH = ["Do you have any medical conditions, anything you've been treated for?", "Any long-term health problems I should know about?",
         "What about your general health, any conditions you're being treated for?", "Moving on to your background, any past medical history?"]
P_PMH1 = ["I have {c}.", "I've got {c}.", "Yes, {c}.", "I've had {c}, yes."]
P_PMH_DUR = ["I have {c}, for {d}.", "I've had {c} for {d} now.", "{C}, for {d}."]
D_PMH_NONE = ["No other medical conditions?", "Nothing else in the background?"]
P_PMH_NONE = ["No, nothing, I've generally been healthy.", "No, none that I know of.", "No, I've never had anything serious."]
D_SURG = ["Any operations in the past?", "Have you had any surgery before?", "Any previous surgeries?", "What about operations, anything like that?"]
P_SURG = ["Yes, I had {s}, {t}.", "I had {s} {t}.", "Just {s}, {t}."]
P_SURG_NONE = ["No, never had any surgery.", "No operations, no.", "No, nothing like that."]
D_FAM = ["Does anything run in the family?", "What about family history, any illnesses that run in the family?", "Anyone in the family with similar problems or other conditions?"]
P_FAM_NONE = ["Not that I know of.", "No, nothing I'm aware of."]
D_SOC = ["Do you smoke?", "How about smoking?", "Any smoking?", "What about alcohol?", "Do you drink alcohol?", "And alcohol, how much?"]
D_MEDS = ["What medicines are you taking at the moment?", "Are you on any tablets or medication?", "What medicines do you take regularly?",
          "Any medication at the moment, including things from the pharmacy?", "Let's go through your medication. What are you taking?"]
D_MEDS_NONE = ["Any regular medication?", "Are you on any regular medication?"]
P_MEDS_NONE = ["No, nothing regular.", "No, I don't take anything regularly.", "Nothing, no."]
D_DOSE = ["Do you know the dose?", "And what strength is that?", "How much do you take?"]
D_FREQM = ["And how often do you take it?", "How often is that?"]
D_ALLERGY = ["Do you have any allergies to medicines, food, anything at all?", "Any allergies I should know about?",
             "Do you have any known allergies at all?", "What about allergies, to medicines or foods or anything else?"]
P_ALLERGY = ["Yes, {s}. I get {r}.", "I'm allergic to {s}, I get {r}.", "{S}. I come out in... well, {r}.", "Yes, {s}, it gives me {r}."]
P_ALLERGY_NR = ["Yes, I'm allergic to {s}.", "Yes, {s}.", "{S}, I'd say."]
P_NKA = ["No, none that I know of.", "No allergies.", "No, nothing I'm aware of.", "Not that I know, no."]
D_ALLERGY_FU = ["Do you remember what happened?", "What kind of reaction was it?"]
P_ALLERGY_UNC = ["I think I reacted to some {s} once, years ago. I don't remember which one, or what happened exactly.",
                 "Hmm, there was some {s}, I was told I was allergic. But I couldn't tell you what it was called or what it did."]

D_VIT_START = ["Let me check your vitals now.", "I'll take a few measurements first.", "Let's get your blood pressure and the other basics."]
D_VIT_READ = ["Okay, give me a moment...", "Hold still for me...", "Just relax your arm..."]
N_VIT_INTRO = ["Doctor, I've got the readings for you.", "Okay, so the vitals from earlier.", "Here are the numbers, doctor."]

D_EXAM_INTRO = ["Alright, I'd like to examine you now. Please come over here.", "Let me have a look at you now.",
                "Okay, let's do a quick examination.", "I'll examine you now, so please bear with me.", "Can I examine you now?"]
P_OK = ["Okay.", "Alright.", "Sure.", "Hm.", "Okay, go ahead.", "Yes, doctor."]
D_EXAM_DONE = ["Okay, you can sit back up.", "That's fine, you can get dressed.", "All done, thank you, please sit down."]

ASSESS_INTRO = ["From what you've told me and what I found,", "Putting it all together,", "So, based on the history and the examination,",
                "Right, here's what I'm thinking.", "Okay, so my impression is this:"]
ASSESS_PRIM = ["this looks most like {a}.", "it fits best with {a}.", "I think we're dealing with {a} at this stage.", "my working impression is {a}."]
ASSESS_DIFF = ["I'd also keep {d} in mind.", "It could also be {d}, so we'll keep that open.", "I can't rule out {d} yet.", "{D} is also on my list."]
ASSESS_DIFF_N = ["I'd also keep {d} in mind.", "We can't rule out {d} yet.", "It could also be {d}."]
CONCERN_Q = ["Is it something serious, doctor?", "Should I be worried about this?", "Is this going to go away?",
             "Doctor, is this dangerous?", "I've been thinking the worst, to be honest. Is it bad?"]
CONCERN_A = ["I understand the worry. At the moment I'd say it's {a}, and we'll know more once the {i} is back.",
             "Nothing I've seen today points to an emergency. It looks like {a}, but I'd like to confirm.",
             "I can't promise yet, but most people with {a} do well once it's treated properly.",
             "It's reasonable to be concerned, but right now {a} is my leading thought, not anything worse."]
CONCERN_A_NOINV = ["I understand the worry. At the moment I'd say it's {a}, and we'll watch how it goes.",
                   "Nothing I've seen today points to an emergency. It looks like {a}."]
D_INV = ["I'd like to arrange {n} for {i}.", "I'm going to order {n}, for {i}.", "We should do {n} for {i}.", "Let's get {n}, for {i}."]
P_INV_OK = ["Okay, that's fine.", "Alright. When can I do that?", "Sure, where do I go for that?", "Okay, doctor."]
S_APPT = ["We have a slot {w} at {t}, if that works.", "I can book that for {w} at {t}.", "The earliest is {w}, {t}."]
P_APPT = ["That's fine.", "Okay, I'll be there.", "{W}, that works for me."]
N_DONE = ["Doctor, I did {n} before they came in, the result's on your screen.", "I've already done {n}, it's ready for you.",
          "We've already done {n} this morning, doctor."]
D_DONE_ACK = ["Good, thank you.", "Okay, thanks, I'll look at that.", "Perfect."]
P_PREV_INV = ["I had {n} done at another clinic {w}. I don't have the report with me.", "I did have {n} done {w}, but the paper's at home."]
D_PREV_INV = ["Have you had any tests for this so far?", "Any scans or blood work done already?"]
D_RX = ["I'll start you on {n}, {d}{f}{u}.", "Let's use {n}, {d}{f}{u}.", "I'd like you to take {n}, {d}{f}{u}.", "I'm prescribing {n}, {d}{f}{u}."]
D_RX_IND = [" That's for {i}.", " It's for {i}.", " That should help with {i}."]
P_RX_OK = ["Okay, and I take that after food?", "Alright, I'll pick it up today.", "Okay, doctor.", "Right, I'll remember that."]
D_REFER = ["I'll also refer you to {r}.", "I'd like you to see {r} as well, and I'll write the referral.", "We'll refer you to {r}."]
D_FU = ["Come back {t}.", "I'd like to see you again {t}.", "Let's review you {t}.", "Please come and see me {t}."]
P_FU_OK = ["Okay, I'll book that.", "Sure, I'll make the appointment on the way out.", "Alright."]
D_RED = ["Please, {s}"]
P_UNDERSTOOD = ["Understood.", "Yes, I'll do that.", "Okay, I understand.", "Got it, thank you."]

CLOSE_D = ["Take care, and don't hesitate to call if anything changes.", "Alright, that's everything from me. Any other questions?",
           "I think we've covered it. Do you have any questions?", "Good. Look after yourself.",
           "Right, that's all I have. Is there anything you wanted to ask?", "Okay, we're done for today. Take care."]
CLOSE_P = ["No, I think that's everything. Thank you, doctor.", "Thanks so much, doctor.", "No questions. Thank you.",
           "That's all, thank you for your time.", "Thank you. I'll see you then.", "Alright, thanks. Bye for now.",
           "No, you've explained it well. Thanks."]
CLOSE_D2 = ["Take care.", "See you then.", "Bye for now, look after yourself.", "Alright, goodbye."]

RAPPORT = [
    ("Did you find the place alright?", "Yes, it was easy enough. The parking was the hard part."),
    ("Sorry about the wait, we're running a bit behind.", "Oh, that's fine. I was just reading something on my phone."),
    ("Busy day out there?", "Always is. The traffic coming in was terrible."),
    ("Have you been here before?", "A couple of times, but not recently."),
    ("Did you come far?", "Not too far, about half an hour by bus."),
    ("Is this your first time with this clinic?", "Mm, first time with this one, yes. A friend recommended it."),
    ("Weather's turned, hasn't it?", "It has. I got caught in the rain walking over."),
    ("You came on your own today?", "Yes, I managed on my own."),
]
CONTEXT_CHAT = [
    ("How's everything else at home otherwise?", "Busy. Everyone's running in different directions at the moment, you know how it is."),
    ("Sorry, I'm just writing a few notes, bear with me.", "No problem, take your time."),
    ("Is it okay if I type while we talk?", "Yes, of course, go ahead."),
    ("Do you need me to explain anything as we go?", "Just tell me in plain language, please. I'm not good with the medical terms."),
    ("Is there anything you were hoping to get out of today's visit?", "Mostly I just want to understand what's going on."),
    ("Are you comfortable? Do you want some water?", "Yes, some water would be nice, thank you."),
    ("Let me know if I'm going too fast.", "No, you're fine."),
]
RECORDS_CHECK = [
    ("Let me just pull up your file for a second.", "Sure."),
    ("One moment, the system's being slow today.", "That's alright."),
    ("Give me a second, I'm just scrolling back through your chart.", "Of course."),
    ("Let me make a quick note of that before I forget.", "Okay."),
]

P_ELAB = [
    "I wasn't sure whether to come in at all, to be honest.", "My family kept telling me to get it checked.",
    "I thought it would sort itself out, but it hasn't.", "I didn't want to make a fuss, you know.",
    "I looked a few things up online, and that probably didn't help.", "I'd rather know what's going on than keep guessing.",
    "I took the morning off to come in today.", "A neighbour of mine said I should see someone about it.",
    "I've never really been one for hospitals.", "I'm hoping you can tell me something definite.",
    "I kept putting it off, which I know isn't sensible.", "I just want to get back to normal, really.",
    "Sorry, I know I'm rambling a bit.", "It's the not knowing that gets to me.", "I did try to ignore it for a while.",
    "I'm not great at remembering details, so bear with me.", "It's a relief to finally sit down and talk about it.",
    "I told myself I'd wait and see, and here I am.", "My sister suggested writing things down, but I forgot.",
    "I'd rather not end up on lots of tablets if I can avoid it.",
]
D_ELAB = [
    "I ask because it helps me narrow things down.", "Bear with me, I'm just building up the picture.",
    "These questions might sound routine, but they matter.", "Take your time, there's no rush.",
    "I'll explain everything as we go along.", "It helps to be thorough at this stage.",
    "Just so I get the full picture.", "I'm asking so that we don't miss anything.",
]
INV_EL = [
    "That will help us see what's going on underneath and decide the next step.", "It's a routine test and it'll give us a much clearer picture.",
    "I'd rather check than guess, and this is the quickest way to know more.", "The result will help us decide whether anything more is needed.",
]
RX_EL = [
    "It's a commonly used medicine and most people tolerate it well.", "I'll put all of this in writing so you don't have to remember it.",
    "The pharmacy will go through the details again when you pick it up.",
]
ASSESS_EL = [
    "The reason I say that is that your story and my examination fit together.", "That's my thinking for now, and it may change as we learn more.",
    "I want to be honest that this is an impression, not a final answer.",
]

EXPLAIN = [
    "Let me explain how I'm thinking about this. When someone has symptoms like these, we first look for the common and treatable causes, and only then for the rarer ones. That's why I'm going step by step rather than ordering everything at once.",
    "I'll be straight with you about how this works. Most of what we see in clinic turns out to be manageable, and the history you give me is often more useful than any single test, so thank you for being so detailed.",
    "What I'm doing here is putting together three things: what you tell me, what I find when I examine you, and what the tests show. None of those alone is enough, which is why we sometimes need to wait for results before being certain.",
    "It's quite normal to feel unsure at this point. People often expect an instant answer, but a good assessment usually has a few stages, and today is mainly about narrowing things down and making a sensible plan together.",
    "I like to make sure you understand what's happening, so please stop me at any point. There are no silly questions, and I'd much rather you ask now than go home still wondering about something.",
    "Just so you know how the rest of the visit will go: I'll finish my notes, we'll agree on the plan, and the front desk will help with anything that needs booking. You shouldn't need to chase anything yourself.",
]
LIFE = [
    ("Has anything about your daily routine changed lately?", "Not really, the days are pretty much the same, work and home, and I've been trying to fit appointments in around my schedule, which isn't always easy, so I'm glad we could find a time today."),
    ("Is there anyone at home who can help you out if you need it?", "Yes, there's family around most evenings, and they've been very good about checking in, although they do worry more than they need to."),
    ("Do you have everything you need to get home alright?", "Yes, I've got my transport sorted. It's a bit of a trek, but I'm used to the journey by now, and I brought something to read for the wait."),
    ("Have you been able to keep up with your usual activities?", "For the most part, yes. I just carry on and try not to dwell on things too much, though I won't pretend it hasn't crossed my mind a few times."),
    ("Do you have any questions before we carry on?", "Not at the moment, I think you've covered most of what I was wondering. If something comes to mind later, I'll ask you before I leave."),
]
EXAM_EXPLAIN = [
    "Thank you for that. I'll write up what I found in a moment, and then I'll tell you what I think is going on.",
    "Good, that's all I need to examine. Let me gather my thoughts and then we'll talk it through together.",
    "Thanks for bearing with me. Now that I've had a look, I can put the whole picture together.",
]

ASSESS_INTRO_NOEXAM = ["From what you've told me,", "Putting together what you've described,", "So, based on your history,",
                       "Right, here's what I'm thinking.", "Okay, so my impression from what you've said is this:"]
ASSESS_EL_NOEXAM = [
    "The reason I say that is that the way you describe it fits together.", "That's my thinking for now, and it may change as we learn more.",
    "I want to be honest that this is an impression, not a final answer.",
]

EXPLAIN_R = ["Okay, that makes sense.", "Thank you, that really helps.", "I appreciate you explaining that.", "That's reassuring to hear.",
             "Right, I understand now.", "Good, I was wondering how this would go."]

# ---- widened pools (override earlier, smaller lists)
P_FIRST = ["Good morning, doctor. Can I come in?", "Hello doctor, sorry, am I early?", "Hi, doctor. Is this the right room?",
           "Afternoon, doctor.", "Excuse me, doctor, should I sit here?", "Hello? Doctor? They told me to come straight in.",
           "Morning, doctor, I hope I'm not interrupting.", "Hi doctor, sorry, the lift was out and I had to take the stairs.",
           "Doctor, hello, I've got my papers here, where should I put them?", "Good evening, doctor, thank you for staying late.",
           "Sorry I'm a few minutes behind, doctor.", "Hi there, is it alright if I come in now?", "Hello, doctor. It's my turn, I think.",
           "Good afternoon, doctor, the receptionist said you'd see me now.", "Hi, doctor, I brought my bag, is it fine to leave it here?",
           "Morning. Nice to finally see you, doctor.", "Doctor? Hi. I hope I've got the right time.", "Hello, doctor. Where would you like me?",
           "Sorry, doctor, I couldn't find the door at first.", "Hi, doctor. Long queue outside, but here I am."]
D_AFTER_PFIRST = ["Yes, come in, take a seat. What can I do for you today?", "You're fine, sit down. So, what brings you in?",
                  "Right on time. Sit, please. How can I help?", "Yes, do sit. Tell me what's been happening.",
                  "No trouble at all, come in. What's been bothering you?", "That's alright, take a seat. Tell me why you've come.",
                  "Of course, put it down anywhere. So, how can I help?", "Not at all, please sit. What's the problem?"]
NURSE_HANDOVER = [
    "Doctor, your next patient is here. I've done the basics, I'll read them out in a moment.",
    "Okay, doctor, we're all set in here. I'll give you the numbers when you want them.",
    "Doctor, this one's ready for you. Everything's on the chart, but I'll go through it.",
    "Morning, doctor. I've settled them in, ready when you are.", "Doctor, we're ready in room two, I've already taken the observations.",
    "Doctor, I've checked them in and done the preliminary measurements, I'll hand them over when you ask.",
    "All set here, doctor. Chart's updated, and I'll read the readings out when you're ready.",
    "Doctor, the patient's with us now. I did the usual checks at the front, so just say when you want them.",
    "Afternoon, doctor. They're in and comfortable, and I have the measurements ready.", "Doctor, if you're free, we can start. I've got the numbers noted down.",
    "Ready for you, doctor. I'll stay in case you need anything.", "Doctor, I've brought them through. The observations are done, whenever you need them.",
]
D_AFTER_NURSE = ["Thanks. Hello, come in, sit down. What brings you in today?", "Thank you. Good morning, tell me what's been going on.",
                 "Perfect, thanks. Hello there, so what's the trouble?", "Okay, thanks. Hi, how can I help today?",
                 "Thanks, that's helpful. Hello, please sit. What's been happening?", "Good, thank you. Welcome, tell me what's brought you in.",
                 "Great. Hello, come in and sit down. How can I help?", "Thank you. Right, hello, what's the problem?"]
CARE_ENTER = ["Doctor, thank you for seeing us.", "Good morning, doctor. I came along to help out.",
              "Hello, doctor. I hope it's alright if I stay in for this.", "Doctor, I'm just here to help with the details.",
              "Hello, doctor, I came in with them, if that's okay.", "Morning, doctor. I'll stay and fill in anything that's missed.",
              "Doctor, I've come along because I know the history, if it helps.", "Thank you for fitting us in, doctor."]
D_TO_CARE = ["Of course, please stay. It's helpful to have you here.", "That's fine, sit down. We'll go through it together.",
             "Yes, that's no problem at all. Please sit.", "Please do. Extra information is always welcome.",
             "Absolutely, come and sit beside them.", "Good, that'll be useful. Pull up a chair."]
TEACH_Q = ["Just so I know I've explained it clearly, can you tell me the plan back in your own words?",
           "Before we finish, can you repeat the plan back to me so I know I haven't been confusing?",
           "Let me check that I've been clear. What will you do once you get home?",
           "Can you run through the plan with me quickly, just to be certain?",
           "I want to be sure we're on the same page. How would you describe the plan?",
           "Tell me what you've taken from all that, so I can fill in any gaps.",
           "Okay, summarise it for me, what's the plan from your side?", "Just to confirm, what are the next steps as you understand them?"]
EXAM_STEPS = ["Let me press here.", "Take a breath for me.", "Now I'm going to check this part.", "Bear with me a second.",
              "Can you lie back for me?", "Breathe in deeply... and out.", "Tell me if anything hurts as I press.",
              "I'll just listen to your chest now.", "Look straight ahead for me.", "Open wide for me.", "Hold your arm out like this.",
              "Now bend it for me, slowly.", "Let me check your reflexes.", "A little pressure here, tell me if it's tender.", "Stay still while I have a look.",
              "Turn your head to the side for me.", "Just relax, I'll be quick."]
D_RXQ = ["Hm. Do you have the latest prescription with you?", "I see. Is the most recent prescription on you?",
         "Okay. Have you got the newest prescription or the box with you?", "Right. Do you happen to have the current prescription here?",
         "Hm, that's different. Is the latest prescription anywhere near you?", "Alright. Did you bring the up-to-date prescription?"]
D_PACKET = ["Do you have the packet or the prescription with you?", "Have you got the box or the prescription on you?",
            "Is the packet here, or the prescription?", "Did you happen to bring the box or the paperwork?"]
HOLD_A = ["Give me a second, I'm just typing this up.", "Let me just write this down properly.", "One moment, I'm updating your notes.",
          "Bear with me, I need to finish this line in the notes.", "I'm just saving what we've covered so far.", "Hold on, the screen's frozen for a second."]
HOLD_B = ["Okay, that's done.", "Right, carry on.", "Good, where were we.", "Alright, back to you.", "That's saved, thanks for waiting.", "Okay, continuing."]
RECORDS_CHECK = [
    ("Let me just pull up your file for a second.", "Sure."), ("One moment, the system's being slow today.", "That's alright."),
    ("Give me a second, I'm just scrolling back through your chart.", "Of course."), ("Let me make a quick note of that before I forget.", "Okay."),
    ("I want to open your previous notes quickly.", "Go ahead."), ("Sorry, the computer needs a moment to load this.", "No rush."),
    ("I'll just check what's already recorded here.", "Please do."), ("Let me double-check something in your record.", "Of course, take your time."),
]
CONTEXT_CHAT = CONTEXT_CHAT + [
    ("Is the room warm enough for you?", "It's perfect, thank you."), ("Sorry about the noise outside, the building work never stops.", "I hadn't even noticed, honestly."),
    ("Did you manage to eat before coming?", "Yes, I had something small this morning."), ("I'll try to keep this as efficient as I can.", "Thank you, I appreciate it."),
    ("Is it all right if a trainee sits in later? No? Fine.", "I'd rather not, if you don't mind."),
]
RAPPORT = RAPPORT + [
    ("Was parking alright?", "Not great, I ended up a few streets away."), ("Did the receptionist sort you out quickly?", "Yes, she was lovely about it."),
    ("Lovely day outside, isn't it?", "It is, I almost forgot I was coming here."), ("Have you been waiting long?", "Only about ten minutes, no trouble."),
    ("Did you take the bus in?", "I drove. The roads were quiet today."), ("Is the form from the front desk all filled in?", "I think so, I handed it in at the counter."),
]
CLOSE_D = ["Take care, and don't hesitate to call if anything changes.", "Alright, that's everything from me. Any other questions?",
           "I think we've covered it. Do you have any questions?", "Good. Look after yourself.",
           "Right, that's all I have. Is there anything you wanted to ask?", "Okay, we're done for today. Take care.",
           "That's everything on my side. Anything you're unsure about?", "Wonderful, I think that's it. Ask me anything before you go.",
           "We're all set. Don't leave without asking if something's unclear.", "Good. Call the clinic if you need us in the meantime.",
           "All right, I'll let you go. Any final questions first?", "Okay, I think we're finished. Is everything clear?"]
CLOSE_P = ["No, I think that's everything. Thank you, doctor.", "Thanks so much, doctor.", "No questions. Thank you.",
           "That's all, thank you for your time.", "Thank you. I'll see you then.", "Alright, thanks. Bye for now.",
           "No, you've explained it well. Thanks.", "I think that's clear. Thank you for being so thorough.", "Nothing more from me, doctor, thanks.",
           "That's everything I wanted to ask. Thank you.", "I appreciate your time, doctor.", "Okay, thank you. I'll get started on all of that."]

from dialogue_pools2 import *  # noqa: E402,F401,F403  (corrected-build overrides)
