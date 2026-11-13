"""Widened phrase pools for the corrected build.  Imported AFTER dialogue_pools; every name defined here overrides the
older, smaller list.  Each encounter only ever sees a random ~45% subset of any pool (see Enc.r), which keeps wording
coherent inside an encounter while reducing dataset-wide repetition."""

D_BACKCH = ["Mm-hm.", "Right.", "I see.", "Go on.", "Okay.", "Mm.", "Yes?", "And then?", "Uh-huh.", "Ah.", "Hm, okay.", "I follow.",
            "Right, right.", "Sure.", "Okay, so.", "Mhm.", "Understood.", "Okay, keep going."]
P_OK = ["Okay.", "Sure.", "Fine.", "Yes, doctor.", "Alright.", "That's fine.", "Go ahead.", "Mm, okay.", "No problem.", "Okay, ready."]
P_INV_OK = ["Okay, that's fine.", "Where do I go for that?", "Is that done here?", "Will it hurt?", "Alright, when would that be?", "Fine by me.",
            "How long does that take?", "Okay, noted.", "That sounds sensible.", "Does it need any preparation?", "Mm, okay."]
P_RX_OK = ["Okay, and I take that after food?", "Alright, I'll collect it today.", "Is that safe with my other things?", "Right, understood.",
           "Can I get that from the usual pharmacy?", "Mm, okay.", "That's easy enough to remember.", "Okay, thank you.", "Fine, I'll start it.",
           "How long until it works?", "Should I keep taking it if I feel better?"]
P_UNDERSTOOD = ["Understood.", "Yes, I'll keep that in mind.", "Okay, I understand.", "Got it, thank you.", "That's clear.", "Yes, I'll watch for that.",
                "Alright, I know what to look for.", "Okay, I'll remember.", "Right, will do.", "Okay, fair enough."]
P_FU_OK = ["Okay, I'll book that.", "I'll make the appointment on my way out.", "Fine.", "That works for me.", "Alright, I'll put it in my diary.",
           "Okay, see you then.", "Sure, that's doable.", "Good, I'll come back then.", "Yes, I can do that.", "Okay."]
D_DONE_ACK = ["Good, thank you.", "Thanks, I'll look at that.", "Perfect.", "Great, that saves time.", "Thanks, I'll check it.", "Okay, noted."]
D_EXAM_INTRO = ["I'd like to examine you now.", "Let me have a look at you.", "Okay, a quick examination now.", "Can I examine you now?",
                "Shall we do the examination?", "Right, let me check a few things physically.", "I'll examine you now, bear with me.",
                "If you're comfortable, I'll examine you now.", "Let's do the physical part now.", "Come over here and I'll have a look.",
                "Okay, I need to examine you for this.", "Let me examine, it won't take long."]
D_EXAM_DONE = ["Okay, you can sit up.", "That's all I need, thank you.", "All done, you can get dressed.", "Thanks, please take a seat again.",
               "Good, that's the examination.", "Right, you can sit back down.", "Okay, finished.", "Thanks for that.", "That's fine, sit up."]
D_VIT_START = ["Let me check your vitals now.", "I'll take a few measurements first.", "Let's get your blood pressure and the other basics.",
               "I'll check your pressure and pulse.", "Before we go on, a few quick readings.", "Let me measure a few things."]
D_VIT_READ = ["Okay, give me a moment...", "Hold still for me...", "Just relax your arm...", "Rest your hand here...", "Almost there...", "One second..."]
D_REFER = ["I'll also refer you to {r}.", "I'd like you to see {r} as well, and I'll write the referral.", "We'll refer you to {r}.",
           "I'm going to send a referral to {r}.", "I think {r} should see you too.", "Let's get you seen by {r}, I'll arrange the letter.",
           "{R} would be the right next step, I'll refer you."]
INV_T = ["I'd like to arrange {n} for {i}.", "I'm going to order {n}, for {i}.", "We should do {n} for {i}.", "Let's get {n}, for {i}.",
         "I want {n} done, that's for {i}.", "I'll request {n}, it'll help with {i}.", "Let's book {n} to look into {i}.",
         "{N} is what I'd like next, for {i}.", "I'm sending you for {n} because of {i}.", "I think {n} makes sense here, for {i}."]
RX_T = ["I'll start you on {n}{r}.", "Let's use {n}{r}.", "I'd like you to take {n}{r}.", "I'm prescribing {n}{r}.",
        "We'll begin with {n}{r}.", "You'll be taking {n}{r}.", "What I'm giving you is {n}{r}.", "The treatment will be {n}{r}.",
        "I'm going to put you on {n}{r}.", "For this, {n}{r}."]
FU_T = ["Come back {t}.", "I'd like to see you again {t}.", "Let's review you {t}.", "Please come and see me {t}.",
        "We'll catch up {t}.", "I'd like you back {t}.", "Book a review {t}.", "See me again {t}.", "Let's plan a check {t}.",
        "I'll want another look {t}."]
SAFETY_T = ["If {red}, or you feel really unwell, please come to the emergency department.", "Come back or go to emergency straight away if {red}.",
            "Please don't wait if {red}. That's when to be seen urgently.", "Keep an eye out, and if {red}, call us the same day or go to emergency.",
            "The thing that would worry me is if {red}. If that happens, go to emergency.", "Do get help quickly if {red}.",
            "If {red}, that's the point to come in urgently.", "One warning sign to remember: {red}. In that case don't wait."]
COND_INV_T = ["If it hasn't settled {when}, we'd think about {n}, but not now.", "I'm not ordering {n} today. If things carry on {when}, we'll consider it.",
              "Let's hold off on {n} for now, and if there's no change {when} we can revisit it.",
              "{N} is something we might do if this doesn't improve {when}."]
DECLINE_Q = ["Could I get {n} done? A friend had it.", "Should I have {n} as well?", "Do I need {n}? I read it might help.",
             "Can you send me for {n}?"]
DECLINE_A = ["I don't think that's needed at this stage, the history doesn't call for it.", "Not right now, it wouldn't change what we do today.",
             "I wouldn't order it today. If anything changes, we'll reconsider.", "Not at this point, no. It isn't indicated yet."]
NONE_PLAN = ["There's nothing new for me to start or arrange today.", "I don't need to add any tests or treatment at this point.",
             "For now, no new medicines or tests are needed.", "Today I'm not changing anything."]
ASSESS_INTRO = ["From what you've told me and what I found,", "Putting it all together,", "So, based on the history and the examination,",
                "Right, here's what I'm thinking.", "Okay, so my impression is this:", "Having listened and examined,", "Taking everything into account,",
                "Let me tell you where I've got to.", "Okay, thinking it through,", "So where does that leave us?"]
ASSESS_INTRO_NOEXAM = ["From what you've told me,", "Putting together what you've described,", "So, based on your history,",
                       "Right, here's what I'm thinking.", "Okay, so my impression from what you've said is this:", "Listening to the whole story,",
                       "Going by what you've described,", "Let me tell you where I've got to."]
ASSESS_PRIM = ["this looks most like {a}.", "it fits best with {a}.", "I think we're dealing with {a} at this stage.", "my working impression is {a}.",
               "the most likely explanation is {a}.", "it points towards {a}.", "I'd lean towards {a}.", "this is probably {a}."]
ASSESS_DIFF = ["I'd also keep {d} in mind.", "It could also be {d}, so we'll keep that open.", "I can't rule out {d} yet.", "{D} is also on my list.",
               "{D} is still possible.", "We shouldn't forget {d}.", "Another possibility is {d}."]
ASSESS_UNCERTAIN = ["I'm honestly not certain yet. It could be {a}, or it might be {d}.", "I don't have a clear answer today: {a} is possible, and so is {d}.",
                    "It's hard to say. {A} is one possibility and {d} another, and I'd rather not commit yet.",
                    "I can't pin this down yet. We're looking at {a} or {d}."]
CONCERN_Q = ["Is it something serious, doctor?", "Should I be worried about this?", "Is this going to go away?", "Doctor, is this dangerous?",
             "I've been thinking the worst, to be honest. Is it bad?", "What are the chances it's something bad?", "Is this something I'll have for good?",
             "Do you think it's serious?"]
RECAP_T = ["Let me just check I've got this right.", "So, to recap quickly.", "Let me repeat that back to make sure.", "Just to be sure I understood.",
           "Stop me if I've got anything wrong."]
RECAP_R = ["Yes, that's right.", "That's it, yes.", "Exactly.", "Yes, you've got it.", "Correct.", "That's what happened, yes.", "Mm, that's right."]
TEACH_Q = ["Can you tell me the plan back in your own words, so I know I've explained it clearly?",
           "Before we finish, can you repeat the plan back to me?", "Let me check I've been clear. What will you do once you get home?",
           "Can you run through the plan with me quickly, just to be certain?", "How would you describe the plan, so we're on the same page?",
           "Tell me what you've taken from all that, so I can fill in any gaps.", "What are the next steps as you understand them?"]
CLOSE_D = ["Take care, and call us if anything changes.", "That's everything from me. Any other questions?", "Do you have any questions?",
           "Look after yourself.", "Is there anything you wanted to ask?", "Okay, we're done for today. Take care.", "That's it on my side. Anything unclear?",
           "Ask me anything before you go.", "Call the clinic if you need us.", "Any last questions?", "Okay, I think we're finished. Is everything clear?",
           "Right, that's all. Go gently.", "Good. Let us know how you get on.", "Thanks for coming in.", "Alright, I'll see you out."]
CLOSE_P = ["No, I think that's everything. Thank you, doctor.", "Thanks so much, doctor.", "No questions. Thank you.", "Thank you for your time.",
           "Alright, thanks. Bye for now.", "No, you've explained it well. Thanks.", "I think that's clear. Thank you for being so thorough.",
           "Nothing more from me, thanks.", "That's everything I wanted to ask. Thank you.", "I appreciate it, doctor.", "Okay, thank you. Bye.",
           "Thanks, that was helpful.", "One thing: no, actually that's all. Thanks.", "All good here. Thank you.", "Right. Thanks again."]
CLOSE_D2 = ["Take care.", "See you then.", "Bye for now.", "Goodbye.", "Mind how you go.", "Safe journey home.", "All the best."]
NEG_Q1 = ["Any {a}?", "Have you had any {a}?", "What about {a}?", "Has there been any {a}?", "And {a}, any of that?", "Did you notice any {a}?",
          "Any sign of {a}?", "How about {a}?", "Nothing like {a}?", "Have you had {a}, by any chance?"]
NEG_A1 = ["No, no {a}.", "No, I haven't had any {a}.", "No {a}, thankfully.", "No. No {a}.", "Not at all, no {a}.", "I haven't noticed any {a}.",
          "No, none, no {a}.", "Nope, no {a}.", "Not that I've noticed, no {a}.", "Definitely no {a}."]
NEG_AN = ["No, none of those.", "No, none of that at all.", "No. None of those.", "Nothing like that, no.", "No, not any of them.",
          "None, as far as I know.", "No, I'd have mentioned it.", "No, nothing there."]
NEG_QN = ["Any {l}?", "Have you had any {l}?", "Let me check a few things. Any {l}?", "Any {l} at all?", "Have you noticed {l}?",
          "Did you get {l}?", "And what about {l}?", "A few quick ones: {l}?"]
D_HOWLONG = ["How long has this been going on?", "And when did that start?", "How long have you had it?", "When did you first notice it?",
             "Is this recent, or has it been a while?", "When did it begin?", "Since when have you had this?", "How far back does it go?",
             "How long are we talking about?", "Roughly when did it start?"]
D_SEV = ["How bad is it, would you say?", "And how severe is it?", "How would you describe it, mild, moderate, severe?", "How much is it bothering you?",
         "On a normal day, how strong is it?", "Is it mild, moderate or severe?", "How intense does it get?", "Would you call it mild or bad?"]
SEV_T = ["It's {s}, honestly.", "I'd say {s}.", "Pretty {s}, if I'm being honest.", "{S}, I'd say.", "I'd call it {s}.", "It feels {s} to me.",
         "Mostly {s}.", "{S}, really."]
D_AGGR = ["Does anything bring it on or make it worse?", "Is there anything that triggers it?", "What makes it worse, if anything?",
          "Do you notice anything setting it off?", "Anything you do that brings it on?", "Is it worse with anything in particular?"]
D_RELIEF = ["Anything that helps?", "Does anything make it better?", "Have you found anything that eases it?", "And what do you do to cope with it?",
            "Does anything settle it?", "Is there anything that takes the edge off?"]
D_PMH = ["Do you have any medical conditions, anything you've been treated for?", "Any long-term health problems I should know about?",
         "What about your general health, any conditions you're being treated for?", "Moving on to your background, any past medical history?",
         "Tell me about your health in general, any ongoing conditions?", "Is there anything medical in your background?",
         "Any diagnoses you've been given before?", "Have you got any chronic problems?"]
D_SURG = ["Any operations in the past?", "Have you had any surgery before?", "Any previous surgeries?", "What about operations, anything like that?",
          "Have you ever been under the knife?", "Any procedures or operations?", "Any surgery in your history?", "Have you had to have anything operated on?"]
D_MEDS = ["What medicines are you taking at the moment?", "Are you on any tablets or medication?", "What medicines do you take regularly?",
          "Any medication at the moment, including things from the pharmacy?", "Let's go through your medication. What are you taking?",
          "Which tablets or creams or inhalers do you use?", "Tell me what you take day to day.", "What's your current medication list?"]
D_ALLERGY = ["Do you have any allergies to medicines, food, anything at all?", "Any allergies I should know about?", "Do you have any known allergies at all?",
             "What about allergies, to medicines or foods or anything else?", "Have you ever reacted badly to a medicine or food? Any allergies?",
             "Before I prescribe anything, any allergies?", "Any drug or food allergies?", "Are there any allergies on your record that I should check?"]
P_NKA = ["No, none that I know of.", "No allergies.", "No, nothing I'm aware of.", "Not that I know, no.", "I don't have any known medication allergies.",
         "No allergies that I know of, no.", "None, as far as I'm aware.", "I've never been told I have allergies.", "No, no allergies to anything."]
ELAB_RATE_SCALE = .35

EXAM_STEPS = ["Let me press here.", "Bear with me a second.", "Tell me if anything hurts.", "Stay still while I have a look.", "Just relax, I'll be quick.",
              "A little pressure here, tell me if it's tender.", "Hold that position for me.", "Let me just check something.", "Take your time, no rush.",
              "I'll go gently.", "Almost done with this part.", "Let me look at this properly."]


ROS_POOL = [  # (system, category key, questions, answers)
    ("gastrointestinal", "gastrointestinal", ["What about your tummy and bowels, anything unusual there?", "Any change in your bowel habit or your stomach generally?",
                                              "Is your digestion otherwise okay?", "How are your bowels, any trouble?"],
     ["No, all normal there.", "Nothing unusual, no.", "No, that side's been fine.", "Bowels are regular, nothing odd."]),
    ("genitourinary", "genitourinary", ["Anything unusual with passing urine?", "Any trouble with the waterworks?", "Is your urine normal, no changes?",
                                        "Anything different when you pass water?"],
     ["No, that's all fine.", "Nothing there, no.", "No changes there.", "That's normal as far as I know."]),
    ("cardiovascular", "cardiovascular", ["How about your heart, any problems like that?", "Anything with your heart, like skipped beats or fainting?",
                                          "Has your heart given you any trouble?", "On the cardiac side, anything I should know?"],
     ["No, nothing with my heart.", "No, that's been fine.", "Nothing like that.", "My heart's been fine, as far as I know."]),
    ("respiratory", "respiratory", ["Your breathing, any trouble there?", "How's your breathing otherwise?", "Any breathing difficulties apart from this?",
                                    "Is your chest okay generally?"],
     ["No, my breathing's been fine.", "No problems with breathing.", "Breathing's normal.", "No, nothing there."]),
    ("neurological", "neurological", ["Anything with your nerves, like weakness or numbness?", "Any pins and needles or loss of strength anywhere?",
                                      "Have you noticed any weakness, or anything odd with your balance?", "Neurologically, anything strange?"],
     ["No, nothing like that.", "No, that's all normal.", "No weakness or anything.", "Nothing odd there."]),
    ("skin", "dermatological", ["And your skin, any changes there?", "Any rashes or skin problems otherwise?", "Has your skin been okay?",
                                "Anything on the skin I should know about?"],
     ["No, skin's been fine.", "Nothing on the skin, no.", "No rashes.", "Skin's normal."]),
    ("musculoskeletal", "musculoskeletal", ["Any problems with your joints or muscles?", "How are your joints, any aches elsewhere?",
                                            "Any muscle or joint problems besides this?", "Is your mobility otherwise okay?"],
     ["No, nothing there.", "No, joints are fine.", "Nothing else aches.", "I move fine otherwise."]),
]
D_MED_DUR = ["How long have you been on it?", "How long has that been going on?", "Since when have you been taking it?", "And for how long?",
             "How long have you taken that?", "Is that long-standing?", "Roughly how long on that one?", "When did you start it?"]
D_CONTEXT = ["We'll put it in context in a moment.", "I'll explain what that means shortly.", "Let's look at it together in a minute.",
             "I'll come back to those numbers.", "They help build the picture, I'll tell you more soon.", "That's fine, we'll come to it.",
             "I'll interpret it once I've examined you.", "Don't worry, I'll go through it in a moment."]
D_ANYTHING_ELSE = ["Okay, anything else?", "Anything more?", "Is there more?", "Any others?", "And apart from that?", "Okay, and what else?", "Right, any more?"]
D_FAM = ["Does anything run in the family?", "What about family history, any illnesses that run in the family?",
         "Anyone in the family with similar problems or other conditions?", "Any relatives with health problems I should be aware of?",
         "Is there a family history of anything significant?", "Do your parents or siblings have any long-term illnesses?"]
D_VIT_START = ["Let me check your vitals now.", "I'll take a few measurements first.", "Let's get your blood pressure and the other basics.",
               "I'll check your pressure and pulse.", "Before we go on, a few quick readings.", "Let me measure a few things.",
               "First the numbers, if you don't mind.", "Can I take your vitals now?", "Let's do your observations.", "A few measurements, then we'll continue."]
D_ANYMORE = D_ANYTHING_ELSE
